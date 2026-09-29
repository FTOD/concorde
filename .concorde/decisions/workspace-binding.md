# Decision log: workspace-binding

Goal: Decouple the task level from the execution core: the lower half (Operations, commands, workflows, workers) binds a workspace through a workspace binding file instead of a task; worker-less Operations (validate, delivery, scaffold, configure_workers) become concorde commands (validate becomes task-validation beside spec-validation); workflow state leaves the task record; task state is derived from what the lower half records.

## Merged with the branch's own merge code, 2026-09-27

The primary worktree's `task merge` predates this task: it looks for deliveries in the task record,
which this task's new `delivery` no longer writes (the delivery commit on the branch is the record).
It refused with `not_merged`. The same checked merge was therefore run with the task branch's own
code, exported to a scratch directory (so the merge does not remove the code it runs from), with
both checks of DEVELOPING.md. After this merge the primary worktree's code is the new code, so the
bootstrap is needed only once.

## Closed: merged, 2026-09-27T10:03:16Z
