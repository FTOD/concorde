# Delivery scenarios

Concrete situations that show the [requirements](requirements.md) of [Delivery](module.md). The
commit and output are defined in the [contracts](contracts.md).

## Delivering

### scenario.delivery.deliver — Deliver a workspace with uncommitted work

- GIVEN a task worktree bound to the workspace `severity` on the branch `concorde/severity`, with uncommitted changes that pass validation
- WHEN the task level runs `concorde delivery` there
- THEN Delivery decides the readiness itself and names its own run as the readiness run
- AND a [delivery commit](../../glossary.json#concept.delivery-commit) `concorde: deliver severity`, with the goal as body and no trailer, is created on `concorde/severity` with the validated head as its parent
- AND it contains every uncommitted change and nothing else
- AND the result has kind `command`, no worker and status `ok`, with the commit as output, and the worktree is clean
- BUT no [task record](../../glossary.json#concept.task-record) changes: the task level reads the delivery back from the commit

### scenario.delivery.unverified-scenarios — An untested new scenario stops a code change

- GIVEN a workspace that changes `src/a/calc.py` and adds `scenario.a.sum` to [Module](../../glossary.json#concept.module) A's [Specs](../../glossary.json#concept.spec), while the untouched `scenario.a.answer` has no test either
- WHEN delivery runs
- THEN delivery is `blocked` with `unverified_scenarios` naming `scenario.a.sum` and its document, and not `scenario.a.answer`

### scenario.delivery.verified-scenarios — A verifying test lets the code change through

- GIVEN the workspace of the previous scenario
- AND a test in a file Module A binds declaring that it verifies `scenario.a.sum`
- WHEN delivery runs
- THEN the workspace is delivered, `ok`

### scenario.delivery.spec-only-scenarios — A scenario added without code needs no test

- GIVEN a workspace that adds `scenario.a.sum` to Module A's Specs without changing code
- WHEN delivery runs
- THEN the workspace is delivered, `ok`, without a test

### scenario.delivery.unrealized-scenarios — An untested scenario of a Module without files stops a code change

- GIVEN a workspace that changes `src/a/calc.py` and adds `scenario.b.more` to the Specs of Module B, which binds no file
- WHEN delivery runs
- THEN delivery is `blocked` with `unverified_scenarios` naming `scenario.b.more` and its document
- BUT once a test in a file Module A binds declares that it verifies `scenario.b.more`, the workspace is delivered, `ok`

### scenario.delivery.adoption — An adoption delivery needs no scenario test

- GIVEN a workspace that changes `src/a/calc.py` and adds `scenario.a.sum` without a test
- WHEN `concorde delivery --adoption` runs
- THEN the workspace is delivered, `ok`
- AND its host evidence records the scenario-test rule as `exempt`

### scenario.delivery.sandbox-masks — Deliver from a sandbox that masks paths

- GIVEN a workspace with an uncommitted change, seen from inside a sandbox that hides `.bashrc` behind a `/dev/null` mount
- WHEN delivery runs inside that sandbox
- THEN the readiness's changed paths do not include `.bashrc`
- AND the delivery commit contains the change but not `.bashrc`

### scenario.delivery.committed — Deliver a workspace whose steps are committed

- GIVEN a workspace whose verified steps are committed on its branch and whose worktree is clean
- AND no `task-validation` run since
- WHEN delivery runs
- THEN Delivery validates every change since the base commit
- AND the delivery commit, on top of the last step, changes no file and marks the delivery by its subject

### scenario.delivery.second — Deliver again after further work

- GIVEN a workspace delivered once, then changed further and validated again
- WHEN delivery runs
- THEN a second delivery commit is created on top of the first, and the output gives it sequence 2
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

### scenario.delivery.redeliver — Delivering a delivered head again

- GIVEN a clean workspace whose head is its latest delivery commit
- WHEN delivery runs
- THEN Delivery validates the whole workspace again
- AND the result has status `ok` and reports that commit with `recovered` true
- AND nothing is committed
- AND the run's [trace node](../../glossary.json#concept.trace-node) references that commit with `found_commit`, not with `commit`

### scenario.delivery.unbound — Delivery needs a bound workspace

- GIVEN a worktree without a [workspace binding](../../glossary.json#concept.workspace-binding), such as the primary worktree, with a changed file
- WHEN `concorde delivery` is run there
- THEN the result is `failed` with `workspace` null and a `command` link `refused` whose cause is `binding_required`
- AND nothing is committed

## Failures

### scenario.delivery.commit-refused — Git refuses the commit

- GIVEN a workspace that is ready, with changes staged before the delivery, an intent-to-add path, a skip-worktree and an assume-unchanged flag, and a commit hook that rejects the commit
- WHEN the workspace is delivered
- THEN the result has status `failed` with the hook's output as host evidence
- AND the index is restored with the changes staged before, including a staged version the worktree changed since, the intent-to-add path and both flags
- AND a fresh measurement yields the readiness's input digest again
- AND the branch holds no delivery commit

### scenario.delivery.hook-changed-commit — A commit hook that changes the content is caught

- GIVEN a workspace that is ready, with a pre-commit hook that rewrites `src/a/calc.py` and stages it again
- WHEN the workspace is delivered
- THEN Git creates the delivery commit and the worktree is clean
- BUT the commit's tree is not the tree recorded after staging, so the result has status `failed` with `commit_unverified`, reason `decision`, naming `src/a/calc.py` as changed
- AND Delivery takes the commit off the branch: the head is again the validated head, and its error says so and names the commit
- AND the index and the worktree hold what the commit held, the hook's version of `src/a/calc.py` staged
- AND the branch holds no delivery commit, so a following `delivery` validates the workspace as it now is

### scenario.delivery.hook-changed-message — A commit message hook that rewrites the subject is caught

- GIVEN a workspace that is ready, with a commit-msg hook that prefixes the subject with a ticket, `[T-1] `
- WHEN the workspace is delivered
- THEN Git creates the commit with the subject `[T-1] concorde: deliver t1`
- BUT its subject is not the delivery subject, so the result has status `failed` with `commit_unverified`, naming the subject it carries and the one it should
- AND Delivery takes the commit off the branch: the head is again the validated head and the branch holds no delivery commit

### scenario.delivery.hook-edits-kept — A failing hook's worktree edits are kept and named

- GIVEN a workspace that is ready, with a pre-commit hook that rewrites `src/a/calc.py` in the worktree and then rejects the commit, as a formatter hook does
- WHEN the workspace is delivered
- THEN the result has status `failed` with `commit_failed`
- AND the index is restored as the readiness examined it
- BUT the worktree keeps the hook's version of `src/a/calc.py`, and the run's summary and error name `src/a/calc.py` as not as the readiness examined it
- AND the branch holds no delivery commit

### scenario.delivery.staged-unvalidated — Staging that changes validated content is refused

- GIVEN a workspace that is ready, with changes staged before the delivery, an intent-to-add path, a skip-worktree and an assume-unchanged flag
- AND a Git clean filter that succeeds while it rewrites the new file `src/a/extra.py`, with no smudge filter to reverse it
- WHEN the workspace is delivered
- THEN the result has status `failed` with `staged_unvalidated`, reason `decision`, naming `src/a/extra.py` and no other path
- AND the index is again exactly as before the delivery
- AND a fresh measurement yields the readiness's input digest again, and the branch holds no delivery commit

### scenario.delivery.staged-filtered — Staging through a filter a checkout reverses is delivered

- GIVEN a workspace that is ready, with a new file `src/a/extra.py` under a clean filter that reverses each line and a smudge filter that reverses it back
- WHEN the workspace is delivered
- THEN the result has status `ok`
- AND the delivery commit holds the filtered content, which a checkout turns back into the content the readiness examined

### scenario.delivery.stage-refused — Git refuses to stage a change

- GIVEN a workspace that is ready, with changes staged before the delivery, an intent-to-add path, a skip-worktree and an assume-unchanged flag
- AND a Git clean filter that refuses one of its changed files, which the readiness's checks do not read through Git
- WHEN the workspace is delivered
- THEN the result has status `failed` with `stage_failed` and a `git add` cause carrying Git's output
- AND the index is again exactly as before the delivery
- AND a fresh measurement yields the readiness's input digest again, and the branch holds no delivery commit

### scenario.delivery.unmerged-index — An unmerged index is refused before anything changes

- GIVEN a workspace that is ready while its index holds unmerged entries for `src/a/calc.py`
- WHEN the workspace is delivered
- THEN the result has status `failed` with `index_unrecorded`, reason `decision`, the unmerged path in its detail and options to resolve or abort the merge
- AND its cause is the `git write-tree` link with Git's output
- AND the index, the metadata and the branch are unchanged

### scenario.delivery.recover — A delivery interrupted after its commit needs no repair

- GIVEN a delivery run that created its delivery commit and ended without saving its result
- WHEN delivery runs again
- THEN Delivery validates the whole workspace again
- AND no new commit is created
- AND the output is the existing commit with `recovered` true, and the worktree is clean
- AND the branch still holds exactly that one delivery commit, which alone records the delivery
- AND the new run's trace node references that commit with `found_commit`

### scenario.delivery.recover-unverified — A head that only looks delivered is not reported

- GIVEN a clean workspace whose head has the subject of a delivery commit of the workspace
- AND the head is a merge commit, with two parents
- WHEN delivery runs
- THEN the result has status `failed` with `commit_unverified`, reason `decision`, naming the mismatch
- AND no commit is created and the head is unchanged
- AND the run's trace node references no commit, created or found

### scenario.delivery.recover-not-ready — A delivered head whose workspace is not ready is not reported

- GIVEN a clean workspace whose head has the subject of a delivery commit of the workspace and one parent
- AND that commit holds a file no Module binds
- WHEN delivery runs
- THEN the result has status `blocked` with `not_ready`, and Validation's `not_deliverable` link names the file as a cause
- AND no commit is created and the head is unchanged
- AND the run's trace node references no commit, created or found
