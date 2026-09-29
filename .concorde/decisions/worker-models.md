# Decision log: worker-models

Goal: Project/worktree-level worker model configuration (default + per task type, per backend) discovered from the installed Claude Code or pi, chosen in the main session; worker backend follows the main session's client

## Closed: merged, 2026-09-24T19:47:09Z

## Decisions made without the developer (2026-09-25)

- The worker model configuration is an untracked file per worktree, `.concorde/worker-models.json`,
  not a key of the tracked `.concorde/config.json`: a tracked file would leave the primary worktree
  dirty (blocking merges) and delivery would merge a task's own choice back into main. `task open`
  copies it, which realizes "inherited at task creation, independent afterwards".
- `concorde workers models|show|set|unset` is an ordinary command of Workers, not a catalog
  Operation: Operations are task-bound (`--task`, task record, task worktree) and this command
  changes no task. The main agent still starts it on the developer's request.
- The backend is detected, never configured: CONCORDE_CLIENT, then CLAUDECODE=1, then pi's
  PI_SESSION_ID/PI_CODING_AGENT. The pi extension sets CONCORDE_CLIENT=pi. `workers.backend`,
  `workers.model` and `workers.thinking` were removed from the project configuration.
- The reasoning level is one field, `reasoning`, passed as `--effort` (Claude Code) or
  `--thinking` (pi).
- Claude Code cannot list an account's models; its candidates are its aliases plus models named
  in settings/environment, marked incomplete; other full names need `--allow-unlisted`.
