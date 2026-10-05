# The read-only check boundary

This document describes these details of the check runner and its boundary:

- the exact call
- the environment
- the mounts
- the limits
- the requirements
- the scenarios

The [entry](../../glossary.json#concept.read-only-check-boundary) explains what the boundary is for.
The entry also explains what the boundary deliberately leaves out.

## Running one command

```python
execute_check(project_root: Path, argv: Sequence[str], *, timeout: float,
              environment: Mapping[str, str],
              cancel_event: threading.Event | None = None) -> CheckResult
CheckResult(stdout: bytes, stderr: bytes, returncode: int, timed_out: bool = False)
```

`execute_check` in `src/concorde/execution/checks/check_executor.py` is trusted host code. Except
for the command itself, no argument comes from any of these sources:

- a registry
- a task
- a model

The runner refuses with `CheckSandboxError(RuntimeError)` in these cases:

- The command is empty.
- The project is missing or not a directory.
- The timeout is nonpositive or nonfinite.
- The platform is other than Linux.
- The project is at `/` or under any of these paths:
  - `/proc`
  - `/dev`
  - `/sys`
- The root-owned system bubblewrap is missing.
- Namespace or process file descriptor support is missing.
- Sandbox setup fails.
- No writable temporary directory exists outside the project.

The error carries the diagnostic output as bytes for the host. Apart from a deadline, a command
that never received a trusted successful start is an isolation error, not a failed check. Even
when it passes during sandbox setup, a deadline is a timeout. `CheckResult` is this runner's
command outcome. It is not the [check result](../../glossary.json#concept.check-result) the
[check service](service.md) builds from it.

| Outcome | Result |
| --- | --- |
| Exit | `returncode` is the exit status, or `128 + signal` for a signal |
| Timeout (sandbox setup included) | `timed_out=True`, `returncode=-1`, captured partial output |
| Cancellation (`cancel_event` set, or interrupt) | `CheckCancelled(KeyboardInterrupt)` after cleanup, carrying the drained output |
| Another exception interrupting the wait, such as a caller's signal handler raising its own cancellation | that exception unchanged after cleanup, carrying the drained output as `check_output` |

Every outcome carries both output streams whole. The check service saves them as the check's log.

`CHECK_POLICY = "project-read-only-v1"` names the boundary. The policy name is part of every
[configured check](../../glossary.json#concept.configured-check)'s measured digest. This digest is
`check_revision` of [the check service](service.md#running-checks).

## Scratch and environment

The scratch is created below the first usable directory in this order:

- the process temporary directory
- an inherited `CONCORDE_CHECK_TMPDIR`
- `/tmp`
- `/var/tmp`

A usable directory lies outside the project and allows scratch creation. Without a usable
temporary directory, the process goes on to the next. The scratch holds these directories:

- `tmp/`
- `cache/`
- `reports/`
- `shm/`

The command's environment is the caller's `environment`, passed whole, with these values set:

| Variable | Value |
| --- | --- |
| `TMPDIR`, `TMP`, `TEMP` | `<scratch>/tmp` |
| `XDG_CACHE_HOME` | `<scratch>/cache` |
| `npm_config_cache` | `<scratch>/cache/npm` |
| `CONCORDE_CHECK_TMPDIR` | `<scratch>` |
| `CONCORDE_CHECK_REPORT_DIR` | `<scratch>/reports` |
| `PYTHONDONTWRITEBYTECODE` | `1` (avoids routine cache writes; it is not the boundary) |

## The Linux boundary

The runner starts bubblewrap with a fixed system search path and a minimal loader environment.
The runner passes the command's environment through an anonymous descriptor rather than its
command line. The runner unshares these namespaces:

- user
- PID
- IPC

The runner also does these things:

- drops all capabilities
- dies with the host
- binds the host filesystem recursively read-only
- replaces `/proc` with the sandbox's PID view
- replaces `/dev` with a minimal private one
- binds only the scratch writable at its own path

Shared memory is backed by the scratch. The runner starts only a bubblewrap with a root-owned file
and root-owned parent directories, all writable by neither group nor others. Because the check's
namespace cannot map root, a check inside another check's boundary sees root as the operating
system's overflow user. There, only for a file on a read-only mount, the runner accepts that owner
in place of root. So a nested check can still use the system bubblewrap, while a file the checking
user owns is never trusted. The host performs these actions:

- closes inherited descriptors
- gives the command a null standard input
- reads both pipes

Before the command runs, bubblewrap's own metadata descriptors are closed. Until the host holds
a process file descriptor for the namespace's first process, the command stays stopped. At the
end, before removing the scratch, the host kills the namespace. Before removing the scratch, the
host also waits for the namespace.

The network namespace is shared. Because of this, the command reaches the host's network and
abstract Unix sockets. Filesystem Unix sockets under read-only mounts stay connectable. The IPC
namespace is private only for System V IPC and POSIX message queues. No task input can add a mount.

## Requirements

### req.checks.project-read-only — Files cannot change during a run

For the whole run, the check runner SHALL prevent a command and every process it starts from these
actions, in the operating system, on any host filesystem file outside its own scratch:

- create
- modify
- rename
- delete

This covers these cases:

- alternative path names
- hard links
- inherited file descriptors
- nested namespaces

The check runner restricts file writes only. As [the entry's design](module.md#design) explains,
the check runner does not limit these:

- reads
- the network
- host sockets
- the environment

### req.checks.fail-closed — No run without the boundary

Whenever it cannot establish the read-only check boundary, the check runner SHALL refuse to start
a command.

No ordinary subprocess and no weaker boundary is used instead.

### req.checks.fresh-scratch — Every run has its own scratch

Every run SHALL receive a new writable scratch directory outside the project.

### req.checks.scratch-removed — A scratch outlives no process of its run

After a run's whole process tree ends, the check runner SHALL remove the run's scratch directory.

### req.checks.process-tree — No process outlives its run

Before it returns a result or an error, the check runner SHALL terminate every descendant of a
command.

This holds for these outcomes:

- success
- failure
- timeout
- cancellation

This includes processes with these behaviours:

- processes that detached
- processes that started a new session
- processes that reset their parent-death signal

## Scenarios

### scenario.checks.read-only — A file change is refused at the system call

- GIVEN a command running inside the read-only check boundary
- WHEN it or a descendant tries to create, modify, delete or rename a project file, or to modify one
  and restore it
- THEN the operating system refuses the operation before any byte or directory entry changes
- AND another path name, an inherited descriptor or a remount in a nested namespace does not make
  the project writable

### scenario.checks.scratch — A run reads its inputs and writes disposable output

- GIVEN a command and an available temporary directory outside the project
- WHEN the host runs it
- THEN project reads succeed
- AND writes to the issued temporary directory succeed
- AND writes to the issued cache directory succeed
- AND writes to the issued report directory succeed
- AND repeated runs receive separate scratch directories
- AND each scratch directory is removed after its run
- BUT an ambient temporary path inside the project never becomes a writable mount

### scenario.checks.command-output — Output and exit status return to the host

- GIVEN a command that writes to standard output
- AND writes to standard error
- AND exits with a given code
- WHEN its run finishes
- THEN the runner returns both byte streams and that exit code
- AND signal endings are reported as 128 plus the signal
- AND large output on both pipes is drained without blocking the command
- AND the caller's environment reaches the command without appearing in the sandbox's command line

### scenario.checks.unavailable — Without the boundary nothing runs

- GIVEN an unsupported platform, a missing trusted bubblewrap, a denied namespace setup or a failed
  sandbox setup
- WHEN the host asks to run a command
- THEN the run is refused with a sandbox error carrying the host-side diagnostics
- BUT no ordinary subprocess runs the command instead

### scenario.checks.descendants-end — Descendants end with their run

- GIVEN a command that starts detached descendants
- WHEN the initial command completes or fails
- THEN before returning, the host terminates every descendant
- AND only then removes the scratch

### scenario.checks.timeout — A command past its deadline times out

- GIVEN a command that still runs at its deadline, possibly with detached descendants
- WHEN the deadline passes
- THEN the host terminates the whole process tree
- AND returns the partial output with `timed_out` set and exit code `-1`
- BUT the result is never reported as a success

### scenario.checks.cancelled — A cancelled command ends cleanly

- GIVEN a running command
- WHEN the caller sets its cancel event or the host is interrupted
- THEN the host terminates the whole process tree
- AND drains both pipes
- AND raises a cancellation carrying the drained output
- AND the scratch is removed
