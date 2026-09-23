# Validation scenarios

Concrete situations that show the [requirements](requirements.md) of [Validation](module.md). The
readiness is defined in the [contracts](contracts.md).

## Deciding readiness

### scenario.validation.ready — A complete task is ready

- GIVEN a task worktree whose changes are bound by `module.issues`, whose Specs have no structural error and whose checks pass
- WHEN the main agent runs `concorde run validate --task severity`
- THEN the result has status `ok` and its output is a readiness with `ready` true
- AND the readiness records the input measurement and one passed check result per configured check of `module.issues`
- AND nothing in the task worktree changed

### scenario.validation.not-ready — Every blocker is reported in one run

- GIVEN a task worktree with a broken Spec link, a new file bound by no Module and a failing check of a changed Module
- WHEN `validate` runs
- THEN the result has status `ok` and the readiness has `ready` false
- AND `blocking` holds a structural finding, an unbound finding and a check finding

### scenario.validation.warnings — Warnings do not block

- GIVEN a task worktree whose only findings are structural warnings, such as missing scenario coverage
- WHEN `validate` runs
- THEN the readiness has `ready` true and lists the warnings

### scenario.validation.unloadable — Specs that cannot be loaded

- GIVEN a task worktree whose Specs cannot be loaded
- WHEN `validate` runs
- THEN the readiness has `ready` false with a `load` finding
- AND no configured check is run

### scenario.validation.shared-file — A shared file runs every binder's checks

- GIVEN a changed file bound by `module.spec` and `module.views`
- WHEN `validate` runs
- THEN the configured checks of both Modules are run

### scenario.validation.confirmation — A filled pending entry becomes a confirmation

- GIVEN a realization entry marked pending whose file an `implement` run created
- WHEN `validate` runs
- THEN the entry is listed in `confirmations` with its declaring document and that document's digest
- AND it is not a blocking finding

## Failures

### scenario.validation.inputs-changed — The worktree changes during the run

- GIVEN a `validate` run whose checks are running
- WHEN a file of the task worktree changes before the run ends
- THEN the result has status `failed` with `inputs_changed`
- AND no readiness is issued

### scenario.validation.wrong-branch — The worktree is not on the task branch

- GIVEN a task worktree whose head is detached or on another branch
- WHEN `validate` runs
- THEN the result has status `failed`
- AND no check is run

### scenario.validation.sandbox-unavailable — Checks cannot be bounded

- GIVEN a host where the read-only check boundary cannot be established
- WHEN `validate` reaches its checks
- THEN the result has status `failed`
- AND no check runs outside the boundary

## Confirmation for Delivery

### scenario.validation.confirm — Confirmations are applied exactly

- GIVEN a ready readiness with one confirmation whose declaring document is unchanged
- WHEN Delivery asks Validation to apply the confirmations
- THEN the pending marker of exactly that entry is cleared in one file transaction
- AND the Specs validate without a structural error

### scenario.validation.confirm-refused — A changed document stops confirmation

- GIVEN a confirmation whose declaring document no longer has the recorded digest, or whose clearing would leave a structural error
- WHEN Delivery asks Validation to apply the confirmations
- THEN the application is refused
- AND every Spec document is left as it was
