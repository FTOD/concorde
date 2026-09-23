# Check execution requirements

The Module-wide obligations of Check execution. The [entry](module.md) explains them;
[interfaces](interfaces.md) states the exact environment, limits and records.

### req.checks.project-read-only — Project files cannot change during a run

The check runner SHALL enforce, in the operating system, that a check or tester command and every
process it starts cannot create, modify, rename or delete any file of the host filesystem outside
its own scratch for the whole run.

This covers alternative path names, hard links, inherited file descriptors and nested namespaces.
It restricts writes only; reads, the network and credentials in the environment are not limited.

### req.checks.fail-closed — No run without the boundary

The check runner SHALL refuse to start a command whenever it cannot establish the read-only check
boundary.

No ordinary subprocess and no weaker boundary is used instead.

### req.checks.fresh-scratch — Every run has its own scratch

Every run SHALL receive a new writable scratch directory outside the project that is removed after
its process tree has ended.

### req.checks.process-tree — No process outlives its run

The check runner SHALL terminate every descendant of a command before it returns a result or an
error.

This holds on success, failure, timeout and cancellation, including for processes that detached,
started a new session or reset their parent-death signal.

### req.checks.measured-input-unchanged — A check cannot vouch for input that changed

A configured check run SHALL fail with `stale_evidence` when the implementation files or check
inputs it measured differ after the run from before it.

### req.checks.tester-evidence-honest — Tester evidence is complete only when it is

The Host SHALL mark tester evidence complete only when every requested report and every observed
output byte was exported and the command neither timed out, was cancelled nor failed to start.
