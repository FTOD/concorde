# Validation design

This topic explains in more detail why [Validation](module.md) is built the way its entry
summarizes: how evidence is bound to bytes, why Validation computes edited Modules itself, and why
failures and unmet gates are treated differently. The precise flow and gate table are in
[Validation interface](records.md).

## Evidence bound to bytes

A check result carries the digest of what the check measured, computed by Check execution.
Validation adds the digest of the validated Spec sources and the Spec and implementation revisions
of every affected Module: a Module's Spec revision is the identity of its resolved Spec context, and
its implementation revision is a digest of its realization entries and the bytes of every file they
bind. Validation snapshots the candidate's deliverable tree before the checks and compares it, and
the affected revisions, afterwards; a difference means someone changed the candidate during
validation, and the result is refused rather than recorded. Delivery later compares the validated
tree with the candidate's actual tree for the same reason, and the completion check it reruns
counts a check result only while its measured-input digest still matches the current files.

Pending realization entries are confirmed before anything is checked. Once a file declared
`pending` exists, the Protocol requires the marker to go, so Validation removes such entries from
their `pending` lists, changing only metadata members, and the confirmation becomes part of the
validated tree.

## Edited Modules

Which Modules a change edits is a question about one change's candidate, not about the Spec model,
so Validation computes it itself: from the paths that differ between the change's base commit and
the candidate's deliverable tree, it takes the owner of every changed Spec document member and every
Module that binds a changed file. Spec tooling supplies only the indexes of which Module owns a
document and which Modules bind a file. Local control records and the Host's worktree guidance are
not part of the deliverable tree and edit no Module. Scoping the widening to the Module the change
is about keeps the validation of one component's work to that component's own affected Modules,
while validating the change's own Module covers everything it edits, so delivering the one
candidate lands a multi-Module change atomically.

## Readiness is not transitive trust

When the change recorded component work, the completion check runs again for each component with
its own task, and a component whose Spec or implementation changed since it completed stops
readiness. The Module the change is about also records the revisions of every edited Module, so an
edit to any of them after validation makes the evidence stale.

## Failures and unmet gates

A failed check or an invalid Spec is a fact about the candidate's current bytes, recorded as
`blocked` so that the user session and Delivery see it. A missing review or an unfinished task is a
gate still to be met, so it only stops the request and leaves the change in phase `validate` with
its earlier ready state withdrawn.

## No candidate of its own

Readiness is a property of work. Creating a candidate to validate would record the readiness of an
unchanged base commit and leave an orphan worktree, so a request without an existing change is
refused.
