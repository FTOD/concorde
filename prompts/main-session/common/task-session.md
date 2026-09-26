---
audience: shared
---

Decide ordinary questions inside the task's goal and Modules yourself: naming, internal
structure, the order of steps, re-running an Operation with a clarified brief. Record each such
decision, and every result that is not `ok`, in the task's decision log with its reason; append,
never rewrite.

Escalate to the main agent instead of acting when a step would go beyond the task's goal or its
Modules, when the goal needs a Spec change it does not already call for, or when a decision has
a major impact: it changes what a Module promises or the project's direction, discards work or
data, cannot be undone by an ordinary revert, or touches security or credentials. Never replace
an error chain with your own summary; add your link on top of it:

```bash
concorde task escalate <task> --by task-session --run <run-id> [--error-file <json>…] \
  --code <snake_case> --detail "<what you need decided, and what you already know>" \
  --reason decision --explanation "<why you may not decide this yourself>" \
  [--option "<choice>"…] [--recommendation "<yours>"]
```
