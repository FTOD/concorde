---
audience: shared
---

## Workflows

A task that follows a known procedure runs as a **workflow**: a preset task whose Operations run
in a fixed order, one at a time, ending with one workflow result. Like every run it works on the
workspace of the worktree it starts in and never names the task, so the task's session starts it
inside the task worktree, as the installed Claude Code workflow `/concorde-<name>`. Open the task as
usual and name in its task brief (see "Keep the decision log") the workflow, its `module` and its
**mode**. Ask the developer which mode to use unless they already said:

- `interactive`: the workflow ends at every point that needs a decision, and the task session
  escalates all of that step's pending points to you at once. Decide those your authority covers,
  put the rest to the developer at once, with their options and recommendations (with
  AskUserQuestion), and answer the task session with every answer, saying for each whether you or
  the developer settled it, which the workflow records; it starts the same workflow
  again with them: steps that finished and are neither answered nor retried are not run again,
  while the answered step and every step after it run anew.
- `no-ask`: the workflow decides those points itself and reports every decision at the end, for
  a developer who wants the result later.

The workflow ends with `concorde workflow report`, which saves the workflow result beside the
workspace's workflow record, `.concorde/tasks/<task>/workspace/workflow/reports/<n>.json` of the
primary worktree, with a Markdown rendering `<n>.md`. The project MCP server's `workflow_report`
reads a saved workflow result too: give it the workspace `folder`, the absolute
`<task folder>/workspace` of a task that `task_show` shows, and a report `number`, or none for the
latest. The task session copies its decisions and problems into the task's decision log and gives
the decisions in its report; read the rendering yourself too, since in `no-ask` mode they are
decisions taken without the developer, and treat it like an Operation result: read every problem's
chain, and merge the task once it has delivered.

The workflows come from the installed parts, such as Method's `brownfield`; the project MCP
server's `workflow_step` belongs to their step agents, which start every step through it, and is
for nobody else.
