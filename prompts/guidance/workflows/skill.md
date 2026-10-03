---
audience: shared
---

## Workflows

Work that follows a known procedure runs as a **workflow**: its Operations and execution commands
run in a fixed order, one at a time, ending with one workflow result. Like every run it works on the
workspace of the worktree it starts in and never names a task, so it is started inside a bound
worktree, as the installed Claude Code workflow `/concorde-<name>`. Where the coordination part is
installed, that worktree is a task's: open the task as usual, name in its task brief (see "Keep the
decision log") the workflow, its `module` and its **mode**, and the task's session starts it. Without
the coordination part nothing in Concorde binds a worktree, so a workflow runs only in a workspace
something else prepared, started there by whoever works in it, and its results reach you from that
session rather than through a task. Ask the developer which mode to use unless they already said:

- `interactive`: the workflow ends at every point that needs a decision, and the task session
  (where the coordination part is installed) escalates all of that step's pending points to you at
  once. Decide those your authority covers, put the rest to the developer at once, with their
  options and recommendations (with AskUserQuestion), and answer with every answer, saying for each
  whether you or the developer settled it, which the workflow records; the same workflow is
  started again with them: steps that finished and are neither answered nor retried are not run
  again, while the answered step and every step after it run anew.
- `no-ask`: the workflow decides those points itself and reports every decision at the end, for
  a developer who wants the result later.

The workflow ends with `concorde workflow report`, which saves the workflow result beside the
workspace's workflow record, `workflow/reports/<n>.json` of the workspace folder the binding names
(for a task's workspace `.concorde/tasks/<task>/workspace/workflow/reports/<n>.json` of the primary
worktree), with a Markdown rendering `<n>.md`. The project MCP server's `workflow_report` reads a
saved workflow result too: give it the workspace `folder`, the absolute workspace folder (for a
task, `<task folder>/workspace` of a task that `task_show` shows), and a report `number`, or none
for the latest. Where the coordination part is installed, the task session copies its decisions and
problems into the task's decision log and gives the decisions in its report. Read the rendering
yourself too, since in `no-ask` mode they are decisions taken without the developer, and treat it
like an Operation result: read every problem's chain, and merge the task once it has delivered.

The workflows come from the installed parts, such as Method's `brownfield`; the project MCP
server's `workflow_step` belongs to their step agents, which start every step through it, and is
for nobody else.
