# Understanding scenarios

Concrete situations that show the [requirements](requirements.md) at work. The assessment's shape
is in the [contracts](contracts.md).

## Assessing

### scenario.understanding.sufficient — A sufficient Spec is confirmed

- GIVEN a workspace whose bound [Module](../../../glossary.json#concept.module) states every promise a goal needs
- WHEN the caller runs `understand` in it for that Module with the goal and without `--plan`
- THEN the worker receives the Module's [Spec context](../../../glossary.json#concept.spec-context) to read and its implementation files by name only
- AND the result has status `ok` and an assessment marked sufficient
- AND the assessment carries no plan and no [Spec gap](../../../glossary.json#concept.spec-gap)

### scenario.understanding.plan — A plan is returned on request

- GIVEN a workspace whose bound Modules state every promise a goal needs
- WHEN the caller runs `understand` in it for them with the goal and `--plan`
- THEN the result has status `ok` and a sufficient assessment with a plan
- AND the plan names the Modules to change, the new files the change needs with the Module that will bind each, and the ordered next runs

### scenario.understanding.gap — A missing promise is reported, not inferred

- GIVEN a goal that needs a promise the bound Module's [Spec](../../../glossary.json#concept.spec) does not state
- AND the Module's code may well implement that behaviour
- WHEN the caller runs `understand` for that Module with the goal and `--plan`
- THEN the result has status `ok` and an assessment marked insufficient
- AND each Spec gap names the Module, the document where the promise belongs, what is missing and why the goal needs it
- BUT the assessment carries no plan and states no promise taken from the code

### scenario.understanding.unassessable — A goal that cannot be assessed stops the run

- GIVEN a goal that concerns a Module the run is not bound to
- WHEN the worker cannot assess the goal from its Spec context
- THEN the result has status `blocked`
- AND its [error chain](../../../glossary.json#concept.error-chain) ends in the worker's own link with the problem, what it tried, why it could not assess and its options

## Host checks

### scenario.understanding.unknown-module — An unknown Module fails the run

- GIVEN a worker whose assessment names a Module identity the Specs of the worktree the run works on do not define
- WHEN the [Operation](../../../glossary.json#concept.operation) checks the assessment
- THEN the result has status `failed`
- AND the unknown identity is listed as host evidence

### scenario.understanding.inconsistent — An inconsistent assessment fails the run

- GIVEN a worker whose assessment breaks one of the consistency rules of [req.understanding.consistent](requirements.md#req.understanding.consistent), such as a plan although `--plan` was not given
- WHEN the Operation checks the assessment
- THEN the result has status `failed` with each inconsistency as host evidence
- BUT the worker is not resumed

### scenario.understanding.change-detected — A change to the worktree fails the run

- GIVEN an understand run whose worker leaves a changed or new file in the worktree the run works on
- WHEN Workers' [write audit](../../../glossary.json#concept.write-audit) finds it after the round
- THEN the result has status `failed` with the changed paths as host evidence
- BUT the worker is not resumed
