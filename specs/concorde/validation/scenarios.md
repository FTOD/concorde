# Validation scenarios

These situations show how [Validation](module.md) behaves. The obligations they demonstrate are
defined once in [Validation requirements](requirements.md).

## Readiness

### scenario.validation.ready — A planned change that meets every gate becomes ready

- GIVEN a candidate whose accepted tasks for the validated Module are complete
- AND every review the change requires is current and no Blocker is open
- WHEN the user session calls `concorde-validate` in the candidate's worktree
- THEN the Host validates the Specs and runs the configured checks of every affected Module
- AND records the evidence bound to the candidate's exact files
- AND answers with outcome `ready` and marks the change ready with its validated tree
- BUT the answer does not claim semantic completeness

### scenario.validation.ready-direct — A direct candidate becomes ready without a plan

- GIVEN a change with no planned Module work whose Specs or code the user session edited directly
- AND every review the change requires is current
- WHEN `concorde-validate` runs in its candidate
- THEN the Host runs every configured check of the project
- AND stores a `validation` record for the requested Module, focus, task and constraints
- AND answers `ready` and marks the change ready with its validated tree

### scenario.validation.incomplete-tasks — Passing checks with unfinished tasks is not ready

- GIVEN a planned change whose configured checks pass but whose validated Module still has an unfinished accepted task
- WHEN `concorde-validate` runs
- THEN the answer is `completed` with the note that semantic completeness is not proven
- AND the evidence is recorded for the target
- BUT the change is not marked ready

### scenario.validation.multi-module — A multi-Module change is validated as one candidate

- GIVEN a change about one Module whose candidate also edits another Module, such as the consumer of a contract whose version the change raises
- AND the other Module's work was completed as component work in the same candidate
- WHEN the user session calls `concorde-validate` for the change's Module
- THEN the configured checks of every edited Module, and of every Module binding one of their files, run and are recorded with their revisions
- AND the change becomes ready only when each of them passed and every component's own completion check passes

### scenario.validation.component-stale — A component changed after completing stops readiness

- GIVEN a planned change whose component work for another Module completed
- AND that Module's Specs or implementation changed afterwards
- WHEN readiness is evaluated for the change's Module
- THEN the request stops with `stale_evidence`
- BUT the change is not marked ready

## Failures

### scenario.validation.failed-check — A failed check blocks the change

- GIVEN a candidate one of whose affected Modules has a configured check that exits with a nonzero status
- WHEN `concorde-validate` runs
- THEN the answer is `failed` and names the failing check
- AND the change is marked `blocked` with outcome `failed_checks`, and a planned target's progress entry is marked `blocked`
- BUT the candidate's files stay unchanged for inspection

### scenario.validation.invalid-spec — Invalid Specs block the change before any check runs

- GIVEN a candidate whose Specs fail a structural check
- WHEN `concorde-validate` runs
- THEN the answer is `failed` and lists the structural errors
- AND the change is marked `blocked` with outcome `invalid_spec`
- BUT no configured check runs

### scenario.validation.check-input-unsafe — An unsafe check input stops validation

- GIVEN a configured check whose explicit input is missing, a symbolic link or not a regular file
- WHEN `concorde-validate` runs
- THEN the answer is `failed` and names the check, its Module and the path
- BUT no configured check runs

### scenario.validation.review-required — A stale required review stops readiness

- GIVEN a planned change whose tasks are complete and whose checks pass
- AND a review the change requires is missing or no longer current
- WHEN readiness is evaluated
- THEN the request stops with `review_required`
- BUT the change is not marked ready or blocked

### scenario.validation.open-blocker — An open Blocker stops readiness

- GIVEN a change with an open Blocker for the validated Module's current task
- WHEN readiness is evaluated
- THEN the request stops with `spec_incomplete`
- BUT the Blocker stays open

### scenario.validation.changed-during-run — A candidate edited during validation is refused

- GIVEN a validation whose checks are running
- WHEN the candidate's deliverable tree or an affected Module's revision changes before the checks finish
- THEN the request stops with `stale_evidence`
- BUT no ready state is recorded

### scenario.validation.sandbox-unavailable — Without the check boundary nothing is recorded

- GIVEN a host on which Check execution cannot set up its read-only check boundary
- WHEN `concorde-validate` runs checks
- THEN the request stops with `check_sandbox_unavailable`
- BUT no check result and no ready state is recorded

## Workspace and repetition

### scenario.validation.without-change — Validation from the primary without a change is refused

- GIVEN the primary worktree
- WHEN the user session calls `concorde-validate` without a `change_id`
- THEN the request is refused with `missing_change`
- BUT no change and no candidate worktree is created

### scenario.validation.relayed — Validation from the primary runs in the change's candidate

- GIVEN a change with a live candidate
- WHEN the user session calls `concorde-validate` from the primary worktree with that change's `change_id`
- THEN the request is relayed into the candidate and validates it there
- AND the user session receives the candidate's answer

### scenario.validation.checks-skipped — Skipping checks never fakes them

- GIVEN a planned change whose tasks are complete and which has configured checks
- WHEN `concorde-validate` runs with `run_checks: false`
- THEN no configured check runs
- AND the request stops with `stale_evidence` because the required check results are missing
- BUT the change is not marked ready

### scenario.validation.repeat — Repeating validation withdraws the earlier ready state first

- GIVEN a change that was ready
- WHEN `concorde-validate` runs again
- THEN the earlier ready state and validated tree are withdrawn before anything is checked
- AND the change becomes ready again only if every gate holds for the current bytes

### scenario.validation.pending-confirmed — Validation confirms created pending files first

- GIVEN a candidate whose Specs declare some realization entries as pending
- AND the change created the files of some of those entries
- WHEN `concorde-validate` runs in the candidate
- THEN the Host removes those entries from their `pending` lists before validating the Specs
- AND the entries whose files are still missing stay pending
- BUT no reading document changes and every entry stays bound
