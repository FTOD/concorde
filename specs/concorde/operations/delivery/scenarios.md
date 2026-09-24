# Delivery scenarios

Concrete situations that show the [requirements](requirements.md) of [Delivery](module.md). The
commit, bundle and output are defined in the [contracts](contracts.md).

## Delivering

### scenario.delivery.deliver — Deliver a task with uncommitted work

- GIVEN an active task whose worktree has uncommitted changes that pass validation
- WHEN the main agent runs `concorde run delivery --task severity`
- THEN Delivery decides the readiness itself and records its own run as the readiness run
- AND a delivery commit is created on `concorde/severity` with the validated head as its parent
- AND it contains every uncommitted change and the evidence bundle `.concorde/evidence/severity/1.json`
- AND the task record lists the delivery and the task is delivered
- AND the result has status `ok` with the commit as output and the worktree is clean

### scenario.delivery.committed — Deliver a task whose steps are committed

- GIVEN an active task whose verified steps are committed on its branch and whose worktree is clean
- AND no `validate` run since
- WHEN the main agent runs `delivery`
- THEN Delivery validates every change since the base commit
- AND the delivery commit, on top of the last step, adds only the evidence bundle
- AND the task is delivered

### scenario.delivery.confirmations — Pending markers are cleared in the commit

- GIVEN a task whose readiness lists a confirmation for a filled pending entry
- WHEN the task is delivered
- THEN the delivery commit contains the declaring metadata with that entry no longer pending
- AND the output and the bundle list the confirmed entry

### scenario.delivery.second — Deliver again after further work

- GIVEN a task delivered once, then returned to active by another `implement` run and validated again
- WHEN the main agent runs `delivery`
- THEN a second delivery commit is created on top of the first with bundle number 2
- AND the bundle lists only the runs that started after the first delivery

## Refusing

### scenario.delivery.not-ready — Refuse a task that is not ready

- GIVEN a task with a committed file that no Module binds
- WHEN the main agent runs `delivery`
- THEN the result has status `blocked` with `not_ready`, and Validation's `not_deliverable` link
  names the file as a cause
- AND no commit is created, nothing in the worktree changes and no delivery is recorded

### scenario.delivery.nothing — Nothing to deliver

- GIVEN a clean worktree whose head is the task's base commit, or its previous delivery commit
- WHEN the main agent runs `delivery`
- THEN the result has status `blocked` with `nothing_to_deliver`
- AND the error names which commit the head equals and explains that there is no new work

## Failures

### scenario.delivery.commit-refused — Git refuses the commit

- GIVEN a task that is ready and a commit hook that rejects the commit
- WHEN the task is delivered
- THEN the result has status `failed` with the hook's output as host evidence
- AND the confirmed metadata is restored, the bundle removed and the index reset
- AND a fresh measurement yields the readiness's input digest again

### scenario.delivery.recover — Record a delivery the record missed

- GIVEN a delivery commit at the head of the task branch that the task record does not list
- WHEN the main agent runs `delivery`
- THEN no new commit is created
- AND the existing commit is recorded as a delivery and the output has `recovered` true
