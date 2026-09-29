# Decision log: delivery-commit-verify

Goal: Delivery proves what it committed (developer-approved panel-review decisions delivery F7, F10): (1) record git write-tree after staging and, in the post-commit verification, compare it with the new commit's tree, failing commit_unverified naming the difference when a commit hook changed the content; (2) when step 2 recognises the head as a delivery commit, re-verify it before reporting ok/recovered: its single parent equals the bundle's parent_commit, the bundle named by Concorde-Evidence is in the commit and its readiness.run equals the Concorde-Readiness trailer; otherwise fail with commit_unverified naming the mismatch. Spec (module, requirements, contracts, scenarios) and tests.

## Decisions (task session, 2026-09-29)

- **"The bundle is in the commit" read as "the commit adds the bundle".** Options: the bundle
  exists in the commit's tree; or the commit adds it (present in the commit, absent from its
  parent). Chose the second: the Delivery Spec already uses "contains" for a commit's own change,
  Delivery never overwrites a bundle (`bundle_exists`), and the weaker check would accept an empty
  commit whose trailers copy an earlier delivery's bundle and readiness run. Tested by the
  `with_the_parents_bundle` subtest.
- **A failed `git write-tree` after staging is `stage_failed`, undone like any staging failure.**
  Options: a new code, `index_unrecorded`, or `stage_failed`. Chose `stage_failed` with a
  `git write-tree` cause: it happens in step 9 after `git add`, before any commit, so the existing
  undo applies and the status table's "Git refusing (`stage_failed`, …)" already covers it; no new
  code for a case Git should not produce once `git add` succeeded.
- **The recovered-head check parses the bundle JSON but does not validate it against the whole
  bundle schema.** The goal names three checks (parent, bundle present, readiness run); a full
  schema check would go beyond it. Non-JSON or non-object bundles are named as mismatches.
- **`contract.delivery.output` bumped from version 2 to 3.** Its fields are unchanged, but
  `recovered` now requires a verifying head, which is a behaviour change the contract says
  increments the version. Nothing else in the checkout references the version.
- **Both `commit_unverified` paths share one helper with reason `decision`**, options "inspect the
  bound branch and the commit's content" and "revert or remove the commit that does not verify,
  then run delivery again"; the old single option "inspect the bound branch" was widened.
- New requirements `req.delivery.commit-verified` and `req.delivery.recovered-verified`, scenarios
  `scenario.delivery.hook-changed-commit` and `scenario.delivery.recover-unverified`, verified by
  new tests which fail on the previous code and pass now.

## Results

- `spec-validation` first reported `CHK.requirement.statement` errors for both new requirements
  (two SHALLs each); reworded each into a single SHALL clause, then `success`.
- `ruff check` reports a pre-existing ISC004 in `require_verified_scenarios` (command.py, the
  `unverified_scenarios` options list); not introduced by this task and left unchanged.
- Full suite: 664 passed, 4 skipped.

## Open (outside module.delivery)

- Tasks derives "delivered" from the branch head being a delivery commit by subject and trailers
  only (`store.deliveries`); a head that fails the new verification still counts as delivered
  there. Whether Tasks should use `delivery_mismatches` is for the main agent / module.tasks.

## Closed: merged, 2026-09-28T17:22:52Z
