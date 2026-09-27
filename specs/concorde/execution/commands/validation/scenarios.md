# Validation scenarios

Concrete situations that show the [requirements](requirements.md) of [Validation](module.md). The
readiness is defined in the [contracts](contracts.md).

## Deciding readiness

### scenario.validation.ready — A complete workspace is ready

- GIVEN a task worktree bound to the workspace `severity`, whose changes are bound by `module.issues`, whose Specs have no structural error and whose checks pass
- WHEN the task level runs `concorde task-validation` there
- THEN the result has kind `command`, the workspace `severity`, no worker and status `ok`, and its output is a readiness with `ready` true
- AND the readiness records the input measurement and one passed [check result](../../../glossary.json#concept.check-result) per [configured check](../../../glossary.json#concept.configured-check) of `module.issues`
- AND nothing in the workspace changed

### scenario.validation.not-ready — Every blocker is reported in one run

- GIVEN a workspace with a broken [Spec](../../../glossary.json#concept.spec) link, a new file bound by no [Module](../../../glossary.json#concept.module) and a failing check of a changed Module
- WHEN `task-validation` runs
- THEN the result has status `blocked` and the readiness has `ready` false
- AND `blocking` holds a structural finding, an unbound finding and a check finding
- AND the summary names each finding with its location and message
- AND the error's `not_deliverable` link, of level `command`, has one cause per finding, the check's with its exit code and the end of its log

### scenario.validation.warnings — Warnings do not block

- GIVEN a workspace whose only findings are structural warnings, such as missing scenario coverage
- WHEN `task-validation` runs
- THEN the readiness has `ready` true and lists the warnings

### scenario.validation.unloadable — Specs that cannot be loaded

- GIVEN a workspace whose Specs cannot be loaded
- WHEN `task-validation` runs
- THEN the run begins, and the result has status `blocked` and a readiness with `ready` false
- AND its `load` finding names the file and the loader's error, in the readiness and as the cause of the result's error
- AND no configured check is run

### scenario.validation.shared-file — A shared file runs every binder's checks

- GIVEN a changed file bound by `module.spec` and `module.views`
- WHEN `task-validation` runs
- THEN the configured checks of both Modules are run

### scenario.validation.submodule-reference — A vendored reference is accounted for

- GIVEN a workspace that adds two submodules, one of which a Module includes a directory of as `external`
- WHEN `task-validation` runs
- THEN the included submodule's gitlink is no blocking finding
- BUT the other submodule's gitlink is reported as `unbound`

### scenario.validation.submodule-content — Only a submodule's commit is measured

- GIVEN a workspace with a submodule
- WHEN a file inside the submodule's own worktree changes
- THEN the submodule is no changed path and the workspace has no uncommitted change
- BUT when the submodule is moved to another commit, it is a changed path and an uncommitted change

### scenario.validation.confirmation — A filled pending entry becomes a confirmation

- GIVEN a realization entry marked pending whose file an `implement` run created
- WHEN `task-validation` runs
- THEN the entry is listed in `confirmations` with its declaring document and that document's digest
- AND it is not a blocking finding

## Failures

### scenario.validation.inputs-changed — The worktree changes during the run

- GIVEN a `task-validation` run whose checks are running
- WHEN a file of the workspace changes before the run ends
- THEN the result has status `failed` with `inputs_changed`
- AND no readiness is issued

### scenario.validation.wrong-branch — The workspace is not on its bound branch

- GIVEN a workspace whose head is detached or on another branch than the one its binding names
- WHEN `task-validation` runs
- THEN the result has status `failed`
- AND no check is run

### scenario.validation.unbound — Readiness needs a bound workspace

- GIVEN a worktree without a [workspace binding](../../../glossary.json#concept.workspace-binding), such as the primary worktree
- WHEN `concorde task-validation` is run there
- THEN no step runs and the result is `failed`, with `workspace` and `output` null and a `refused` link whose cause is `binding_required`, reason `scope`
- AND the result is saved in that worktree's own [run store](../../../glossary.json#concept.run-store)

### scenario.validation.sandbox-unavailable — Checks cannot be bounded

- GIVEN a host where the [read-only check boundary](../../../glossary.json#concept.read-only-check-boundary) cannot be established
- WHEN `task-validation` reaches its checks
- THEN the result has status `failed`
- AND no check runs outside the boundary

## Confirmation for Delivery

### scenario.validation.confirm — Confirmations are applied exactly

- GIVEN a ready readiness with one confirmation whose declaring document is unchanged
- WHEN Delivery asks Validation to apply the confirmations
- THEN the pending marker of exactly that entry is cleared in one [file transaction](../../../glossary.json#concept.file-transaction)
- AND the Specs validate without a structural error

### scenario.validation.confirm-refused — A changed document stops confirmation

- GIVEN a confirmation whose declaring document no longer has the recorded digest, or whose clearing would leave a structural error
- WHEN Delivery asks Validation to apply the confirmations
- THEN the application is refused
- AND every Spec document is left as it was
