---
audience: shared
---

## Workflows

A task that follows a known procedure may run as its workflow.
The workflow starts in your task worktree as the installed `/concorde-<name>` workflow.
It uses the mode the task brief names:

```json
{"module": "<module>", "mode": "interactive", "answers": {}, "retry": [], "restart": {}}
```

- `interactive` also applies when the task brief names no mode.
  In this mode, the workflow ends at the first step that did not end `ok` or whose decision points
  its answers did not settle.
  When its status is `awaiting_decision`, escalate every point in `pending` at once, with
  `--error-file` naming its workflow result.
  The workflow result's chain names each point with its options and recommendation.
  When the main agent has answered, start the same workflow again with `answers` mapping each
  step's base key to every answer given for it so far.
  Examples of a step's base key are `survey` and `describe:module.checkout`.
  Each answer is `{"id":
  "<d. or q. identity>", "question": "<its text>", "answer": "<the answer>", "answered_by":
  "<main-agent or developer>"}`.
  As the main agent's answer says, `answered_by` names who settled it.
  The run records a decision that follows an answer as decided by that one.
  Steps that finished and are neither answered nor retried are not run again.
  The answered step and every step after it run anew.
- `no-ask`: the workflow decides those points itself.
  It reports every decision at the end.
  Among the decisions the workflow took, escalate a decision of major impact, which carries no
  error.
  Name no run or file, so that your link is the whole chain for the main agent to put to the
  developer.
  Your link includes:
  - The decision's step.
  - The decision's options.
  - Your recommendation.

Either way, read its report like a run result.
The report is `.concorde/tasks/<task>/workspace/workflow/reports/<n>.json` of the primary worktree.
Copy its decisions and problems into the decision log, since they were taken without the developer.
Give its decisions in your report to the main agent.
When a result is not `ok` and you cannot repair it within the task, escalate it with `--error-file`
naming that report.
When you repaired the cause of a failed step, start the workflow again with its base key in `retry`.
Everything after that step runs again.
To run a step that ended `ok` once more, give `restart` a new label for its base key, such as
`{"scaffold": "2"}`.
Keep that label on later relaunches.

Your session's project MCP server has `workflow_step`.
This tool belongs to your workflows' step agents.
The step agents start every step through it.
It runs the step outside your session, so that neither the agent's turn nor a background command's
lifetime bounds the run.
The server's `workflow_report` reads a saved workflow result of your workspace.
