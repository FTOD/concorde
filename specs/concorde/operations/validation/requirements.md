# Validation requirements

The Module-wide obligations of [Validation](module.md). The readiness and the input measurement are
defined in the [contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at
work.

## Readiness

### req.validation.ready-definition — Ready means nothing blocks

A readiness SHALL be ready exactly when it lists no blocking finding.

### req.validation.all-findings — One run reports every blocking finding

A `validate` run SHALL report every blocking finding that its steps establish rather than stopping
at the first.

### req.validation.bound-inputs — Readiness is bound to its inputs

A readiness SHALL record the input measurement of exactly the worktree state its structural
validation and checks examined.

### req.validation.stable-inputs — No readiness for moving inputs

Validation SHALL NOT issue a readiness when the input digest measured at the end of the run differs
from the one measured at its start.

### req.validation.task-worktree — The task worktree is validated

Validation SHALL validate the Specs and run the checks of the task's worktree, never of the primary
worktree.

## Coverage of the change

### req.validation.changed-modules — Checks cover every changed Module

A `validate` run SHALL run the configured checks of every Module that binds a changed path or owns
a changed Spec document, and of every Module the run is bound to.

### req.validation.unbound-paths — Every change is accounted for

Validation SHALL report as blocking every changed path that still exists, is not a Spec document
member, a control record under `.concorde/`, generated or build output or external material, and is
bound by no Module.

### req.validation.confirmations — Filled pending entries are confirmations

Validation SHALL report a pending realization entry whose file exists as a confirmation, not as a
blocking finding.

## Effects

### req.validation.read-only — A validate run changes nothing in the task

A `validate` run SHALL NOT change any file, index entry, branch or commit of the task worktree.

### req.validation.confirm-exact — Confirmation clears only the listed markers

Applying confirmations SHALL clear the pending markers of exactly the listed entries, and only when
each declaring document still has the digest the readiness recorded.

### req.validation.confirm-valid — Confirmation keeps the Specs valid

Applying confirmations SHALL leave the Specs unchanged when the confirmed Specs have a structural
error.
