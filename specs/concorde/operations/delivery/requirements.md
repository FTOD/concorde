# Delivery requirements

The Module-wide obligations of [Delivery](module.md). The commit, the evidence bundle and the
output are defined in the [contracts](contracts.md); the [scenarios](scenarios.md) show the
obligations at work.

## Preconditions

### req.delivery.own-readiness — Delivery validates the whole task itself

Delivery SHALL commit only when a readiness it decided in the same run with Validation's steps,
over every commit on the task branch since the base commit and every uncommitted change, is ready.

### req.delivery.committed-steps — Committed steps are deliverable

Delivery SHALL accept a task worktree without uncommitted changes when the task branch has a
commit since the previous delivery, or since the base commit when the task has no delivery.

### req.delivery.scenarios-verified — A code change ships only with tests for its scenarios

Delivery SHALL refuse a task that changed implementation files while a scenario it added or changed since its base commit has no test declaring that it verifies it, except a task of the brownfield workflow.

### req.delivery.blocked-reason — A refusal says its own reason

A delivery run that ends `blocked` SHALL explain in its error link the reason of its own code: for
`nothing_to_deliver`, which commit the head equals and that no change waits; for `not_ready`,
every blocking finding.

### req.delivery.blocked-inert — A blocked delivery changes nothing

A delivery run that ends `blocked` SHALL leave the task worktree, its index, its branch and the
deliveries of the task record unchanged.

## The commit

### req.delivery.exact-content — The commit holds what was validated

A delivery commit SHALL contain exactly the uncommitted changes the readiness examined, the metadata
changed by the applied confirmations and the evidence bundle; the commits it is created on are the
ones the readiness examined.

### req.delivery.task-branch — Commits go on the task branch

Delivery SHALL create its commit only on the task's own branch, with the validated head as its only
parent.

### req.delivery.evidence — Every delivery commit carries its bundle

Every delivery commit SHALL contain one evidence bundle that satisfies the evidence bundle contract.

### req.delivery.history-kept — History is never rewritten

Delivery SHALL NOT amend, rebase, reset, merge or push any commit.

### req.delivery.atomic — A failed commit leaves the validated worktree

When the commit fails, Delivery SHALL restore the task worktree and its index to the state the
readiness examined.

## Records

### req.delivery.recorded — Every delivery is recorded

Delivery SHALL record every delivery commit it creates in the task record.

### req.delivery.recovery — A missed record is recovered, not repeated

A delivery run that finds at the branch head a delivery commit of the task that the task record
lacks SHALL record that commit instead of creating another.
