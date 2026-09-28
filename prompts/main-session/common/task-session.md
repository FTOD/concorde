---
audience: shared
---

Your session starts with the project's terms, each defined once in its glossary: use every
term exactly as defined, in Specs, code, the decision log and your reports, and never coin a synonym
for one. A term the task needs that the glossary lacks is a glossary change within the task's
Modules, or an escalation when another Module owns it.

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

When `concorde task escalate` itself is refused with `merge_incomplete` or `merge_busy`, a merge in
the primary worktree is unfinished or still running; send that refusal, unchanged, to the main
agent instead and wait for its answer.
