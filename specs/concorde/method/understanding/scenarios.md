# Understanding scenarios

Concrete situations that show the [requirements](requirements.md) at work. The assessment's shape
is in the [contracts](contracts.md).

## Assessing

### scenario.understanding.sufficient — A sufficient Spec is confirmed

- GIVEN a workspace whose bound [Module](../../glossary.json#concept.module) states every promise a goal needs
- WHEN the caller runs `understand` in it for that Module with the goal and without `--plan`
- THEN the worker receives the Module's [Spec context](../../glossary.json#concept.spec-context) to read and its implementation files by name only
- AND the result has status `ok` and an assessment marked sufficient
- AND the assessment carries no plan and no [Spec gap](../../glossary.json#concept.spec-gap)

### scenario.understanding.plan — A plan is returned on request

- GIVEN a workspace whose bound Modules state every promise a goal needs
- WHEN the caller runs `understand` in it for them with the goal and `--plan`
- THEN the result has status `ok` and a sufficient assessment with a plan
- AND the plan names the Modules to change, the new files the change needs with the Module that will bind each, and the ordered next runs

### scenario.understanding.gap — A missing promise is reported, not inferred

- GIVEN a goal that needs a promise the bound Module's [Spec](../../glossary.json#concept.spec) does not state
- AND the Module's code may well implement that behaviour
- WHEN the caller runs `understand` for that Module with the goal and `--plan`
- THEN the result has status `ok` and an assessment marked insufficient
- AND each Spec gap names the Module, the document where the promise belongs, what is missing and why the goal needs it
- BUT the assessment carries no plan and states no promise taken from the code

### scenario.understanding.unassessable — A goal that cannot be assessed stops the run

- GIVEN a goal that concerns a Module the run is not bound to
- WHEN the worker cannot assess the goal from its Spec context
- THEN the result has status `blocked`
- AND its [error chain](../../glossary.json#concept.error-chain) ends in the worker's own link with the problem, what it tried, why it could not assess and its options

## Host checks

### scenario.understanding.unknown-module — An unknown Module fails the run

- GIVEN a worker whose assessment names a Module identity the Specs of the worktree the run works on do not define
- WHEN the [Operation](../../glossary.json#concept.operation) checks the assessment
- THEN the result has status `failed`
- AND the unknown identity is listed as host evidence

### scenario.understanding.inconsistent — An inconsistent assessment fails the run

- GIVEN a worker whose assessment breaks one of the consistency rules of [req.understanding.consistent](requirements.md#req.understanding.consistent), such as a plan although `--plan` was not given
- WHEN the Operation checks the assessment
- THEN the result has status `failed` with each inconsistency as host evidence
- BUT the worker is not resumed

### scenario.understanding.change-detected — A change to the worktree fails the run

- GIVEN an understand run whose worker leaves a changed or new file in the worktree the run works on
- WHEN Workers' [write audit](../../glossary.json#concept.write-audit) finds it after the round
- THEN the result has status `failed` with the changed paths as host evidence
- BUT the worker is not resumed

## Reviewing a plan

### scenario.understanding.plan-accepted — A sound plan is accepted

- GIVEN a task worktree and a plan file its caller wrote for the workspace's goal
- WHEN the caller runs `plan_review --plan <file>` in it
- THEN the reviewer receives the plan, the workspace's goal, the bound Modules' [Spec context](../../glossary.json#concept.spec-context) and the project's code to read, and nothing to write
- AND the result has status `ok`, iteration 1 and verdict `accepted` when no finding is blocking
- AND the report names the plan's kept copy in the run's [trace node](../../glossary.json#concept.trace-node) and its digest

### scenario.understanding.plan-changes-required — Blocking findings require a revision

- GIVEN a plan whose step would break a promise a bound Module's [Spec](../../glossary.json#concept.spec) states
- WHEN the reviewer reports it as a blocking `violation` finding citing that promise
- THEN the result has status `ok` and verdict `changes_required`
- AND the finding is kept as the reviewer wrote it

### scenario.understanding.plan-next-iteration — The next iteration answers the previous one

- GIVEN an `ok` `plan_review` run with findings `F1` and `F2`
- WHEN the caller revises the plan and runs `plan_review` with that run as `--input`, `--accept F1` with how the plan now settles it and `--reject F2` with its reason
- THEN the reviewer's brief carries the previous findings and both answers
- AND the report has iteration 2, names the previous run and repeats the answers
- AND the reviewer responds to `F1` and `F2`, restating a maintained one as a finding of this iteration

### scenario.understanding.plan-unanswered — An unanswered finding stops the next iteration

- GIVEN an `ok` `plan_review` run with findings `F1` and `F2`
- WHEN the caller runs `plan_review` with that run as `--input` and answers only `F1`
- THEN the result has status `failed` with `iteration_mismatch` naming `F2`
- BUT no worker is launched

### scenario.understanding.plan-unreadable — A missing plan stops the run

- GIVEN a `--plan` naming a file that does not exist or is empty
- WHEN the caller runs `plan_review`
- THEN the result has status `failed` with `plan_unreadable`
- BUT no worker is launched

### scenario.understanding.plan-inconsistent — A review that ignores the previous iteration fails

- GIVEN a `plan_review` run whose previous iteration had a finding `F1`
- WHEN the reviewer's answer has no response to `F1`, or restates a finding it settled
- THEN the result has status `failed` with `inconsistent_review` listing each inconsistency
- BUT the reviewer is not resumed

### scenario.understanding.plan-unresolved-basis — A basis must resolve

- GIVEN a reviewer whose finding cites an identity the bound Modules' Spec context does not define, or a `violation` without a basis
- WHEN the Operation checks the review
- THEN the result has status `failed` with `unresolved_basis` naming the finding
