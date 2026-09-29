# Decision log: panel-larger-tasks

Goal: Finish the 2026-09-28 panel review's larger items for Coordination and Tasks: split Tasks' bundled scenarios with their tests' @verifies, and add the normal-path and task merge flow diagrams

## Brief from the main agent (panel-review LARGER items)

These items are the "larger" findings left from the 2026-09-28 `spec_panel` review (decision
history in `/home/zhenyu/concorde/.concorde/tasks/panel-review-fixes.decisions.md`). They are
confirmed real problems that need no design decision but are not small edits. Full review reports
(chair report and verdict per Module) are readable at
`/tmp/claude-1000/-home-zhenyu-concorde--claude-worktrees-panel-review-fixes/dbd505b3-74e1-499b-9440-e3cc4b821993/work/reports/module.<name>.md`
and `module.<name>.verdict.md`.

How to work:
- The project has changed a lot since the review. Check each item against the current Specs and
  code first. If it is already solved or no longer applies, record that here with the reason and
  skip it.
- If doing an item needs a design decision (narrowing or changing a promise, changing behaviour,
  a word choice that is not obvious), do not decide it: escalate to the main agent with options
  and a recommendation. Never narrow a Spec promise to fit the code; a Spec/code difference where
  it is unclear which is intended is escalated.
- Splitting a scenario: keep the original id on the first scenario; each new scenario id needs a
  test with `@verifies`, otherwise spec-validation warns `CONCORDE-COVERAGE-001`. Change the Spec
  and the tests' `@verifies` in the same commit, and only where the existing test really checks
  that scenario's outcome; otherwise add or extend a test.
- Diagrams: `d2 illustrative` blocks, following the diagram rules in the Protocol
  (`.concorde/protocol/`) and the project's Specs. "Don't draw diagrams for trivia": when the prose
  already says it plainly, skipping is fine; record why here.
- Usage items: restructure Usage so it opens with / contains a worked normal path, keeping every
  existing statement true.
- Use the glossary terms (`specs/concorde/glossary.json`) exactly. Edit only files of your
  Modules where possible; if another Module's file (or the glossary) must change, keep the change
  minimal and say so in your report.
- Never commit files a Bash sandbox mounts into the worktree (`.bashrc`, `.claude/...`).
- When done: task-validation and delivery, then report to the main agent: each item done or
  skipped (with reason), the decisions you took on your own, and anything waiting for a decision.

### Items of this task (handover list)

**module.coordination**
- C · F5: the normal path across the primary worktree and the task worktree (diagram).

**module.tasks**
- A · F26: split `open-inherits-worker-models`, `close-completed`, `close-failed`, `merge-waits`, `escalate`, `close-s...`, etc.
- C · F21: flow of `task merge` (now including the `merging` state, `--resume`/`--abort` and `workspace_busy`).

### Verdict text for each item (from the review's verification agents)

#### module.coordination

##### F5 LARGER — No flow view of the normal path
The branch and rejoin are already described in prose, so this is only about clarity. To do: add an illustrative d2 flow beside the Usage normal path. It needs lanes for the primary worktree (main agent) and the task worktree (main agent or task session), running open task → work (self or delegated) → validate → deliver → merge from the primary worktree → report.



#### module.tasks

##### F21 LARGER — The Merging passage needs a command-flow diagram
This is real but advisory, and it needs a new d2 diagram. Add a `d2 illustrative` activity view beside Merging with these steps: take lock, preflight (`not_merged`/`dirty_worktree`/`primary_dirty`), `git merge` (`merge_conflict` → abort), checks (`check_failed` → `reset --keep`, leftovers named), `rollback_failed`, close (a failed close leaves the checked merge and tells the caller to run `close --merged`). Each branch should show the resulting primary-branch and task state. Best done after F12 and F13 are decided, since they change the flow.

##### F26 LARGER — Scenarios bundle alternative situations
This is real: protocol templates/scenario says "Write separate scenarios for situations whose successful, failed, repeated or concurrent outcomes differ". The affected scenarios are open-inherits-worker-models (file present / absent), close-completed (no note / note without force / note with force), close-failed (invalid input / run / no-error), merge-waits (released / busy), escalate (success / refusals) and close-submodules. Splitting them adds scenario ids that need `@verifies` declarations in tests/concorde/tasks/test_store.py and test_merge.py (Tasks' tests), so it is more than a Spec edit. Do it as one pass over scenarios.md plus the tests. open-taken and merge-refused-early are fine as single-WHEN scenarios.



## Task session log

### F26: splitting Tasks' bundled scenarios (decided without the developer)

Checked against the current `scenarios.md` first. `open-inherits-worker-models` no longer exists: it
became `open-carries-worker-configuration`, which no longer bundles "file present / file absent";
what is left is one timeline about one base commit (open, then a later commit on the primary
branch, then a later task). **Skipped** it: splitting would only repeat the same fixture three times.

Split, keeping the original id on the first (the successful) scenario and giving each alternative
its own GIVEN and WHEN:

- `close-completed` → `close-completed` (note and `--force`), `close-completed-no-note`
  (`invalid_input`), `close-completed-dirty` (`dirty_worktree` without `--force`).
- `close-failed` → `close-failed` (`--run`), `close-failed-no-error`, `close-failed-invalid`
  (`invalid_input`; the test already checked a missing reason too, so the scenario names it).
- `close-submodules` → `close-submodules` (clean submodule closes), `close-submodules-dirty`.
- `merge-waits` → `merge-waits` (released within the wait), `merge-busy` (held for the whole wait).
- `escalate` → `escalate`, `escalate-refused` (`unknown_run`, `nothing_to_escalate`).

Beyond the verdict's list ("etc." in the handover), the same defect was in scenarios written after
the review, so I split them too: `merge-resume` → `merge-resume`, `merge-resume-check-failed`,
`merge-resume-refused` (`not_merging`, `not_resumable`, `invalid_input`); `merge-abort` →
`merge-abort`, `merge-abort-diverged`; and `close-rerun`'s refusal of another outcome →
`close-other-outcome` (`invalid_transition`), which also states the trigger F22 asked about.
Reason: the Protocol's scenario rule ("separate scenarios for situations whose successful, failed,
repeated or concurrent outcomes differ") applies to them identically.

Left as they are: scenarios whose BUT/AND steps follow one situation through time or name a
contrasting non-outcome of the same action (`first-run`, `busy`, `delivered-reopened`,
`delivery-unverified`, `merge-interrupted`, `merge-live-busy`, `closed-inert`, `round-closed`,
`sandbox-masks`), and the single-WHEN refusals the verdict accepted (`open-taken`,
`merge-refused-early`).

Tests: each new id is declared by a test that checks its outcome. `close-completed` and
`close-failed` tests were split into one test per scenario; the tests for `close-submodules`,
`merge-waits` and `close-rerun` share one fixture for two situations and declare both ids. Where a
new scenario states "nothing changed", the test now asserts it (record, decision log, primary
head). `escalate-refused` gained a check of `nothing_to_escalate`, which no test covered before.
The `--check` with `--resume` refusal moved from the resume success test to the refusal test.
No promise was narrowed or widened: every new step restates an outcome the bundled scenario, the
Usage prose or the contracts already promised.

### C · F21: `task merge` flow diagram

Added a `d2 illustrative` flow beside Merging in `tasks/module.md`: locks (`workspace_busy` /
`merge_busy`), preflight refusals, record `merging`, `git merge` of the checked commit
(`merge_conflict`), checks, `git reset --keep` (`check_failed`, `rollback_failed`), close (a failed
close leaves `merging`), the process ending mid-merge, and `--resume` / `--abort` from `merging`.
`not_resumable` and `merge_diverged` are left to the prose to keep the picture readable. F12/F13
(the verdict's dependency) are already reflected in the current Merging prose, which the diagram
follows. Node `left` was renamed `unchecked` because `left` is a reserved d2 keyword.

### C · F5: Coordination normal path diagram

Added a `d2 illustrative` flow right after the Usage normal path in `coordination/module.md`,
with the primary worktree (main agent) and the task worktree (main agent or task session) as
lanes: open → work → validate → deliver → merge → report. Prose unchanged.

### Results

- First run of the split tests: `close-failed-invalid` failed with `unknown_run` because it named a
  made-up run id (`--run` is resolved before the argument checks). Fixed by naming a real failed
  run, as the original test did; the Tasks tests then passed (82 passed).
- `ruff check` reports `PLW1510` at `tests/concorde/tasks/test_merge.py:427` (`subprocess.run`
  without `check`). That line is older than this task and outside its change; left alone.
- My first `task-validation` result file was overwritten by another session's run because `$TMPDIR`
  is shared across sessions; reran with a private file. `task-validation`: ok, ready, no blocking
  findings. `delivery`: ok, delivery commit `0757250b` with `.concorde/evidence/panel-larger-tasks/1.json`.

## 2026-09-29 — Main agent: independent review of delivery 1

- Independent review MERGE-WITH-NOTES (nothing dropped, no promise narrowed). Sent back for small
  overstatements of the code: close-failed-invalid's GIVEN (unknown run gives unknown_run),
  merge-resume-check-failed's unconditional "clean", the merge diagram's refusal node and
  "close failed → merging" label (false for decision_log_failed), and the missing
  unchanged-record assertions for not_merging and not_resumable.

### Fixes after the main agent's review

- a. `close-failed-invalid`: GIVEN is again a task whose workspace has an Operation run that ended
  with an error (`--run` is resolved before the argument checks, so another run gives
  `unknown_run` or `nothing_to_escalate`).
- b. `merge-resume-check-failed`: "clean apart from the paths the checks created, which stay", as
  in `merge-check-failed`.
- c. Merge diagram: the refusal node now says "A refusal such as ..." and names `merge_incomplete`
  too. The failed close is split in two: "the record could not be closed" leads to merging, and a
  new node shows that `decision_log_failed` leaves the task closed as merged and that
  `close --merged` appends the closing (my choice over only relabelling, so both outcomes show).
- d. `merge-resume-refused` test asserts the primary head and the record unchanged right after
  the `not_merging` and the `not_resumable` refusals.
- Tasks tests 82 passed; build --check and spec-validation clean.

## Closed: merged, 2026-09-28T20:00:36Z
