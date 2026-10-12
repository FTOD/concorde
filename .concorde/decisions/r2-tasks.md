# Decision log: r2-tasks

Goal: Fix the critical, high and obvious-fix open Issues of Tasks and Coordination found by the complete project_review, the critical first (I-f2433900)

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08) that this round fixes the **critical and high** open Issues of
every Module, plus each Module's **obvious-fix** Issues since they are cheap; medium and low
Issues of other tiers wait for a later round. This task resolves the 25 Issues in its `resolves`,
owned by its Modules, found by the complete project_review
r-20261008T063808-project_review-9851e69f (unbound; reports under
`.concorde/unbound/r-20261008T063808-project_review-9851e69f/` of the primary worktree) or
earlier. Read each with `concorde issues show`. Other open Issues of these Modules are out of
scope: do not fix them, even when nearby, unless a fix in scope needs it.

By tier:
- **decision-needed**: read them first and escalate them all **together in one report, early**,
  each with what you found, the options and your recommendation; continue with the rest
  meanwhile. Never settle one yourself.
- **preferred-fix**: fix with the fix you judge best; report the choice.
- **obvious-fix**: fix.
- Work critical first, then high.
- An Issue that does not hold, is a duplicate or is already fixed: say so with evidence in the log
  and in your report; the main agent closes it.
- A fix needing a change outside the task's Modules: escalate, unless it is a small mechanical
  follow-on (a link, a fixture, a registry refresh).

Eleven other round-2 tasks run in parallel, each on other Modules (r2-*). If a merge conflict
comes back, the main agent asks you to merge the primary branch in. Deliver with
`task-validation` then `delivery`; run the full suite once on the final input.

## Task session: decisions (2026-10-08)

None of the 25 Issues is `decision-needed`, so nothing was escalated early. Every Issue holds;
none was a duplicate or already fixed. All 25 are fixed on the task branch (5cd99ec15, 40c894c03,
e329f09ce).

Critical:
- I-f2433900 (obvious-fix): `_changes` now runs `git status` with `check=True`, so a failed status
  on a worktree that still exists is `git_failed`, never a clean worktree; a concurrently removed
  worktree still has no changes. Regression: a corrupt index refuses a close of a worktree with
  submodules and keeps the uncommitted file.

High, preferred-fix choices:
- I-c7c310ea: after every merge check, before any rollback, the merge verifies the primary
  worktree is on `merging.branch` at `merging.after`; otherwise `merge_diverged`, nothing reset, the
  task stays `merging` and the marker stays (restore by hand, then `--resume`/`--abort`). Checked
  after each check, not only at the end, because the failed-check rollback `git reset --keep`s
  whatever branch is checked out. New scenario.tasks.merge-check-moved.
- I-b30275fd: new `store.refuse_foreign_marker`, called by `mark_merge` (so a new merge never
  replaces another part's marker) and at the start of every close (before any mutation, which
  also covers its decision-log commit). Codes follow Issues' own: `merge_incomplete` with the
  marker's account, and a new `unreadable_merge_marker` (environment). New
  req.tasks.foreign-marker-refused and scenario.tasks.merge-foreign-marker.
- I-1890c160: req.tasks.merge-serialized and the merge-lock contract now say the lock is held from
  before reading the task records (open: its start; merge/close: once the workspace lock is held)
  to the end of the command, and name what lies outside it.
- I-f95aa6b2: req.tasks.merge-all-or-nothing allows the branch to be at bookkeeping commits on top
  of the checked merge, adds the check-moved case, and separates "close failed before the record
  was closed" (resume/abort) from "closed with steps left" (`close --merged`).
- I-2a23fd3b / I-90479f43 (obvious-fix): Tasks now relies on contract.execution.run-result, uses
  module.workflows (req.workflows.workflow-lock-leaf, req.workflows.workspace-retired) with a new
  `#uses-workflows` section explaining the optional integration, and includes
  document.execution.runner, document.issues.interface, document.spec.contracts and
  document.workflows.contracts, each with its reason. Registry mirror refreshed.
- I-932146a9 / I-acff4bba: Coordination's entry lists every way a main session hears of delegated
  work (report + SendMessage, own background Bash, registered waits and server-started merges,
  linking Main session's Owners) and states the merge audit's exact refusals, warning and
  exclusions, linking Tasks' audit.

High/medium obvious-fixes: I-74247e04 (earlier attempt write failures become warnings),
I-52661fbf (clean-worktree condition restored, linked to Task state), I-025f794a (`open --wait`),
I-50a8db28 (resume checks the recorded branch before cleanliness), I-c427bdb2 (marker_unwritable
is environment), I-ee6833b4 (runner liveness before a saved result), I-e8595bfd (history-aware
escalate/merge; `merge --resume/--abort` of a task in the history answers `not_merging`),
I-8ccddc9d (live set excludes ended records), I-b33dd3af (`_still_unended` inside every retried
report/answer/rebind/session update), I-277e8e38, I-c32339c0, I-c7f4fe45, I-e29a1a8e (split into
merge-commit-recorded, merge-marker-updated, merge-marker-removed, merge-warns-delivered,
deliver-recovered, state-read-only; original identities kept for the first duty so links stay),
I-f4b1db71, I-8ba85566.
- I-067df4e5: the test's `unfinished_merge` hook fired twice, first at the close's preflight
  without the workspace lock, which started a stray run that finished at once and made the test
  wait its full 30 s. It now launches the run only under the close's workspace lock and waits for
  the detached runner to exit before cleanup (31 s -> 0.65 s; passed 5 of 5 runs).

## Report 1 to the main agent (Review流程), 2026-10-08T14:18:06Z

r2-tasks delivered: delivery commit 49887c41f (run r-20261008T140732-delivery-f21304d1), task-validation ready, full suite 1384 passed / 5 skipped, spec-validation success.

All 25 Issues in resolves are fixed on the branch; none was decision-needed, a duplicate or already fixed, so nothing is escalated. Critical I-f2433900: a failed git status is now git_failed, never a clean worktree, so a close can no longer force away a worktree with submodules and uncommitted work (regression test with a corrupt index).

Preferred-fix choices (details in the decision log):
- I-c7c310ea: after each merge check, the merge verifies the primary worktree is still on its branch at the merge commit; otherwise merge_diverged, nothing reset, task stays merging with its marker (restore by hand, then --resume/--abort). New scenario.tasks.merge-check-moved.
- I-b30275fd: a merge and every close refuse another part's unfinished-merge marker (merge_incomplete with its account) or an unreadable one (new code unreadable_merge_marker, environment) before changing anything. New req.tasks.foreign-marker-refused, scenario.tasks.merge-foreign-marker.
- I-1890c160 / I-f95aa6b2: merge-lock lifetime and merge outcomes restated (bookkeeping commits allowed after the checked merge; close-failed-before-record vs closed-with-steps-left recovery).
- I-2a23fd3b / I-90479f43: Tasks now relies on contract.execution.run-result, uses module.workflows (workflow-lock-leaf, workspace-retired) with a #uses-workflows section, and includes Execution runner, Issues interface, Spec contracts and Workflows contracts documents. Registry mirror refreshed. This touches only Tasks' own metadata and entry.
- I-932146a9 / I-acff4bba: Coordination's entry now lists every way a main session hears of delegated work and states the merge audit's exact refusals, warning and exclusions.
- I-e29a1a8e: split into new identities (merge-commit-recorded, merge-marker-updated, merge-marker-removed, merge-warns-delivered, deliver-recovered, state-read-only); the original identities keep the first duty so existing links hold.

Also: task open takes --wait; task show reports running while a runner holds its run lock even with its result saved; escalate/merge of a task in the history are refused for its state; retried record updates recheck that the task has not ended; the flaky closing-workspace test (I-067df4e5) launched a stray run at the close's preflight and waited 30 s; it now launches only under the lock and waits for the runner's exit (31 s to 0.65 s).

Nothing open.

## Closed: merged, 2026-10-12T14:29:07Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 49887c41fadc1edc8623d406430b99e86db9cece into main and closed it as merged. Nobody answers a report after that.
