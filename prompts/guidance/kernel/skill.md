---
audience: shared
---

## Traces and error chains

Every level of the work leaves a record. `concorde trace show <task>` shows a task's whole
trace, from its sessions down to each worker round. The trace shows how long each part took.
The trace also shows what each part cost. `concorde trace show <run-id>` shows one run. Tasks exist
only where the coordination part is installed. Runs exist only where the execution part is installed. Without these parts,
there is no task or run to name. `concorde trace show <folder>` still shows the node whose folder
you give. The folder can be absolute or relative to a `.concorde` directory.

Except for Spec tooling's commands, when a `concorde` command cannot do what it was asked, it
refuses with `{"error": <link>}`. This is the top link of an **error chain**. Each link is one level's
own account:

- Its `level` and `actor`.
- A `code`.
- The full `detail`.
- Its `evidence` and `attempts`.
- The `options` and `recommendation` it offers.
- Why it could not handle the error itself (`unhandled.reason` and `explanation`).
- The errors it received from below as `causes`, down to where the error started.

Read the whole chain before deciding for these reasons:

- The origin tells you what went wrong.
- Each `unhandled` tells you why nobody below could fix it.

Standard error shows the same chain as indented text.
