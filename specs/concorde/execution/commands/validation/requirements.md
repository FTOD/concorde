# Validation requirements

The Module-wide obligations of [Validation](module.md). The readiness and the input measurement are
defined in the [contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at
work.

## Readiness

### req.validation.ready-definition — Ready means nothing blocks

A readiness SHALL be ready exactly when it lists no blocking finding.

### req.validation.all-findings — One run reports every blocking finding

A `task-validation` run SHALL report every blocking finding that its steps establish rather than
stopping at the first.

### req.validation.bound-inputs — Readiness is bound to its inputs

A readiness SHALL record the input measurement of exactly the workspace state its structural
validation and checks examined.

### req.validation.stable-inputs — No readiness for moving inputs

Validation SHALL NOT issue a readiness when the input digest measured at the end of the run differs
from the one measured at its start.

### req.validation.workspace — The bound workspace is validated

Validation SHALL validate the Specs and run the checks of the bound workspace the run works on,
never of another worktree.

### req.validation.bound-branch — Readiness is decided on the bound branch

Validation SHALL decide a readiness only when the workspace's head is on the branch its binding
names.

## Coverage of the change

### req.validation.changed-modules — Checks cover every changed Module

A `task-validation` run SHALL run the
[configured checks](../../../glossary.json#concept.configured-check) of every
[Module](../../../glossary.json#concept.module) that binds a changed path or owns a changed
[Spec](../../../glossary.json#concept.spec) document, of every Module the run works on, and of every
Module that uses one of those, directly or through further uses.

### req.validation.unbound-paths — Every change is accounted for

Validation SHALL report as blocking every changed path that still exists, is not a Spec document
member, a control record under `.concorde/`, generated or build output or external material, and is
bound by no Module.

External material is what a Module includes as `external`. A submodule's gitlink counts as external
material when a Module includes the submodule or a path inside it, so bumping a vendored reference
needs no binding of its own.

### req.validation.confirmations — Filled pending entries are confirmations

Validation SHALL report a pending realization entry whose file exists as a confirmation, not as a
blocking finding.

## Effects

### req.validation.read-only — A task-validation run changes nothing in the workspace

A `task-validation` run SHALL NOT change any file, index entry, branch or commit of the workspace.

### req.validation.confirm-exact — Confirmation clears only the listed markers

Applying confirmations SHALL clear the pending markers of exactly the listed entries, and only when
each declaring document still has the digest the readiness recorded.

### req.validation.confirm-valid — Confirmation keeps the Specs valid

Applying confirmations SHALL leave the Specs unchanged when the confirmed Specs have a structural
error.
