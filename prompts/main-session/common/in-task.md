---
audience: shared
---

Work on a task only from inside its worktree, `.claude/worktrees/<task>` of the primary worktree
by default (`concorde task show <task>` prints its path):

- **Use the worktree's own Concorde.** Run every `concorde` command for the task (`validate`,
  `build`, `run <operation> --task <task>`, `run delivery`) from the task worktree with the
  worktree's own command, never the primary worktree's. Only the task branch's copy knows the
  branch's Specs, Protocol and checks. Prepare first what Git does not track, such as
  dependencies or build outputs, as the project's own instructions say.
- **Change directly or through Operations.** Inside the task worktree you may change Specs and
  code yourself within the task's goal, verify the change and commit each verified step on the
  task branch, or run Operations for bounded steps and read their results. Never change a file
  outside the task worktree except the task's decision log.
- **Deliver.** `concorde run validate --task <task>` shows what would block; `concorde run
  delivery --task <task>` validates the whole task again and commits the evidence on the task
  branch. Never merge, rebase or switch branches: merging is the main agent's step, from the
  primary worktree.
