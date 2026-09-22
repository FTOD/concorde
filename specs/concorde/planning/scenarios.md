# Planning scenarios

These precise specifications belong directly to the [Planning Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                                      | Meaning / definition                                      |
| --------------------------------------------------------- | --------------------------------------------------------- |
| [Spec](../module.md#terminology)                          | Defined in Concorde Framework.                            |
| [Module](../module.md#terminology)                        | Defined in Concorde Framework.                            |
| [Host](../module.md#terminology)                          | Defined in Concorde Framework.                            |
| [Task sufficiency](assessment.md#terminology)             | Defined in Is the specification sufficient for this task? |
| [Acceptance task](tasks.md#terminology)                   | Defined in Making work verifiable.                        |
| [Reserved task ID](tasks.md#terminology)                  | Defined in Making work verifiable.                        |
| [Ready](../module.md#terminology)                         | Defined in Concorde Framework.                            |
| [Semantic completeness](../spec/structure.md#terminology) | Defined in What structural validation tells you.          |

## Planning

### scenario.planning.task-history-identities — Task authors receive reserved identities

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

## Planning operation

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

## Task authoring operation

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

### scenario.planning.repair-current — Explicit repair requires current independent evidence

- GIVEN accepted tasks and a caller-selected repair_review ArtifactRef
- WHEN task authoring admits blocking code-review feedback
- THEN the reference must match the current host-recorded report and its exact bytes, selected intent, target, focus and current review inputs
- AND the report must contain completed representative coverage and blocking findings with resolvable Issue receipts
- AND missing, corrupt, forged, replaced or stale evidence stops before a task worker or task-state replacement
- AND implementation rechecks the admitted feedback before use without automatically launching review or validation

### scenario.planning.repair-replacement — Replacement retires feedback without losing history

- GIVEN a target has tasks admitted from blocking review feedback
- WHEN the caller replaces those tasks without repair feedback or obtains a new accepted plan
- THEN old repair feedback is removed from the replacement state while prior task identities remain reserved in history
- AND selected independent review requirements remain in force without acquiring fabricated successful evidence

### scenario.planning.historical-author-gap — Supersede an obsolete author prerequisite

- GIVEN a managed change with a correctly attributed same-intent historical specify task relation, including an unknown original revision or obsolete non-contract author failure
- WHEN the caller makes any necessary direct contract edits and explicitly obtains a sufficient current context assessment for the accepted target, task, focus and constraints
- THEN the host supersedes only that retired prerequisite with current assessment evidence and an explicit retirement reason while preserving the original receipt, contexts, source evidence and open Issue
- AND editing alone, malformed attribution, unrelated intent, stale, insufficient or failed assessment cannot supersede it
- AND no historical success, Issue closure or contract repair is inferred from an obsolete execution failure
- AND required independent reviews must still be current before planning and task authoring
- AND retained plan, tasks, implementation and review gaps require their own accepted phase output rather than another phase's success

### scenario.planning.scope-repair — Repair task scope without accepting a stale plan

- GIVEN an accepted current plan and an exact incomplete task list selected by repair_task_scope digest
- WHEN a fresh task author corrects implementation-boundary acceptance using the plan, prior list, fixed scope feedback and reserved IDs
- THEN the host accepts only new incomplete tasks and retains the prior list in history without weakening software acceptance
- AND a stale Spec or plan, mismatched list digest, completed replacement or reserved-ID collision is rejected without replacing the accepted list or history
- AND implementation, configured checks and required independent review remain separately selected responsibilities

### scenario.planning.native-plan-tasks — Native plan and task authoring retain domain gates

- GIVEN a managed selected Module with exact current intent and any required Spec review
- WHEN the calling session invokes the prepared native planning workflow and then its direct task-author call
- THEN separate fresh assessor/planner/task-author executions retain complete scoped inputs and no implementation contents
- AND only sufficient independently accepted assessment launches the planner
- AND stage-only success after native failure never permits a dependent launch or persistence
- AND valid nonempty plan/tasks persist in the candidate with true primary-owned evidence/status
- AND empty output, duplicate/reserved task IDs, stale Spec/metadata/intent/plan or mismatched repair feedback cannot replace accepted artifacts
- AND cancellation stops unsettled acceptance while prior accepted artifacts remain inspectable
- AND scoped external references are delivered and rechecked without admitting unrelated references
- AND no Graph or hidden Pi-RPC model worker runs on these public paths
