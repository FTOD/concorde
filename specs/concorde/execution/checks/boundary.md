# The read-only check boundary

The exact call, environment, mounts and limits of the check runner, and the requirements and
scenarios of the boundary. The [entry](../../glossary.json#concept.read-only-check-boundary)
explains what the boundary is for and what it deliberately leaves out.

## Running one command

```python
execute_check(project_root: Path, argv: Sequence[str], *, timeout: float,
              environment: Mapping[str, str],
              cancel_event: threading.Event | None = None) -> CheckResult
CheckResult(stdout: bytes, stderr: bytes, returncode: int, timed_out: bool = False)
```

`execute_check` in `src/concorde/harness/check_executor.py` is trusted host code; no argument comes
from a registry, a task or a model except the command itself. It refuses, with
`CheckSandboxError(RuntimeError)`, an empty command, a project that is not a directory, a
nonpositive or nonfinite timeout, a platform other than Linux, a project at `/` or under `/proc`,
`/dev` or `/sys`, a missing root-owned system bubblewrap, missing namespace or process file
descriptor support, a failed sandbox setup, and the absence of any writable temporary directory
outside the project. The error carries the diagnostic output as bytes for the host. Apart from a
deadline, which is a timeout even when it passes during sandbox setup, a command that never
received a trusted successful start is an isolation error, not a failed check. `CheckResult` is
this runner's command outcome, not the [check result](../../glossary.json#concept.check-result) the
[check service](service.md) builds from it.

| Outcome | Result |
| --- | --- |
| Exit | `returncode` is the exit status, or `128 + signal` for a signal |
| Timeout (sandbox setup included) | `timed_out=True`, `returncode=-1`, captured partial output |
| Cancellation (`cancel_event` set, or interrupt) | `CheckCancelled(KeyboardInterrupt)` after cleanup, carrying the drained output |

Every outcome carries both output streams whole; the check service saves them as the check's log.

`CHECK_POLICY = "project-read-only-v1"` names the boundary. The policy name is part of every
[configured check](../../glossary.json#concept.configured-check)'s measured digest, the
`check_revision` of [the check service](service.md#running-checks).

## Scratch and environment

The scratch is created below the first of the process temporary directory, an inherited
`CONCORDE_CHECK_TMPDIR`, `/tmp` and `/var/tmp` that lies outside the project, and holds `tmp/`,
`cache/`, `reports/` and `shm/`. The command's environment is the caller's `environment`, passed
whole, with these values set:

| Variable | Value |
| --- | --- |
| `TMPDIR`, `TMP`, `TEMP` | `<scratch>/tmp` |
| `XDG_CACHE_HOME` | `<scratch>/cache` |
| `npm_config_cache` | `<scratch>/cache/npm` |
| `CONCORDE_CHECK_TMPDIR` | `<scratch>` |
| `CONCORDE_CHECK_REPORT_DIR` | `<scratch>/reports` |
| `PYTHONDONTWRITEBYTECODE` | `1` (avoids routine cache writes; it is not the boundary) |

## The Linux boundary

The runner starts bubblewrap with a fixed system search path and a minimal loader environment,
passing the command's environment through an anonymous descriptor rather than its command line. It
unshares user, PID and IPC namespaces, drops all capabilities, dies with the host, binds the host
filesystem recursively read-only, replaces `/proc` with the sandbox's PID view and `/dev` with a
minimal private one, and binds only the scratch writable at its own path; shared memory is backed by
the scratch. The runner starts only a bubblewrap whose file and parent directories are owned by
root and writable by neither group nor others. A check running inside another check's boundary
sees root as the operating system's overflow user, because its namespace cannot map root; there the runner
accepts that owner in place of root only for a file on a read-only mount, so a nested check can
still use the system bubblewrap while a file the checking user owns is never trusted. The host
closes inherited descriptors, gives the command a null standard input and reads both pipes;
bubblewrap's own metadata descriptors are closed before the command runs. The command stays
stopped until the host holds a process file descriptor for the namespace's first process; at the
end the host kills the namespace and waits for it before removing the scratch.

The network namespace is shared, so the command reaches the host's network and abstract Unix
sockets. Filesystem Unix sockets under read-only mounts stay connectable. The IPC namespace is
private only for System V IPC and POSIX message queues. No task input can add a mount.

## Requirements

### req.checks.project-read-only — Files cannot change during a run

The check runner SHALL enforce, in the operating system, that a command and every process it starts
cannot create, modify, rename or delete any file of the host filesystem outside its own scratch for
the whole run.

This covers alternative path names, hard links, inherited file descriptors and nested namespaces.
It restricts file writes only; reads, the network, host sockets and the environment are not limited,
as [the entry's design](module.md#design) explains.

### req.checks.fail-closed — No run without the boundary

The check runner SHALL refuse to start a command whenever it cannot establish the read-only check
boundary.

No ordinary subprocess and no weaker boundary is used instead.

### req.checks.fresh-scratch — Every run has its own scratch

Every run SHALL receive a new writable scratch directory outside the project.

### req.checks.scratch-removed — A scratch outlives no process of its run

The check runner SHALL remove a run's scratch directory after its whole process tree has ended.

### req.checks.process-tree — No process outlives its run

The check runner SHALL terminate every descendant of a command before it returns a result or an
error.

This holds on success, failure, timeout and cancellation, including for processes that detached,
started a new session or reset their parent-death signal.

## Scenarios

### scenario.checks.read-only — A file change is refused at the system call

- GIVEN a command running inside the read-only check boundary
- WHEN it or a descendant tries to create, modify, delete or rename a project file, or to modify one and restore it
- THEN the operating system refuses the operation before any byte or directory entry changes
- AND another path name, an inherited descriptor or a remount in a nested namespace does not make the project writable

### scenario.checks.scratch — A run reads its inputs and writes disposable output

- GIVEN a command and an available temporary directory outside the project
- WHEN the host runs it
- THEN project reads and writes to the issued temporary, cache and report directories succeed
- AND repeated runs receive separate scratch directories, each removed after its run
- BUT an ambient temporary path inside the project never becomes a writable mount

### scenario.checks.command-output — Output and exit status return to the host

- GIVEN a command that writes to standard output and standard error and exits with a given code
- WHEN its run finishes
- THEN the runner returns both byte streams and that exit code, with signal endings reported as 128 plus the signal
- AND large output on both pipes is drained without blocking the command
- AND the caller's environment reaches the command without appearing in the sandbox's command line

### scenario.checks.unavailable — Without the boundary nothing runs

- GIVEN an unsupported platform, a missing trusted bubblewrap, a denied namespace setup or a failed sandbox setup
- WHEN the host asks to run a command
- THEN the run is refused with a sandbox error carrying the host-side diagnostics
- BUT no ordinary subprocess runs the command instead

### scenario.checks.descendants-end — Descendants end with their run

- GIVEN a command that starts detached descendants
- WHEN the initial command completes or fails
- THEN the host terminates every descendant before returning and only then removes the scratch

### scenario.checks.timeout — A command past its deadline times out

- GIVEN a command that is still running at its deadline, possibly with detached descendants
- WHEN the deadline passes
- THEN the host terminates the whole process tree and returns the partial output with `timed_out` set and exit code `-1`
- BUT the result is never reported as a success

### scenario.checks.cancelled — A cancelled command ends cleanly

- GIVEN a running command
- WHEN the caller sets its cancel event or the host is interrupted
- THEN the host terminates the whole process tree, drains both pipes and raises a cancellation carrying the drained output
- AND the scratch is removed
