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

A task that follows a known procedure may run as its workflow, started in your task worktree as
the main agent would start it (the installed `/concorde-<name>` workflow in Claude Code, the
`subagent` tool with the primary worktree's `.concorde/workflows/pi/<name>.js` in pi), but only in
`no-ask` mode (`"mode": "no-ask"` in its `args`): nobody answers you at a decision point, so the
workflow decides those points itself and reports every decision at the end. Read its report,
`.concorde/runs/workflows/<task>/reports/<n>.json` of the primary worktree, like a run result: copy
its decisions and problems into the decision log, since they were taken without the developer, and
give its decisions in your report to the main agent. Escalate to the main agent what needs the
developer: a result that is not `ok` and that you cannot repair within the task, with
`--error-file` naming that report; and a decision of major impact among those the workflow took,
which carries no error, escalated naming no run or file, so that your link, with its step, its
options and your recommendation, is the whole chain for the main agent to put to the developer.

Escalate to the main agent instead of acting when a step would go beyond the task's goal or its
Modules, when the goal needs a Spec change it does not already call for, or when a decision has
a major impact: it changes what a Module promises or the project's direction, discards work or
data, cannot be undone by an ordinary revert, or touches security or credentials. Never replace
an error chain with your own summary; add your link on top of it, or, when no error carries what
you escalate, name no run or file and your link alone is the chain:

```bash
concorde task escalate <task> --by task-session [--run <run-id>…] [--error-file <json>…] \
  --code <snake_case> --detail "<what you need decided, and what you already know>" \
  --reason decision --explanation "<why you may not decide this yourself>" \
  [--option "<choice>"…] [--recommendation "<yours>"]
```

When `concorde task escalate` itself is refused with `merge_incomplete` or `merge_busy`, a merge in
the primary worktree is unfinished or still running; send that refusal, unchanged, to the main
agent instead and wait for its answer.
