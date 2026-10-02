---
audience: shared
---

## Workflows

A task that follows a known procedure may run as its workflow, started in your task
worktree as the installed `/concorde-<name>` workflow, in the mode the task brief names:

```json
{"module": "<module>", "mode": "interactive", "answers": {}, "retry": [], "restart": {}}
```

- `interactive`, also when the task brief names no mode: the workflow ends at the first step that
  did not end `ok` or whose decision points its answers did not settle. When its status is
  `awaiting_decision`, escalate every point in `pending` at once, with `--error-file` naming its
  workflow result, whose chain names each point with its options and recommendation. When the main
  agent has answered, start the same workflow again with `answers` mapping each step's base key
  (such as `survey` or `describe:module.checkout`) to every answer given for it so far, each `{"id":
  "<d. or q. identity>", "question": "<its text>", "answer": "<the answer>", "answered_by":
  "<main-agent or developer>"}`, where `answered_by` names who settled it, as the main agent's
  answer says; the run records a decision that follows an answer as decided by that one. Steps that
  finished and are neither answered nor retried are not run again; the answered step and every step
  after it run anew.
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

Your session's project MCP server has `workflow_step`, which belongs to your workflows' step agents,
which start every step through it: it runs the step outside your session, so that neither the
agent's turn nor a background command's lifetime bounds the run. Its `workflow_report` reads a
saved workflow result of your workspace.
