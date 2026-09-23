# Planning scenarios

Concrete situations for context assessment, planning and task authoring in the
[Planning Module](module.md). The Module-wide obligations and the exact records are in the
[planning workflow](workflow.md).

## Context assessment

### scenario.planning.assessment-sufficient — The Spec supports the task

- GIVEN a selected Module whose declared collaborations are consistent
- AND whose Spec states everything the task needs
- WHEN a fresh context assessor evaluates the task
- THEN the Host accepts the outcome `sufficient`
- AND no plan, task or document is written
- BUT the answer concerns this task only and says nothing about other tasks

### scenario.planning.assessment-gap — A needed promise is missing

- GIVEN the selected Module's Spec lacks a promise the task needs
- WHEN a fresh context assessor evaluates the task
- THEN it reports the missing promise as an Issue and returns `spec_incomplete` with a blocker citing that Issue and naming the blocked step
- AND the Host records the blocker for that step, target and task
- BUT the assessor reads no implementation contents and no other Module's context to fill the gap

See [report necessary gaps as Issues](workflow.md#req.planning.assessment-gap).

### scenario.harness.native-context-public — A prepared native assessment is accepted independently

- GIVEN a selected Module with a current frozen context and the candidate's own Pi entry
- WHEN `concorde-context-solve` prepares its native context-assessor call and the user session invokes that exact call
- THEN the prepared call and its descriptor are returned as `prepared` and not accepted, and no model runs during preparation
- AND the proposal the Agent submits and its passing staging gate are recorded as `proposed` and `staged`, never as accepted
- AND the Host accepts the assessment only after the native run completed and every frozen input is unchanged, keeping a sufficient result distinct from a business-blocked one
- AND `describe-policy` returns the intended read policy without writing a capsule or starting an Agent, and a known collaboration gap stops before any Agent starts
- BUT a duplicate, foreign or malformed proposal, a native failure despite a passing gate, a cancellation, a changed configuration, registry, Spec, Agent definition or capture extension, or a missing capsule accepts nothing

The prepared Agent is found only in the capsule's project scope, so an Agent with the same name
installed elsewhere cannot replace it. Accepted evidence is written to the primary worktree's run
records, not kept in the capsule. The identity's `harness` prefix is kept because tests declare
it; an identity prefix does not establish ownership.

## Planning

### scenario.planning.plan-current — A sufficient assessment admits a plan

- GIVEN a selected Module, task and constraints whose Spec is sufficient
- WHEN the planning workflow's planner returns a nonempty plan and the Host accepts it
- THEN the plan is saved in the candidate, bound to the current Spec revision and the task
- AND the result references the saved plan
- BUT no task list, code change or readiness is produced

### scenario.planning.plan-empty — An empty plan is rejected

- GIVEN a target with a previously accepted plan
- AND a sufficient assessment that admitted a fresh planner
- WHEN the planner returns an empty plan
- THEN the Host rejects it
- AND the previously accepted plan and tasks stay unchanged

### scenario.planning.plan-stale — Changed inputs invalidate a returned plan

- GIVEN a planning run prepared against a Spec revision and task
- AND the Spec, registry, configuration or candidate state changes before the plan is accepted
- WHEN the Host checks the returned plan
- THEN it rejects the plan as stale
- AND the previously accepted plan stays unchanged
- BUT keeping the old plan does not make it current for the changed inputs

## Task authoring

### scenario.planning.tasks-from-plan — An accepted plan yields tasks

- GIVEN a managed candidate with a current accepted plan for the target
- WHEN a fresh task author returns a nonempty list of new, uniquely identified, incomplete tasks aimed at the Module, a Module it uses or a direct child
- THEN the Host saves the list in the candidate's change record
- AND the result references that record
- BUT the task author completes no task and writes no project file

### scenario.planning.tasks-missing-plan — Task authoring without a plan

- GIVEN a managed candidate with no accepted plan for the selected target
- WHEN the user session requests task authoring
- THEN the Host refuses the request with `missing_plan` before starting a task author
- AND no task list is created and the task history is unchanged

### scenario.planning.tasks-foreign-target — A task for an unrelated Module is refused

- GIVEN a current accepted plan for the selected Module
- WHEN the task author returns a task whose target is neither the Module, a Module it uses nor one of its direct children
- THEN the Host refuses the list and the result is blocked
- BUT no task list is saved and no programmer starts for that target

See [accept only valid new task lists](workflow.md#req.planning.tasks-admission).

### scenario.planning.task-history-identities — Task authors receive the reserved identities

- GIVEN a target that keeps task lists from earlier plans or repairs
- WHEN the Host prepares a fresh task author, including after a new plan
- THEN its inputs include every identity in the task history and, for a repair, every identity of the list being replaced
- AND those identities constrain naming only and add no work to the new list

### scenario.planning.tasks-id-conflict — A reserved identity is reused

- GIVEN reserved task identities for a fresh task author
- WHEN the returned list reuses one of them
- THEN the Host rejects the list and reports the colliding identities
- AND the prior task list and task history stay unchanged
- BUT the Host never rewrites the Agent's answer to make it fit

See [collisions preserve history](workflow.md#req.planning.task-collision-preserves).

## Repair

### scenario.planning.repair-current — Review repair needs current review evidence

- GIVEN accepted tasks and a `repair_review` reference chosen by the user session
- WHEN task authoring admits it
- THEN the reference must match the review currently recorded for this target and task, byte for byte
- AND the review must have completed its coverage and contain blocking findings with resolvable Issue references
- BUT missing, corrupt, replaced or stale evidence stops the request before a task author starts or any task changes

### scenario.planning.repair-replacement — Replacing repaired tasks keeps history

- GIVEN a target whose current tasks were admitted from review feedback
- WHEN the user session replaces them without repair feedback, or obtains a new plan
- THEN the old feedback is dropped from the target
- AND the replaced identities stay reserved in the task history
- BUT required independent reviews still need fresh evidence

### scenario.planning.scope-repair — Correcting task scope without a stale plan

- GIVEN a current accepted plan and an incomplete task list selected by its digest in `repair_task_scope`
- WHEN a fresh task author rewrites the acceptance conditions to stay within what the programmer can do
- THEN the Host accepts the new incomplete tasks and moves the prior list to the task history
- BUT a changed Spec, a stale plan, a mismatched digest, an all-complete list or a reserved-identity collision is refused without changing the tasks or the history

## Native execution

### scenario.planning.native-plan-tasks — Native planning keeps the business rules

- GIVEN a managed candidate for a selected Module with a current required Spec review, if one is required
- WHEN the user session invokes the prepared planning workflow and then the prepared task-author call
- THEN each assessor, planner and task author runs as a fresh Agent with its own frozen context and no implementation contents
- AND the planner starts only after the Host accepted a sufficient assessment
- AND a valid plan and task list are saved in the candidate with their run evidence in the primary worktree
- BUT a failed, cancelled or unverifiable run, an empty plan or task list, a reserved identity, or changed Spec, metadata, task or plan inputs replaces nothing that was accepted before
