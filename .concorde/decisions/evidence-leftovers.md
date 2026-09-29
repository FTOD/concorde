# Decision log: evidence-leftovers

Goal: Remove the last statements that delivery commits evidence or cites earlier runs, in the root, Validation and Understanding

## Brief (main agent, 2026-09-30)

Task `stale-statements` (merged `0f4be437`) removed statements left over from dropping the
committed evidence bundle (developer's decision, 2026-09-30) and "delivery cites the run that
decided readiness" (Delivery's own Spec: it decides readiness itself and cites no earlier run) from
Workers, Execution, Commands and Task sessions. It reported four more outside its Modules; fix
them the same way, aligning with Delivery's Spec and changing nothing else:
- `specs/concorde/requirements.md:143` (module.concorde): delivery "commits them together with
  their evidence".
- `specs/concorde/execution/commands/validation/module.md:142` (module.validation): "delivery must
  cite the run that decided a readiness".
- `specs/concorde/execution/operations/understanding/contracts.md:134` (module.understanding):
  example purpose "commit the change with its evidence".
- `src/concorde/validation/command.py:3` docstring: "delivery cites its run".
Grep these three Modules (Specs, prompts, code comments) for any other leftover of the same kind
and fix it too; report, do not fix, anything outside them. Before task-validation and delivery,
stop every background command you started. Run build, spec-validation, task-validation, delivery.

## Task session (2026-09-30)

- Fixed the four statements the brief names, aligned with Delivery's Spec (Delivery decides the
  readiness itself and cites no earlier run; no evidence is committed):
  - `specs/concorde/requirements.md` `req.concorde.delivery-separate`: delivery now "decides their
    readiness itself and commits them only when the workspace is ready" instead of committing them
    "together with their evidence".
  - `specs/concorde/execution/commands/validation/module.md` "How it is built": dropped "delivery
    must cite the run that decided a readiness" from the reasons task-validation is an execution
    command; the workflow step and the caller's evidence and error chain remain.
  - `specs/concorde/execution/operations/understanding/contracts.md` example plan: the delivery
    step's purpose is now "validate the whole workspace again and commit the change".
  - `src/concorde/validation/command.py` docstring: "delivery decides the same readiness again
    itself" instead of "delivery cites its run".
- Grepping the three Modules' Specs, prompts, code and docs found two more leftovers of the same
  kind, fixed the same way:
  - `specs/concorde/scenarios.md` `scenario.concorde.task-to-merge`: the delivery commit holds "the
    change", no longer "the change and its evidence".
  - `specs/concorde/execution/commands/validation/module.md` "Running task-validation": the run
    store record is there "so that a workflow can find it", no longer "so that Delivery and a
    workflow can find it", since Delivery never reads a task-validation run.
- Checked and left unchanged: the root's other "evidence" mentions (run results carry evidence,
  host evidence vs worker claims), `tests/concorde/acceptance/test_flows.py`, which asserts no
  `.concorde/evidence/` path is committed, and Validation's "Delivery can run the same steps".
- Noticed, not changed (other kind, outside the brief): `req.concorde.delivery-separate` still says
  changes reach the task branch "only through" `delivery`, while Delivery's Spec lets the task
  level commit verified steps on the branch and makes only the commit that marks the work
  delivered.
- Verified: build, `build --check`, spec-validation (no findings), pytest of
  `tests/concorde/understanding` and `tests/concorde/validation` (31 passed), task-validation `ok`
  (ready). Delivered as `7a934981` on `concorde/evidence-leftovers`.

## Closed: merged, 2026-09-29T18:59:15Z
