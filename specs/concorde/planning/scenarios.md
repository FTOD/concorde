# Planning scenarios

These precise specifications belong directly to the [Planning Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Task sufficiency](assessment.md#terminology) | Defined in Is the specification sufficient for this task? |
| [Acceptance task](tasks.md#terminology) | Defined in Making work verifiable. |
| [Reserved task ID](tasks.md#terminology) | Defined in Making work verifiable. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Semantic completeness](../spec/structure.md#terminology) | Defined in What structural validation tells you. |

## Planning

### scenario.development.task-history-identities — Task authors receive reserved identities

- GIVEN a target may retain task lists from earlier repair rounds
- WHEN the Host invokes a fresh task author, including after replanning
- THEN its typed stage inputs include every retained historical task ID and, for a scope or code-review repair, every ID in the list being replaced
- AND those reserved IDs constrain identity only and add no software obligations or implementation contents
- AND returned tasks must be nonempty, internally unique, initially incomplete and disjoint from the reserved IDs
- AND a collision reports the conflicting IDs without rewriting the result, replacing tasks or discarding history

The independent contracts are [Assessment](assessment.md), [Plan](plan.md) and [Tasks](tasks.md).

## Context assessment

### scenario.planning.assessment-sufficient — The admitted contract supports the task

- GIVEN a selected Module whose dependency declarations agree with its registered relationships
- AND its complete admitted Spec supplies the contracts necessary for the task
- WHEN the fresh context assessor evaluates that task
- THEN it returns sufficient without authored documents, a plan or tasks
- AND the assessment concerns that task and does not prove universal semantic completeness

### scenario.planning.assessment-gap — A necessary promise is missing

- GIVEN the selected Module's complete admitted Spec lacks a contract needed for the task
- WHEN context assessment reaches the dependent judgment
- THEN it reports spec_incomplete with question, blocked_step and needed_contract and host-bound target/context provenance
- AND the dependent step pauses while independent reasoning may continue
- AND the assessor neither reads implementation contents nor expands the selected context to supply the missing promise

## Planning capability

### scenario.planning.plan-current — Assessment admits a revision-bound plan

- GIVEN a selected Module, task and constraints with sufficient complete contract context
- WHEN a fresh planner returns a nonempty plan
- THEN the host persists the accepted plan against that revision and returns its ArtifactRef
- AND no task list, code changes or ready state is produced

### scenario.planning.plan-empty — An empty result cannot replace a plan

- GIVEN a target has a previously accepted plan and current sufficient assessment admits a fresh planner
- WHEN that planner returns an empty plan
- THEN the host rejects the returned plan and preserves the previously accepted plan
- AND no replacement plan artifact is accepted for dependent task authoring

### scenario.planning.plan-stale — Changed inputs invalidate a returned plan

- GIVEN a previously accepted plan and a fresh planning invocation bound to a selected Spec revision and intent
- AND relevant admitted inputs change before its result is accepted
- WHEN the host rechecks the returned nonempty plan against current inputs
- THEN it rejects stale output without replacing the previously accepted plan
- AND preserving old bytes does not make the old plan current; reuse requires current admission

## Task authoring capability

### scenario.planning.tasks-from-plan — Accepted plan yields implementation tasks

- GIVEN a current managed change, accepted plan and complete reserved task-ID input
- WHEN a fresh task author returns a nonempty, internally unique, initially incomplete acceptance-task list disjoint from the reserved IDs
- THEN the host accepts and persists the list with its plan as the implementation task artifact
- AND its response supplies artifact references without completing tasks or granting the author project writes

### scenario.planning.tasks-missing-plan — Task authoring has no prerequisite plan

- GIVEN a current managed change with no authored plan for the selected target
- WHEN a declared composing caller requests task authoring
- THEN the host rejects the request with missing_plan before launching a task author
- AND it does not create a task list or discard retained task history

### scenario.planning.tasks-id-conflict — New output reuses a reserved identity

- GIVEN an accepted plan, prior tasks and retained history with IDs reserved for a fresh task author
- WHEN the returned task list reuses an admitted reserved ID
- THEN the host rejects the list and reports the conflicting IDs without rewriting author output
- AND the prior task list and retained history remain unchanged
