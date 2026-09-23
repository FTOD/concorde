# Check execution in depth

This topic explains the reasons behind Check execution's design and what its boundary leaves out.
The [entry](module.md) defines the terms; [the boundary](boundary.md) and
[the records](records.md) state the exact behaviour.

## What the boundary enforces and what it does not {#enforcement}

Checks produce evidence that a candidate is ready. That evidence is only useful if the check could
not have changed what it measured, so the one guarantee that matters is that files cannot change.
The boundary delivers exactly that and states plainly what it leaves out:

| Concern | Enforced |
| --- | --- |
| Writing any host file outside the scratch, through any path name, hard link, inherited descriptor or nested namespace | Yes, by the kernel |
| Descendant processes outliving the run | Yes: the Host ends the whole process tree |
| Reading files the developer's user can read | Not enforced |
| Network access | Not enforced: the network namespace is shared with the host |
| Host sockets: abstract Unix sockets and filesystem sockets such as an SSH agent or a container daemon | Not enforced: a read-only mount does not stop connecting to a socket, so a command could ask a host service to act, including changing the project |
| Environment and credentials | Not enforced: the command receives the caller's environment, including any credentials in it |

These omissions are deliberate. Configured checks are commands the project itself chose. Tester
commands are written by a model, so a tester's only way to run anything is this boundary: it can
read and send out whatever the user can, but it cannot write the project it is testing.

## How the runner holds the boundary

The runner mounts the whole host filesystem read-only, recursively, so no other path, hard link or
dependency directory can serve as a writable alias. It gives fresh `/proc` and `/dev`, drops
capabilities, disconnects the terminal and makes only the scratch writable. The command starts
stopped until the Host holds a process file descriptor for the sandbox's first process, so the Host
can always end the whole process tree: on success, failure, timeout and cancellation it terminates
every descendant, including ones that detached or started new sessions, before it removes the
scratch. Output is drained from both pipes while the command runs, so a large or background writer
cannot block completion.

## Why configured checks measure twice

The boundary cannot stop a process outside it, or a host service a check talked to, from changing
the project during the run. Comparing the measured digest before and after turns that race into a
stale result instead of false evidence. The check result is owned here, next to the runner that
produces it, so Validation and Delivery consume one record and never run checks another way. Logs
are kept only in the primary worktree's run directory; a check's output never enters an Agent's
context except as the bounded tail `run_checks` returns.

## Why tester evidence is exported by the Host

A tester's scratch disappears when its command ends, and the tester itself cannot write the primary
worktree. The export therefore runs inside the Host after the sandboxed processes have ended and
before scratch removal. It opens only regular files with one link, through non-symlink paths under
the reports directory, bounds each report and the total, and records every truncation and error in
the manifest. Output and reports are the command's own data: the Host does not filter secrets from
them, so a command must not print any.

## Writing a check that works in the boundary

A tool that hard-codes a cache or report path in the project fails and must be pointed at the
scratch through `TMPDIR`, `XDG_CACHE_HOME`, `npm_config_cache` or `CONCORDE_CHECK_REPORT_DIR`; a
tool that rewrites sources, such as a formatter in fix mode, is implementation work and does not
belong in a check. Only Linux is supported, with a root-owned system bubblewrap, user, mount, PID
and IPC namespaces and kernel process file descriptors; there is no fallback to an ordinary
subprocess.

## Open questions

- Whether an Agent needs more than the last 20,000 bytes of each check's log is undecided.
