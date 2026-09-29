---
audience: shared
---

Work on a task only from inside its worktree, `.claude/worktrees/<task>` of the primary worktree
by default (`concorde task show <task>` prints its path):

- **Use the worktree's own Concorde.** Run every `concorde` command for the task
  (`spec-validation`, `build`, `run <operation>`, `task-validation`, `delivery`) from the task
  worktree with the worktree's own command, never the primary worktree's. Only the task branch's
  copy knows the branch's Specs, Protocol and checks, and the worktree's workspace binding tells
  every run which task's goal, Modules and base it works on. Prepare first what Git does not
  track, such as dependencies or build outputs, as the project's own instructions say.
- **Change directly or through Operations.** Inside the task worktree you may change Specs and
  code yourself within the task's goal, verify the change and commit each verified step on the
  task branch, or run Operations for bounded steps and read their results. Never change a file
  outside the task worktree except the task's decision log.
- **Deliver.** `concorde task-validation` shows what would block; `concorde delivery` validates
  the whole workspace again and commits the evidence on the task branch. Never rebase or switch
  branches, and never merge the task branch into the primary branch: that merge is the main
  agent's step, from the primary worktree. The only merge you make is the one the main agent asks
  for after its merge of the task failed with `merge_conflict`: merging the primary branch into
  your task branch, as "A merge conflict" below says.
