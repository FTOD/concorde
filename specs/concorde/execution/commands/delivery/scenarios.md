# Delivery scenarios

Concrete situations that show the [requirements](requirements.md) of [Delivery](module.md). The
commit, bundle and output are defined in the [contracts](contracts.md).

## Delivering

### scenario.delivery.deliver — Deliver a workspace with uncommitted work

- GIVEN a task worktree bound to the workspace `severity` on the branch `concorde/severity`, with uncommitted changes that pass validation
- WHEN the task level runs `concorde delivery` there
- THEN Delivery decides the readiness itself and names its own run as the readiness run
- AND a delivery commit `concorde: deliver severity` with the trailers `Concorde-Workspace`, `Concorde-Evidence` and `Concorde-Readiness` is created on `concorde/severity` with the validated head as its parent
- AND it contains every uncommitted change and the evidence bundle `.concorde/evidence/severity/1.json`
- AND the result has kind `command`, no worker and status `ok`, with the commit as output, and the worktree is clean
- BUT no task record changes: the task level reads the delivery back from the commit

### scenario.delivery.unverified-scenarios — An untested new scenario stops a code change

- GIVEN a workspace that changes `src/a/calc.py` and adds `scenario.a.sum` to Module A's Specs, while the untouched `scenario.a.answer` has no test either
- WHEN delivery runs
- THEN delivery is `blocked` with `unverified_scenarios` naming `scenario.a.sum` and its document, and not `scenario.a.answer`
- AND once a test in a file Module A binds declares that it verifies `scenario.a.sum`, delivery commits the workspace
- BUT a workspace that adds the scenario without changing code is delivered without a test

### scenario.delivery.adoption — An adoption delivery needs no scenario test

- GIVEN a workspace that changes `src/a/calc.py` and adds `scenario.a.sum` without a test
- WHEN `concorde delivery --adoption` runs
- THEN the workspace is delivered, `ok`
- AND its host evidence records the scenario-test rule as `exempt`

### scenario.delivery.sandbox-masks — Deliver from a sandbox that masks paths

- GIVEN a workspace with an uncommitted change, seen from inside a sandbox that hides `.bashrc` behind a `/dev/null` mount
- WHEN delivery runs inside that sandbox
- THEN the readiness's changed paths do not include `.bashrc`
- AND the delivery commit contains the change and the bundle but not `.bashrc`

### scenario.delivery.committed — Deliver a workspace whose steps are committed

- GIVEN a workspace whose verified steps are committed on its branch and whose worktree is clean
- AND no `task-validation` run since
- WHEN delivery runs
- THEN Delivery validates every change since the base commit
- AND the delivery commit, on top of the last step, adds only the evidence bundle

### scenario.delivery.confirmations — Pending markers are cleared in the commit

- GIVEN a workspace whose readiness lists a confirmation for a filled pending entry
- WHEN the workspace is delivered
- THEN the delivery commit contains the declaring metadata with that entry no longer pending
- AND the output and the bundle list the confirmed entry

### scenario.delivery.second — Deliver again after further work

- GIVEN a workspace delivered once, then changed further and validated again
- WHEN delivery runs
- THEN a second delivery commit is created on top of the first with bundle number 2
- AND the bundle lists only the runs of the workspace that started after the first delivery run
- AND the branch then holds both delivery commits, oldest first

## Refusing

### scenario.delivery.not-ready — Refuse a workspace that is not ready

- GIVEN a workspace with a committed file that no Module binds
- WHEN delivery runs
- THEN the result has status `blocked` with `not_ready`, and Validation's `not_deliverable` link
  names the file as a cause
- AND no commit is created and nothing in the workspace changes

### scenario.delivery.nothing — Nothing new to deliver

- GIVEN a clean workspace whose head is its base commit
- WHEN delivery runs
- THEN the result has status `blocked` with `nothing_to_deliver`
- AND the error names the base commit and explains that there is no new work
- BUT when the clean head is the workspace's latest delivery commit, delivery ends `ok`, reports that commit with `recovered` true and commits nothing

### scenario.delivery.unbound — Delivery needs a bound workspace

- GIVEN a worktree without a workspace binding, such as the primary worktree, with a changed file
- WHEN `concorde delivery` is run there
- THEN the result is `failed` with `workspace` null and a `command` link `refused` whose cause is `binding_required`
- AND nothing is committed

## Failures

### scenario.delivery.commit-refused — Git refuses the commit

- GIVEN a workspace that is ready and a commit hook that rejects the commit
- WHEN the workspace is delivered
- THEN the result has status `failed` with the hook's output as host evidence
- AND the confirmed metadata is restored, the bundle removed and the index reset
- AND a fresh measurement yields the readiness's input digest again
- AND the branch holds no delivery commit

### scenario.delivery.recover — A delivery interrupted after its commit needs no repair

- GIVEN a delivery run that created its delivery commit and ended without saving its result
- WHEN delivery runs again
- THEN no new commit is created
- AND the output is the existing commit with `recovered` true and no confirmations, and the worktree is clean
- AND the branch still holds exactly that one delivery commit, which alone records the delivery
