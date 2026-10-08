# Decision log: fix-scaffold

Goal: Fix every open Issue of Scaffold: the stale-content overwrite in planning (critical), parent entries without a Parts section, vendored paths other Modules bind, colliding relation anchors, admission bypassing stale-proposal handling, and the Spec wording Issues

## Task brief (main agent, 2026-10-08)

The developer decided (2026-10-08): fix every known open Issue before the first full
`project_review`. This task resolves every open Issue owned by `module.scaffold` (10, listed in the
task record's `resolves`), found by project_review run r-20261006T193742-project_review-4cbffb26.
Read each with `concorde issues show`.

Tiers and how to handle them:
- **I-468535e4 (critical, preferred-fix)**: planning computes replacement content from one read and
  the transaction's before_digest from a later read, so a concurrent edit can be silently lost.
  Fix first; follow the suggested repair (one snapshot per source file for both content and digest,
  explicit absent-file precondition for children, regression test of a concurrent edit ending
  `stale_proposal` with the edit preserved) unless you find a clearly better one; report the fix.
- **I-85a2aaa2 (decision-needed), decided by the main agent**: when a parent's entry has no Parts
  section, Scaffold creates one and appends the child explanations, keeping the existing prose
  unchanged; add a scenario for such a parent.
- **I-b95ea491 (decision-needed), decided by the main agent**: when a vendored path is also bound
  by an existing Module other than the surveyed parent, Scaffold refuses before writing anything,
  naming each conflicting Module and path; define the status and error code and add a scenario.
  This concerns module.adoption too (bound to this task).
- **preferred-fix** I-1b78b455, I-3766dd3e, I-db43e3a8: fix, report the fix you chose.
- **obvious-fix** I-27c12836: fix.
- **suggestions** I-464c5674, I-c403fd87, I-39d3c913: apply them too (the developer asked for
  every known Issue), unless one turns out wrong; then say why in the log and leave it open.

Left to the session: everything else of ordinary scope. Escalate anything that changes what
Scaffold or Adoption promise beyond these decisions.
Deliver with `task-validation` then `delivery`; run the full suite once on the final input.

## Task session decisions (2026-10-08)

- **I-468535e4 (critical, preferred-fix)**: chose a variant of the suggested repair that is
  strictly stronger: the plan derives every replaced file's content *and* its `before_digest`
  from the bytes the recheck's `SpecRepository` loaded and validated (`loaded_bytes`, and
  `registry_bytes` for the registry), not from a fresh read in the plan. So the content, the
  narrowing (computed from the same repository) and the digest share one snapshot, and any change
  after the recheck ends `blocked`/`stale_proposal` with the change kept. Created files carry an
  explicit `before_digest: null` (absence precondition) instead of `file_change`'s reread. A
  parent document whose bytes the repository could not read ends `failed`/`specs_unloadable`.
  New requirement `req.scaffold.one-snapshot` and `scenario.scaffold.concurrent-edit`, with a
  regression test that edits the parent's entry between the snapshot and the transaction.
- **I-85a2aaa2 (main agent's decision)**: the code already appended a new `Parts` section at the
  end of an entry without one; specified it in `req.scaffold.contained` and the entry, added
  `scenario.scaffold.no-parts-section` and its test.
- **I-b95ea491 (main agent's decision)**: implemented the refusal as one more Adoption proposal
  check (`proposal_problems`): a vendored path any file of which a registered Module other than
  the surveyed one binds. Thus the scaffold's recheck ends `blocked` with `stale_proposal`, one
  `proposal_mismatch` cause per conflicting Module naming the Module, its binding entries and the
  path, before writing; and the survey refuses the same proposal with `inconsistent_proposal`.
  Reason: the survey would otherwise return an `ok` proposal the scaffold can never apply, and
  the recheck reuses Adoption's checks by design, so `stale_proposal` is accurate (only a change
  after the survey reaches the scaffold). New `req.scaffold.vendored-bound-elsewhere`, a bullet in
  `req.adoption.proposal-checked`, `scenario.scaffold.vendored-bound-elsewhere`,
  `scenario.adoption.vendored-bound-elsewhere`, tests, and one sentence in the survey worker's
  prompt.
- **I-1b78b455 (preferred-fix)**: chose the suggested injective encoding: relation anchors keep
  the dots of the local identity (`contains-stock.hold` vs `contains-stock-hold`); identities with
  one segment keep their old anchors. `scenario.scaffold.distinct-anchors` and a test with two
  colliding children used by a third.
- **I-3766dd3e (preferred-fix)**: removed Method's Module admission from `SCAFFOLD` (it only
  overwrote `ctx.modules`, which the `admit` step sets anyway); the runner still admits the
  workspace and the input. A removed/renamed surveyed Module now reaches the recheck
  (`blocked`/`stale_proposal`, `proposal_mismatch` cause) and unloadable Specs reach
  `specs_unloadable` with Spec core's error as cause. Scenarios `surveyed-module-removed` and
  `specs-unloadable` with tests.
- **I-db43e3a8 (preferred-fix)**: added to Results and errors the interruption limit with a link
  to Spec core's File transactions contract and the instruction to inspect and repair the
  workspace before retrying a lost or interrupted run.
- **I-27c12836 (obvious-fix)**: the overview now says no file stays bound by both parent and child,
  deliberate sharing among children stays, vendored code leaves every Module, linking
  `req.scaffold.parent-narrowed`.
- **Suggestions applied**: I-464c5674 (split `write-failed`/`restore-failed`,
  `unbound`/`bound`, `refused-input`/`foreign-input`, and the vendored variants into
  `vendored-inside-child` and `vendored-child-entry`, which links Adoption's proposal checks;
  tests re-declared accordingly); I-c403fd87 (`no-overwrite` condition first; `rechecked` keeps
  the unconditional recheck and moves the mismatch condition just before the failure reaction);
  I-39d3c913 (the scaffold host is now the actor of `vendored-external`, `parent-narrowed`,
  `stub-honest`, `stub-unspecified` and `step-output`).

## Report 1 to the main agent (concorde-d4), 2026-10-08T01:54:34Z

fix-scaffold delivered: delivery commit bb7cfd94 (run r-20261008T015346-delivery-1e79e257) on concorde/fix-scaffold, over d6b42164. task-validation ready; build --check and spec-validation clean (0 errors, no new warnings); full suite 1295 passed, 5 skipped on the final input.

Resolves all 10 Issues in the task record (already listed in resolves):
- I-468535e4 (critical, preferred-fix): the plan now derives each replaced file's content AND before_digest from the bytes the recheck's SpecRepository loaded and validated (loaded_bytes / registry_bytes), a stronger form of the suggested single snapshot: content, narrowing and digest share one state. Created files bind explicitly to absence. A change after the recheck ends blocked/stale_proposal with the change kept. New req.scaffold.one-snapshot + scenario.scaffold.concurrent-edit + a regression test (fails on the old code).
- I-85a2aaa2 (your decision): a Parts section is added at the end of an entry without one, prose unchanged; req.scaffold.contained + scenario.scaffold.no-parts-section + test.
- I-b95ea491 (your decision): implemented as one more Adoption proposal check, so the scaffold's recheck refuses before writing with blocked/stale_proposal, one proposal_mismatch cause per conflicting Module naming the Module, its entries and the path. The survey refuses the same proposal with inconsistent_proposal, since it would otherwise return an ok proposal no scaffold can apply. New req.scaffold.vendored-bound-elsewhere, a bullet in req.adoption.proposal-checked, scenarios in both Modules, tests, and one sentence in prompts/workers/survey.md.
- I-1b78b455: anchors keep the dots of the local identity (contains-stock.hold vs contains-stock-hold); one-segment identities are unchanged. Scenario + test.
- I-3766dd3e: dropped Method's Module admission from SCAFFOLD (the runner still admits the workspace and the input), so a removed/renamed surveyed Module gives blocked/stale_proposal and unloadable Specs give failed/specs_unloadable with Spec core's error as cause. Two scenarios + tests.
- I-db43e3a8: Results and errors now explains the interruption limit, links Spec core's File transactions, and says to inspect and repair the workspace before retrying.
- I-27c12836: the overview no longer says "no file is bound twice": parent/child overlap removed, deliberate sharing among children kept, link to req.scaffold.parent-narrowed.
- Suggestions I-464c5674 (scenarios split, tests re-declared), I-c403fd87 (conditions moved before the reactions), I-39d3c913 (scaffold host named as actor): all applied.

Decisions taken without the developer are in the decision log. Nothing is open and nothing of major impact needs the developer.

## Closed: merged, 2026-10-08T01:54:58Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit bb7cfd948376abf85698fe0e2e760e9889400b05 into main and closed it as merged. Nobody answers a report after that.
