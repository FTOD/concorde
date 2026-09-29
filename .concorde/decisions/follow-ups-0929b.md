# Decision log: follow-ups-0929b

Goal: Small follow-ups: (1) developer's decision: concorde task escalate may be run without --run, --error-file or --escalation; it then records the main agent's or task session's own link with no causes as the whole chain (the shape the dogfooding F5 guidance writes by hand), so a decision an ok no-ask workflow took can be escalated; update the Tasks Spec and the main-session, task-session and dogfooding guidance that currently works around it; (2) pi_session.verify accepts a delivered session report only when its delivery commit verifies (Tasks' store.verified / Delivery's delivery_mismatches); (3) Tasks' clean-worktree check ignores untracked paths Git cannot version (e.g. sandbox mount stubs), as Delivery does; (4) Workflows' module.md and req.workflows.one-at-a-time no longer say a finished step leaves the workspace free (a step waits for the lock; Execution's corrected property); (5) specify's brief heading 'The task's own goal' becomes 'The workspace's goal', as implement and test use; (6) Distribution's wording that init --apply 'applies exactly the proposal it printed' matches Spec core's restated guarantee (shape, integrity, freshness). Specs, prompts (then build) and tests.

## (1) Escalation without an error

- Decision: `concorde task escalate` with no `--run`, `--error-file` or `--escalation` records the link alone; `nothing_to_escalate` stays only for a named run that ended without an error. Added `scenario.tasks.escalate-decision` (verified by a new store test) instead of stretching `scenario.tasks.escalate`. Reason: the goal's developer decision; a separate scenario keeps the error-escalation scenario about causes.
- Decision: the task-session guidance now has a task session escalate a major-impact decision of an ok no-ask workflow with `--by task-session` naming no run or file (and then, like every escalation, send the chain and wait), rather than only naming it in its report. Reason: the goal asks the guidance that worked around the refusal to use the new shape; recording it in the task record keeps it for the developer.
- Decision: the dogfooding guidance builds an ok-run defect's link with `task escalate` without `--run` inside a task, citing the run in `--detail` (escalate has no evidence option); outside a task the hand-written link, with evidence citing the run, stays. Reason: adding an `--evidence` option is beyond the goal; the report's own `evidence` field already cites the run's files.

## (1) Escalation without an error — commit 29de8cce

- Decision: `concorde task escalate` with no `--run`, `--error-file` or `--escalation` records the escalating session's link alone as the whole chain; `nothing_to_escalate` stays only for a named run that ended without an error. Added `scenario.tasks.escalate-decision` (verified by a new store test) rather than stretching `scenario.tasks.escalate`. Reason: the goal's developer decision; a separate scenario keeps the error scenario about causes.
- Decision: the task-session guidance now has a task session escalate a major-impact decision of an ok no-ask workflow with `--by task-session` naming no run or file (then, like every escalation, send the chain and wait), instead of only naming it in its report. Reason: the goal asks the guidance that worked around the refusal to use the new shape; recording it keeps it in the task record for the developer.
- Decision: inside a task, the dogfooding guidance builds an ok-run defect's link with `task escalate` without `--run`, naming the run in `--detail` (escalate has no evidence option); outside a task the hand-written link, with evidence citing the run, stays. Reason: an `--evidence` option is beyond the goal; the report's own `evidence` field cites the run's files.

## (2) Verified delivery commit in pi session reports — commit cce3be50

- Decision: `pi_session.delivered_record` now carries `store.verified` deliveries and `verify` adds one mismatch per failing check of the named commit ("does not verify against its evidence bundle: …"). Bumped `contract.task-session.report` to version 3 with a note on what version 2 accepted. Reason: the contract says a behaviour change increments its version; the field set is unchanged.

## (3) Clean-worktree check ignores unversionable paths

- Decision: Tasks' `_changes` lists `git status --porcelain -z --no-renames --untracked-files=all` and drops untracked entries that are neither file, symlink nor directory, the rule Validation's `measurement._special` applies; written inside Tasks rather than importing `concorde.validation.measurement`, since Tasks declares no use of Validation. Reason: keep Tasks' relations as declared.
- Decision: kept changes inside a submodule counting (did not add `--ignore-submodules=dirty` as Validation does): `scenario.tasks.close-submodules` requires closing to refuse them, since removing the worktree would lose them.
- Decision: left `merge.py`'s primary-worktree check (`primary_dirty`) unchanged; the goal names the task worktree's clean check. Open point: a main agent in a Claude Code sandbox could see the same stubs in the primary worktree.
- Added `scenario.tasks.sandbox-masks` with a bubblewrap test (skipped where bwrap cannot run); confirmed it fails against the previous store.

## (4)–(6) Wording — commits ef97698c, 31320c5e, ce1b76d8

- (4) Workflows' module and `req.workflows.one-at-a-time` now say a step's run finds earlier results written but a result on disk does not mean the lock is free, so the next step waits for the lock (Execution's wording from 0a56c11a).
- (5) Decision: kept specify's goal as a line in its "This run" section, relabelled "The workspace's goal:", rather than moving it to a `## The workspace's goal` section like implement. Reason: minimal change of the label the goal names. Open point: `src/concorde/understanding/operation.py` still says "The task's own goal"; module.understanding is outside this task's Modules.
- (6) Distribution's module now says `init --apply` is held to shape, integrity and freshness, linking `req.spec.init-explicit-envelope`.

## Delivery

- Full suite: 694 passed, 4 skipped. `task-validation`: ok, ready. `delivery`: ok, delivery commit f0a6ca4703a0af173c351073b60631b7e51d3d79 with `.concorde/evidence/follow-ups-0929b/1.json`.

## Closed: merged, 2026-09-28T18:46:02Z
