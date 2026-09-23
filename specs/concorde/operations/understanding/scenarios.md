# Understanding scenarios

Concrete situations that show the [requirements](requirements.md) at work. The assessment's shape
is in the [contracts](contracts.md).

## Assessing

### scenario.understanding.sufficient — A sufficient Spec is confirmed

- GIVEN a task worktree whose bound Module states every promise a goal needs
- WHEN the main agent runs `understand` for that Module with the goal and without `--plan`
- THEN the worker receives the Module's Spec context to read and its implementation files by name only
- AND the result has status `ok` and an assessment marked sufficient
- AND the assessment carries no plan and no Spec gap

### scenario.understanding.plan — A plan is returned on request

- GIVEN a task worktree whose bound Modules state every promise a goal needs
- WHEN the main agent runs `understand` for them with the goal and `--plan`
- THEN the result has status `ok` and a sufficient assessment with a plan
- AND the plan names the Modules to change, the files to declare as pending entries with their Module and realization, and the ordered next Operations

### scenario.understanding.gap — A missing promise is reported, not inferred

- GIVEN a goal that needs a promise the bound Module's Spec does not state
- AND the Module's code may well implement that behaviour
- WHEN the main agent runs `understand` for that Module with the goal and `--plan`
- THEN the result has status `ok` and an assessment marked insufficient
- AND each Spec gap names the Module, the document where the promise belongs, what is missing and why the goal needs it
- BUT the assessment carries no plan and states no promise taken from the code

### scenario.understanding.unassessable — A goal that cannot be assessed escalates

- GIVEN a goal that concerns a Module the run is not bound to
- WHEN the worker cannot assess the goal from its Spec context
- THEN the result has status `blocked`
- AND it carries the worker's escalation with the problem, what it tried and its options

## Host checks

### scenario.understanding.unknown-module — An unknown Module fails the run

- GIVEN a worker whose assessment names a Module identity the task worktree does not define
- WHEN the host checks the assessment
- THEN the result has status `failed`
- AND the unknown identity is listed as host evidence

### scenario.understanding.change-detected — A change to the worktree fails the run

- GIVEN an understand run whose write audit finds a changed or new file in the task worktree
- WHEN the host evaluates the audit
- THEN the result has status `failed` with the changed paths as host evidence
- BUT the worker is not resumed
