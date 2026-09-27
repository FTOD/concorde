# Delivery requirements

The Module-wide obligations of [Delivery](module.md). The commit, the evidence bundle and the
output are defined in the [contracts](contracts.md); the [scenarios](scenarios.md) show the
obligations at work.

## Preconditions

### req.delivery.own-readiness — Delivery validates the whole workspace itself

Delivery SHALL commit only when a readiness it decided in the same run with Validation's steps,
over every commit on the bound branch since the base commit and every uncommitted change, is ready.

### req.delivery.committed-steps — Committed steps are deliverable

Delivery SHALL accept a workspace without uncommitted changes when its branch head is past the base
commit and is no delivery commit of the workspace.

### req.delivery.scenarios-verified — A code change ships only with tests for its scenarios

Delivery SHALL refuse a workspace that changed implementation files while a scenario it added or changed since its base commit has no test declaring that it verifies it, except in a run given `--adoption`.

### req.delivery.blocked-reason — A refusal says its own reason

A delivery run that ends `blocked` SHALL explain in its error link the reason of its own code: for
`nothing_to_deliver`, that the head is the base commit and no change waits; for `not_ready`, every
blocking finding; for `unverified_scenarios`, every unverified scenario with its document.

### req.delivery.blocked-inert — A blocked delivery changes nothing

A delivery run that ends `blocked` SHALL leave the workspace, its index and its branch unchanged.

## The commit

### req.delivery.exact-content — The commit holds what was validated

A delivery commit SHALL contain exactly the uncommitted changes the readiness examined, the metadata
changed by the applied confirmations and the evidence bundle; the commits it is created on are the
ones the readiness examined.

### req.delivery.bound-branch — Commits go on the bound branch

Delivery SHALL create its commit only on the branch the workspace binding names, with the validated
head as its only parent.

### req.delivery.evidence — Every delivery commit carries its bundle

Every delivery commit SHALL contain one evidence bundle that satisfies the evidence bundle contract.

### req.delivery.history-kept — History is never rewritten

Delivery SHALL NOT amend, rebase, reset, merge or push any commit.

### req.delivery.atomic — A failed commit leaves the validated workspace

When the commit fails, Delivery SHALL restore the workspace and its index to the state the readiness
examined.

## Records

### req.delivery.commit-is-record — The commit is the only record

Delivery SHALL record a delivery only in its delivery commit, writing no task record and no other
record of it.

Whoever needs to know whether and how often a workspace was delivered reads the delivery commits on
its branch, as the [contract](contracts.md#delivery-commit) defines them.

### req.delivery.already-delivered — A delivered head is reported, not repeated

A delivery run that finds the branch head already a delivery commit of the workspace with no
uncommitted change SHALL report that commit as its output with `recovered` true and create no
commit.
