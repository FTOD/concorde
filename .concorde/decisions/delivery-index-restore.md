# Decision log: delivery-index-restore

Goal: When a delivery fails after staging (bundle_exists, measurement_failed while staging, stage_failed, commit_failed), restore the index the readiness examined instead of resetting it to HEAD, using Git's own mechanism (record the index with git write-tree before staging, restore it with git read-tree), so req.delivery.atomic holds; with a test that pre-staged changes survive a failed delivery

## 2026-09-29 — task session

- **Where the index is recorded.** Options: at the start of `commit` (just before staging), or at
  the start of `apply_confirmations` (step 7, the first step that changes anything). Chose step 7:
  `undo` covers steps 7–9 and is also called for `bundle_exists`, so the tree must exist before any
  of them; the index is untouched until staging, so both record the same tree.
- **When `git write-tree` fails** (for example an index with unmerged entries). Options: a new
  failure code, or Validation's `measurement_failed` with a `git_failed` MeasurementError. Chose
  `measurement_failed`: the Spec's `failed` codes already list it, and adding a code would change
  the contract beyond the goal. Nothing has changed at that point, so the workspace stays as
  validated.
- **After `git read-tree`** Delivery runs `git update-index -q --refresh`, because read-tree drops
  the cached stats and Git would otherwise treat every file as possibly modified; its exit status is
  ignored (non-zero only means files differ from the index, which is expected).
- **Error chain on a failed restore.** `undo` now returns a `component` link (`git read-tree <tree>`,
  `git_failed`) when read-tree fails; every caller appends it to the causes of its own error, so a
  failed restore is never silent.
- **Known limit, accepted.** A tree cannot hold intent-to-add markers or skip-worktree /
  assume-unchanged flags, so those are not restored; an intent-to-add path returns as untracked,
  which the readiness measurement counts the same way (same changed paths, same digest).
- **Test.** Extended the existing `scenario.delivery.commit-refused` test instead of adding one:
  it pre-stages `src/new.py` and a version of `src/a/calc.py` the worktree then changes again (`MM`),
  and asserts `git diff --cached` is unchanged after the failure. Confirmed it fails on the old
  `git reset` code and passes on the new. Scenario text and module.md step table / undo paragraph
  updated to say "index restored" from the recorded tree instead of "index reset".
- **Non-ok result, not acted on.** Full suite: 640 passed, 4 skipped, 1 failed —
  `tests/concorde/e2e/test_cases.py::CaseTests::test_grading_runs_the_case_tests_on_a_throwaway_tree`
  (`{'test_calc.py::test_add': 'FAILED'} != {'test_calc.py::test_add': 'not run'}`). It belongs to
  module.swe-bench-cases, imports nothing of Delivery and none of this task's files; outside this
  task's Modules, so left for the main agent.
- **Lint, not acted on.** `ruff check` reports a pre-existing ISC004 in
  `src/concorde/delivery/command.py` (`require_verified_scenarios` options list) that this change
  did not touch; left as is to keep the diff to the goal.

## 2026-09-29 00:23 — second session on the same worktree (stood down)

- **Duplicate session found, stood down without changes.** A second agent was started on this task
  in the same worktree; while it prepared the environment (`uv sync`, `build`, both exit 0) the
  other session committed `25392509`. Options: continue in parallel (two writers in one worktree
  and index, racing on the very index this task protects), or stop. Chose to stop: it changed no
  source, made no commit and ran no task-validation or delivery, and reports the review points
  below to the main agent.
- **Review points on `25392509`, left open for the main agent.** (1) A `git write-tree` failure is
  reported as Validation's `measurement_failed` with the explanation "the measurement reads Git and
  the configuration", and without Git's stdout or a `git write-tree` component cause; an unmerged
  index is a task-level decision (resolve or abort the merge), which a dedicated code with reason
  `decision` would state more precisely. (2) Intent-to-add entries are not restored, although
  `git add -N -f -- <paths>` after `read-tree` would restore them exactly (paths = `git ls-files`
  minus `git ls-tree -r --name-only <tree>`); so the index is not "exactly as before" in that case.
  (3) When undo fails, the summaries still say the index was restored; only the causes show it.
  (4) `confirming.restore` raising OSError in undo is still uncaught (it was already uncaught before this task).
- **Delivered.** `task-validation` ready with no blocking findings; `delivery` run
  r-20260928T162256-delivery-45a21774 committed 9af1ee852d37 with
  `.concorde/evidence/delivery-index-restore/1.json`. No remote push: merging is the main agent's step.

## 2026-09-29 — main agent: duplicate worker, and a task-session start that looked refused

- Non-ok (main agent's mistake): `concorde task session <task> --main ...` printed an error chain
  whose last lines asked for workspace trust ("have the developer run claude once in the task
  worktree and accept the trust prompt"); reading only the tail, I took the start as refused and
  launched a subagent in this worktree as well. The task session had in fact started (a Claude Code
  session in this worktree since 00:18; the task record's `sessions` stays `[]`). The subagent saw
  the session's edits, changed no source and stopped. To examine: why the command reports an
  error while the session runs, and why the start is not recorded in the task record.
- The subagent's review points were sent to the task session to address before delivery.

## 2026-09-29 — task session, second round (main agent's review of 25392509)

The review arrived after delivery 9af1ee85; Delivery allows a later delivery on top, so the fixes
went in as commit 1ad281f9 followed by a second delivery rather than a rewrite.

- **(1) write-tree failure.** Options: keep Validation's `measurement_failed` and add a cause, or a
  Delivery code of its own. Chose a new `failed` code `index_unrecorded` (added to the Spec's status
  table and step 7): the measurement's explanation ("the measurement reads Git and the
  configuration") was wrong for it. Its cause is the failing Git command's own `component` link
  (actor `git write-tree`, `git ls-tree …` or `git ls-files -v -z`) with Git's output. When
  `git ls-files -u` lists unmerged paths the reason is `decision` with the paths as `git` evidence
  and the options "resolve … and stage them" / "abort the merge"; otherwise `environment`.
- **(2) intent-to-add.** Restored as asked: recorded as the paths `git ls-files` lists that
  `git ls-tree -r` of the recorded tree lacks, re-marked after `read-tree` with
  `git --literal-pathspecs add -N -f --pathspec-from-file=- --pathspec-file-nul` (paths on stdin,
  NUL-separated and passed as bytes, so no argument limit and any path Git stores survives).
- **(3) honest summaries.** `undo` now returns an `Undone` value naming each part it could not
  restore; every failed-delivery summary and detail uses it ("the workspace and its index were
  restored as the readiness examined them" or "restoring X and Y failed, so the workspace is not as
  the readiness examined it (see the causes); everything else was restored").
- **(4) OSError in undo.** Each metadata file is written back separately; an OSError becomes a
  `Delivery undo` / `metadata_unrestored` cause, and one removing the bundle `bundle_unremoved`.
  An OSError removing a created directory is still ignored: an empty directory is no content Git
  sees. Every part is attempted even when an earlier one fails; after a failed `read-tree` the
  intent-to-add and flag steps are skipped, since they would apply to the wrong index.
- **(5) tests.** Added `test_git_refuses_to_stage_the_bundle` (a required clean filter that fails
  on `.concorde/evidence/**`, so `git add -A` has already staged everything when the bundle is
  refused), `test_an_unmerged_index_is_refused_before_anything_changes` (stage 1–3 entries through
  `git update-index --index-info`) and `test_a_failed_undo_names_what_it_could_not_restore` (metadata
  over a directory, a missing tree). Both refusal tests share a setup that pre-stages a new file, a
  staged version the worktree changed since (`MM`), an intent-to-add path and both flags, and
  compare status, `ls-files -s`, `ls-files -v` and `diff --cached`. Checked they bite: with the
  intent-to-add/flag restore disabled both refusal tests fail. New scenarios
  `scenario.delivery.stage-refused` and `scenario.delivery.unmerged-index`.
- **(6) skip-worktree / assume-unchanged.** Options: restore with Git, or state the limit in the
  Spec. Chose to restore with Git (`git update-index --skip-worktree|--assume-unchanged -z --stdin`
  from the `git ls-files -v` tags), because under a sparse checkout a read-tree that drops
  skip-worktree would show every file outside the cone as deleted. The Spec's undo paragraph states
  both mechanisms.
- **Non-ok results, unchanged.** Full suite 643 passed, 4 skipped, 1 failed: the same unrelated
  `tests/concorde/e2e/test_cases.py::CaseTests::test_grading_runs_the_case_tests_on_a_throwaway_tree`.
  `ruff check` still reports only the pre-existing ISC004 in `require_verified_scenarios`.
- **Delivered again.** `task-validation` ready, no blocking findings; `delivery` run
  r-20260928T163009-delivery-38a8c338 committed 73da0e3730c1 with
  `.concorde/evidence/delivery-index-restore/2.json`.

## Closed: merged, 2026-09-28T16:32:08Z
