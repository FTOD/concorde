# Decision log: last-nits

Goal: Two small leftovers: (1) task merge's primary-worktree clean check (merge.py primary_dirty) ignores untracked paths Git cannot version (sandbox mount stubs), with the same rule Tasks' _changes now applies, so a main agent in a sandbox is not refused a merge by them; (2) the understand brief (src/concorde/understanding/operation.py) labels the workspace's goal 'The workspace's goal', as specify, implement and test do.

## 2026-09-29 — main agent

- (1) `task merge`'s primary-worktree listing (`merge._status`, used for `primary_dirty` and for
  the paths checks leave behind) now reuses Tasks' `_changes`, which leaves out new paths Git
  cannot version (sandbox `/dev/null` mounts). Decision: one rule for task and primary worktrees
  rather than a second copy. New scenario.tasks.merge-sandbox-masks with a bwrap test that fails
  on the previous code; req.tasks.merge-clean-primary explains the exception.
- (2) The understand brief labels the goal "The workspace's goal", as specify, implement and test.
- Verification: spec-validation 0/0, build --check clean, pytest 686 passed / 4 skipped.

## Closed: merged, 2026-09-28T18:51:43Z
