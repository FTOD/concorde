# Validation requirements

The Module-wide obligations of [Validation](module.md). The readiness and the input measurement are
defined in the [contracts](contracts.md). The [scenarios](scenarios.md) show the obligations at work.

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

When the input digest measured at the end of the run differs from the one measured at its start,
Validation SHALL NOT issue a readiness.

### req.validation.workspace — The bound workspace is validated

Validation SHALL validate the Specs and run the checks of the bound workspace the run works on,
never of another worktree.

### req.validation.bound-branch — Readiness is decided on the bound branch

Validation SHALL decide a readiness only when the workspace's head is on the branch its binding
names.

## Coverage of the change

### req.validation.changed-modules — Checks cover every changed Module

When a `task-validation` run reaches its checks, it SHALL run the
[configured checks](../../glossary.json#concept.configured-check) of all these Modules:

- Every [Module](../../glossary.json#concept.module) that binds a changed path or owns a changed
  [Spec](../../glossary.json#concept.spec) document.
- Every Module the run works on.
- Every Module that uses one of those, directly or through further uses.

### req.validation.unbound-paths — Every change is accounted for

Validation SHALL report as blocking every changed path that meets all these conditions:

- It still exists.
- It is not a Spec document member.
- It is not the project glossary.
- It is not a control record under `.concorde/`.
- It is not generated or build output.
- It is not external material.
- No Module binds it.

External material is what a Module includes as `external`. When a Module includes a submodule or a
path inside it, the submodule's gitlink counts as external material. Bumping a vendored reference
therefore needs no binding of its own.

## Effects

### req.validation.read-only — A task-validation run changes nothing in the workspace

Outside its own [trace node](../../glossary.json#concept.trace-node) and the locks directory its
binding names, a `task-validation` run SHALL NOT change any file, index entry, branch or commit of
the workspace.

## The workflow handoff

### req.validation.step-output — A workspace that is not ready stops a workflow

For every task-validation run that decided a readiness, the output SHALL carry these under the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output):

- Its readiness's `ready` as `data.ready`.
- When the workspace is not ready, a `blocking` item naming the blocking findings.

A run that found the workspace not ready ends `blocked`. This stops a workflow already. The
`blocking` item says the same in the convention. A workflow reads only the convention of a run's
output. The decision therefore never depends on a run's status alone
([contracts](contracts.md#readiness)).

