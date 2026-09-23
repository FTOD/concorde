# Check execution in depth

This topic explains the reasons behind Check execution's design and what its boundary leaves out.
The [entry](module.md) defines the terms; [the boundary](boundary.md),
[the check service](service.md) and [the timing spans](timing.md) state the exact behaviour.

## What the boundary enforces and what it does not {#enforcement}

Checks produce evidence that a task worktree is ready. That evidence is only useful if the check
could not have changed what it measured, so the one guarantee that matters is that files cannot
change. The boundary delivers exactly that and states plainly what it leaves out:

| Concern | Enforced |
| --- | --- |
| Writing any host file outside the scratch, through any path name, hard link, inherited descriptor or nested namespace | Yes, by the kernel |
| Descendant processes outliving the run | Yes: the host ends the whole process tree |
| Reading files the developer's user can read | Not enforced |
| Network access | Not enforced: the network namespace is shared with the host |
| Host sockets: abstract Unix sockets and filesystem sockets such as an SSH agent or a container daemon | Not enforced: a read-only mount does not stop connecting to a socket, so a command could ask a host service to act, including changing the project |
| Environment and credentials | Not enforced: the command receives the caller's environment, including any credentials in it |

These omissions are deliberate. Configured checks are commands the project itself chose, and they
run in the host, never in a worker. A worker never runs a command in this boundary; it only receives
the results.

## How the runner holds the boundary

The runner mounts the whole host filesystem read-only, recursively, so no other path, hard link or
dependency directory can serve as a writable alias. It gives fresh `/proc` and `/dev`, drops
capabilities, disconnects the terminal and makes only the scratch writable. The command starts
stopped until the host holds a process file descriptor for the sandbox's first process, so the host
can always end the whole process tree: on success, failure, timeout and cancellation it terminates
every descendant, including ones that detached or started new sessions, before it removes the
scratch. Output is drained from both pipes while the command runs, so a large or background writer
cannot block completion. The command's environment reaches it through an anonymous descriptor, never
through the sandbox's visible command line.

## Why configured checks measure twice

The boundary cannot stop a process outside it, or a host service a check talked to, from changing
the project during the run. Comparing the measured digest before and after turns that race into a
stale result instead of false evidence. The check result is owned here, next to the runner that
produces it, so Workers, Validation and Delivery consume one record and never run checks another
way. Logs are written only to the directory the caller names, usually the run directory in the
primary worktree; a check's output reaches a worker only as the bounded log tail that Workers puts
into a resume round.

## Why timing lives here

The timing recorder began as a diagnostic of check runs and sandbox setup, which are the slowest
deterministic steps a host takes. It is passive: recording, keeping or failing to keep a span never
changes a run's outcome, and a span holds no content, so it can be left on in any run. Its summary
reports covered time per process and never subtracts clocks of different processes.

## Open questions

- Whether a worker needs more than the last 20,000 bytes of each failing check's log is undecided.
- The timing summary reads the event-log format of the former Pi sessions; whether it should read
  Claude Code transcripts instead is undecided.
