# Decision log: tasks-verified-delivery

Goal: Tasks counts a task as delivered, and task merge accepts it, only when its branch head is a delivery commit that verifies, using Delivery's delivery_mismatches check (single parent equal to the bundle's parent_commit, the commit adds the bundle Concorde-Evidence names, its readiness run equals Concorde-Readiness): today store.deliveries recognises a delivery commit by subject and trailers only, so a head Delivery reports commit_unverified would still be delivered and mergeable (follow-up of the developer-approved delivery F10). A head that does not verify shows as active with the mismatches, and merge refuses it with a detailed error naming them. Declare the use of Delivery's contract, update the Tasks Spec and tests.

## Decisions taken by the task session, 2026-09-29

- **Refusal code for an unverified head.** Options: reuse `not_merged`; reuse Delivery's
  `commit_unverified`; add a Tasks code `delivery_unverified`. Chose `delivery_unverified`
  (reason `decision`, with options to inspect the head and bundle, and to revert or remove the
  commit and deliver again): `not_merged` means "no delivery at the head" and its options would
  mislead, and `commit_unverified` is Delivery's own code for its run's failure, not a Tasks
  refusal.
- **close --merged too.** The goal names derived state and `task merge`; `close --merged` shares
  `store.mergeable` with merge and requires a delivered head, so it refuses an unverified head
  the same way (req.tasks.merge-verified updated). Keeping one check for both avoids a path that
  closes as merged what merge would refuse.
- **Where the mismatches show.** `task show` lists every delivery with a `mismatches` array (empty
  when it verifies), by a new `store.verified`; `derived_state` and `mergeable` verify only the
  head, so `task list` pays for one verification per task, not per delivery. `store.deliveries`
  stays the plain reader, so Task session's `verify` (pi session reports) is unchanged.
- **Spec declarations.** The `uses module.delivery` entry now relies on `concept.evidence-bundle`,
  `contract.delivery.evidence-bundle` and `req.delivery.recovered-verified` (the rule the check
  implements); the "verifies" definition in Delivery's contracts has no id of its own. Added
  req.tasks.delivery-verified and scenario.tasks.delivery-unverified; bumped
  contract.tasks.record to version 11 since its semantics of `delivered` changed.
- **Test helper.** `tests/concorde/tasks/deliveries.deliver` now commits a real evidence bundle
  (built with Delivery's `build_bundle`) so existing tests keep verified deliveries; its
  `bundle_run` argument makes a bundle that disagrees, or None commits none.

## Results that were not ok

- The first spec-validation after writing the new scenario failed with CHK.scenario.steps (a
  second WHEN after THEN, and a BUT right after GIVEN); rewrote the scenario with one WHEN and one
  THEN. Validation then passed with no findings.
- `uvx ruff` could not create its tool directory under ~/.local/share/uv (read-only in the
  sandbox); ran it with UV_TOOL_DIR in the session's temporary directory. `ruff check` reports 27
  findings in the Tasks files that exist unchanged at the base; the change adds none.

## Open points for the main agent

- Task session's `verify` (src/concorde/tasks/pi_session.py, module.task-session) still accepts a
  pi session report whose delivery commit does not verify, since it only checks that the commit is
  among the task's deliveries; outside this task's Modules, so left as is. Merge refuses such a
  task anyway.

## After delivery

- `task-validation` ended ok (ready, no warnings); `delivery` ended ok with delivery commit
  f229646017ee55195fc1c59271c2d8a29a21ff05 and bundle .concorde/evidence/tasks-verified-delivery/1.json.
- Not ok: `task show tasks-verified-delivery`, run with this branch's code inside the task
  session's sandbox, shows the head verifying (`mismatches: []`) but the state `active`. The cause
  is `_dirty`: the sandbox mounts /dev/null over paths such as .bashrc and .claude/agents, which
  `git status --porcelain` lists as untracked inside the sandbox only. That behaviour predates
  this task; outside the sandbox (the main agent's primary worktree) the paths do not exist.
  Open point: Delivery ignores untracked paths Git cannot version, while Tasks' `_dirty` does
  not; aligning them is a separate Tasks change outside this goal.

## Closed: merged, 2026-09-28T17:38:01Z
