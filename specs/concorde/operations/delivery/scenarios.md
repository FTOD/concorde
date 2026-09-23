# Delivery scenarios

Concrete situations that show the [requirements](requirements.md) of [Delivery](module.md). The
commit, bundle and output are defined in the [contracts](contracts.md).

## Delivering

### scenario.delivery.deliver — Deliver a validated task

- GIVEN an active task whose latest `validate` run produced a ready readiness
- AND the task worktree has not changed since
- WHEN the main agent runs `concorde run delivery --task severity`
- THEN a delivery commit is created on `concorde/severity` with the validated head as its parent
- AND it contains every uncommitted change and the evidence bundle `.concorde/evidence/severity/1.json`
- AND the task record lists the delivery and the task is delivered
- AND the result has status `ok` with the commit as output and the worktree is clean

### scenario.delivery.confirmations — Pending markers are cleared in the commit

- GIVEN a ready readiness that lists a confirmation for a filled pending entry
- WHEN the task is delivered
- THEN the delivery commit contains the declaring metadata with that entry no longer pending
- AND the output and the bundle list the confirmed entry

### scenario.delivery.second — Deliver again after further work

- GIVEN a task delivered once, then returned to active by another `implement` run and validated again
- WHEN the main agent runs `delivery`
- THEN a second delivery commit is created on top of the first with bundle number 2
- AND the bundle lists only the runs that started after the first delivery

## Refusing

### scenario.delivery.stale — Refuse a stale readiness

- GIVEN a ready readiness
- WHEN a file of the task worktree changes and the main agent runs `delivery`
- THEN the result has status `blocked` with `stale_readiness`
- AND no commit is created and nothing in the worktree or the task record changes

### scenario.delivery.not-ready — Refuse a missing or negative readiness

- GIVEN a task without a `validate` run, or whose latest readiness is not ready
- WHEN the main agent runs `delivery`
- THEN the result has status `blocked` with `no_readiness` or `not_ready`
- AND nothing changes

### scenario.delivery.nothing — Nothing to deliver

- GIVEN a current ready readiness and a worktree without uncommitted changes
- WHEN the main agent runs `delivery`
- THEN the result has status `blocked` with `nothing_to_deliver`

## Failures

### scenario.delivery.commit-refused — Git refuses the commit

- GIVEN a current ready readiness and a commit hook that rejects the commit
- WHEN the task is delivered
- THEN the result has status `failed` with the hook's output as host evidence
- AND the confirmed metadata is restored, the bundle removed and the index reset
- AND a fresh measurement yields the readiness's input digest again

### scenario.delivery.recover — Record a delivery the record missed

- GIVEN a delivery commit at the head of the task branch that the task record does not list
- WHEN the main agent runs `delivery`
- THEN no new commit is created
- AND the existing commit is recorded as a delivery and the output has `recovered` true
