---
audience: shared
---

## Workflows

Work that follows a known procedure runs as a **workflow**. Its Operations and execution commands
run in a fixed order, one at a time. The workflow ends with one workflow result. Like every run,
the workflow works on the workspace of the worktree it starts in. It never names a task. For these
reasons, it starts inside a bound worktree, as the installed Claude Code workflow
`/concorde-<name>`. Where the coordination part is installed, the following applies:

- That worktree is a task's.
- Open the task as usual.
- In its task brief (see "Keep the decision log"), name:
  - The workflow.
  - Its `module`.
  - Its **mode**.
- The task's session starts the workflow.

Without the coordination part, nothing in Concorde binds a worktree. For this reason, a workflow
runs only in a workspace something else prepared. Whoever works in that workspace starts the
workflow there. Its results reach you from that session rather than through a task. Unless the
developer already said which mode to use, ask the developer which mode to use:

- `interactive`: the workflow ends at every point that needs a decision. Where the coordination
  part is installed, the task session escalates all of that step's pending points to you at once.
  Decide those your authority covers. Put the rest to the developer at once, with their options
  and recommendations (with AskUserQuestion). Answer with every answer. For each answer, say
  whether you or the developer settled it. The workflow records every answer and who settled it.
  The same workflow starts again with those answers. Steps that finished and are neither answered
  nor retried do not run again. The answered step and every step after it run anew.
- `no-ask`: the workflow decides those points itself. It reports every decision at the end, for
  a developer who wants the result later.

The workflow ends with `concorde workflow report`. This command saves the workflow result beside
the workspace's workflow record. The result's path is `workflow/reports/<n>.json` of the workspace
folder the binding names. For a task's workspace, the path is
`.concorde/tasks/<task>/workspace/workflow/reports/<n>.json` of the primary worktree. The command
also saves a Markdown rendering `<n>.md`. The project MCP server's `workflow_report` reads a
saved workflow result too. Give it the workspace `folder`, the absolute workspace folder.
For a task, this folder is `<task folder>/workspace` of a task that `task_show` shows.
Give it a report `number`, or none for the latest. Where the coordination part is installed,
the task session does the following:

- It copies its decisions and problems into the task's decision log.
- It gives the decisions in its report.

Read the rendering yourself too, since in `no-ask` mode the decisions are taken without the
developer. Treat the rendering like an Operation result:

- Read every problem's chain.
- Once the task has delivered, merge the task.

The workflows come from the installed parts, such as Method's `brownfield`. The project MCP
server's `workflow_step` belongs to their step agents. These step agents start every step through
it. It is for nobody else.
