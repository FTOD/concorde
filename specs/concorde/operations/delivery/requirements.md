# Delivery requirements

The Module-wide obligations of [Delivery](module.md). The commit, the evidence bundle and the
output are defined in the [contracts](contracts.md); the [scenarios](scenarios.md) show the
obligations at work.

## Preconditions

### req.delivery.current-readiness — Only a current, ready readiness is delivered

Delivery SHALL commit only when the task's latest `validate` run produced a ready readiness whose
input digest equals a fresh measurement of the task worktree.

### req.delivery.blocked-inert — A blocked delivery changes nothing

A delivery run that ends `blocked` SHALL leave the task worktree, its index, its branch and the task
record unchanged.

## The commit

### req.delivery.exact-content — The commit holds what was validated

A delivery commit SHALL contain exactly the uncommitted changes the readiness examined, the metadata
changed by the applied confirmations and the evidence bundle.

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
