# Delivery requirements

The Module-wide obligations of [Delivery](module.md). The commit, the
[evidence bundle](../../../glossary.json#concept.evidence-bundle) and the output are defined in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations at work.

## Preconditions

### req.delivery.own-readiness — Delivery validates the whole workspace itself

Delivery SHALL commit only when a readiness it decided in the same run with Validation's steps,
over every commit on the bound branch since the base commit and every uncommitted change, is ready.

### req.delivery.committed-steps — Committed steps are deliverable

Delivery SHALL treat a workspace without uncommitted changes whose branch head is past the base
commit and is no [delivery commit](../../../glossary.json#concept.delivery-commit) of the workspace
as new work to validate, never as nothing to deliver.

Such a workspace is still delivered only under the other requirements, first
[its own readiness](#req.delivery.own-readiness).

### req.delivery.scenarios-verified — A code change ships only with tests for its scenarios

Delivery SHALL refuse a workspace that changed code while a scenario it added or changed since its
base commit has no test declaring that it verifies it, except in a run given `--adoption`.

Changed code is a changed path outside `specs/` and `.concorde/` that a
[Module](../../../glossary.json#concept.module)'s realization binds, tests included; a test declares
what it verifies by its
[verification declaration](../../../glossary.json#concept.verification-declaration).

### req.delivery.blocked-reason — A refusal says its own reason

A delivery run that ends `blocked` SHALL explain in its error link the reason of its own code: for
`nothing_to_deliver`, that the head is the base commit and no change waits; for `not_ready`, every
blocking finding; for `unverified_scenarios`, every unverified scenario with its document.

### req.delivery.blocked-inert — A blocked delivery changes nothing

A delivery run that ends `blocked` SHALL leave the workspace, its index and its branch unchanged.

## The commit

### req.delivery.exact-content — The commit holds what was validated

A delivery commit SHALL contain exactly the uncommitted changes the readiness examined, the metadata
changed by the applied confirmations and the evidence bundle.

Its parent is fixed by [req.delivery.bound-branch](#req.delivery.bound-branch).

### req.delivery.bound-branch — Commits go on the bound branch

Delivery SHALL create its commit only on the branch the
[workspace binding](../../../glossary.json#concept.workspace-binding) names, with the validated head
as its only parent.

### req.delivery.evidence — Every delivery commit carries its bundle

Every delivery commit SHALL contain one evidence bundle that satisfies the evidence bundle contract.

### req.delivery.history-kept — History is never rewritten

Delivery SHALL NOT amend, rebase, merge or push any commit, nor move its branch to a commit other
than the delivery commit it creates.

Restoring the index while undoing an uncommitted delivery, as
[req.delivery.atomic](#req.delivery.atomic) requires, changes no commit.

### req.delivery.atomic — A failed commit leaves the validated workspace

When writing the bundle, staging or the commit fails, Delivery SHALL restore the workspace and its
index to the state the readiness examined.

## Records

### req.delivery.commit-is-record — The commit is the only record

Delivery SHALL record a delivery only in its delivery commit, writing no
[task record](../../../glossary.json#concept.task-record) and no other record of it.

Whoever needs to know whether and how often a workspace was delivered reads the delivery commits on
its branch, as the [contract](contracts.md#delivery-commit) defines them.

### req.delivery.already-delivered — A delivered head is reported, not repeated

Delivery SHALL NOT create a commit when the branch head already is a delivery commit of the
workspace and no uncommitted change waits.

Such a run reports the existing commit instead, as
[scenario.delivery.recover](scenarios.md#scenario.delivery.recover) shows.
