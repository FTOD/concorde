---
audience: shared
---

## Traces and error chains

Every level of the work leaves a record, and `concorde trace show <task>` shows a task's whole
trace, from its sessions down to each worker round, with how long each part took and what it cost;
`concorde trace show <run-id>` shows one run. Tasks exist only where the coordination part is
installed and runs only where the execution part is: without them there is no task or run to name,
and `concorde trace show <folder>` still shows the node whose folder you give, absolute or relative
to a `.concorde` directory.

Every `concorde` command that cannot do what it was asked refuses with `{"error": <link>}`, the top
link of an **error chain**, except Spec tooling's commands. Each link is one level's own account:
its `level` and `actor`, a `code`, the full `detail`, its `evidence` and `attempts`, the `options`
and `recommendation` it offers, why it could not handle the error itself (`unhandled.reason` and
`explanation`), and the errors it received from below as `causes`, down to where the error started.
Read the whole chain before deciding: the origin tells you what went wrong, and each `unhandled`
tells you why nobody below could fix it. Standard error shows the same chain as indented text.
