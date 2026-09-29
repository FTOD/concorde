---
audience: shared
---

Your session starts with the project's terms, each defined once in its glossary: use every
term exactly as defined, in Specs, code, the decision log and your reports, and never coin a synonym
for one. A term the task needs that the glossary lacks is a glossary change within the task's
Modules, or an escalation when another Module owns it.

Read the task's decision log before you change anything: the main agent records there the task's
brief, the developer's decisions the task carries out, which you do not revisit, and what it left
for you to decide. Add your own entries below its entries.

Decide ordinary questions inside the task's goal and Modules yourself: naming, internal
structure, the order of steps, re-running an Operation with a clarified brief. Record each such
decision, and every result that is not `ok`, in the task's decision log with its reason; append,
never rewrite.

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

**Never ask in place.** Nobody answers you while you work, so never stop in the middle of the work
to wait for one answer. When the task needs decisions that are not yours, carry on with every part
of the work that does not depend on them, then gather every decision the task still needs and
escalate them together, in one report, rather than one at a time: record each with
`concorde task escalate`, then report them all at once. The main agent decides what it may and puts
the rest to the developer, and its answer carries every answer.

**Workflows.** A task that follows a known procedure may run as its workflow, started in your task
worktree (the installed `/concorde-<name>` workflow in Claude Code, the `subagent` tool with the
primary worktree's `.concorde/workflows/pi/<name>.js` in pi), in the mode the task's brief names:

```json
{"module": "<module>", "mode": "interactive", "answers": {}, "retry": [], "restart": {}}
```

- `interactive`, also when the brief names no mode: the workflow ends at the first step that did
  not end `ok` or whose decision points its answers did not settle. When its status is
  `awaiting_decision`, escalate every point in `pending` at once, with `--error-file` naming its
  report, whose chain names each point with its options and recommendation. When the main agent
  has answered, start the same workflow again with `answers` mapping each step's base key (such as
  `survey` or `describe:module.checkout`) to every answer given for it so far, each
  `{"id": "<d. or q. identity>", "question": "<its text>", "answer": "<the answer>"}`. Steps that
  finished are not run again.
- `no-ask`: the workflow decides those points itself and reports every decision at the end.
  Escalate a decision of major impact among those the workflow took, which carries no error,
  naming no run or file, so that your link, with its step, its options and your recommendation, is
  the whole chain for the main agent to put to the developer.

Either way, read its report, `.concorde/tasks/<task>/workspace/workflow/reports/<n>.json` of the
primary worktree, like a run result: copy its decisions and problems into the decision log, since they were
taken without the developer, and give its decisions in your report to the main agent. Escalate a
result that is not `ok` and that you cannot repair within the task with `--error-file` naming that
report. When you repaired the cause of a failed step, start the workflow again with its base key in
`retry`; everything after it runs again. To run a step that ended `ok` once more, give `restart` a
new label for its base key, such as `{"scaffold": "2"}`, and keep that label on later relaunches.

When `concorde task escalate` itself is refused with `merge_incomplete` or `merge_busy`, a merge in
the primary worktree is unfinished or still running; send that refusal, unchanged, to the main
agent instead and wait for its answer.

**A merge conflict.** When the main agent tells you that merging the task failed with
`merge_conflict`, merge the primary branch it names into your task branch (`git merge <branch>` in
the task worktree), resolve the conflicts within the task's goal, verify the result and commit the
merge, then run `concorde task-validation` and `concorde delivery` again and report as at the end
of the task. It is the only merge you make.
