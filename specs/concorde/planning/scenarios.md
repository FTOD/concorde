# Planning scenarios

Concrete situations for context assessment, planning, task authoring, component requests and
pending gaps in the [Planning Module](module.md). The exact records and obligations are in the
[planning reference](workflow.md).

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
- WHEN a fresh context assessor reports the missing promise as an Issue and returns `spec_incomplete` with a blocker citing that Issue and naming the blocked step
- THEN the Host accepts the assessment
- AND records the blocker as a pending gap for that step, target and task
- BUT the assessor reads no implementation contents and no other Module's context to fill the gap

See [report necessary gaps as Issues](workflow.md#req.planning.assessment-gap).

### scenario.planning.native-assessment-prepared — Preparation runs no model

- GIVEN a selected Module with a current frozen context and the candidate's own Pi entry
- WHEN `concorde-context-solve` prepares its native context-assessor call
- THEN the prepared call and its descriptor are returned as `prepared`
- AND no model runs during preparation
- BUT nothing is accepted and no Agent with the same name installed elsewhere can replace the prepared one

### scenario.planning.native-assessment-accepted — A completed native assessment is accepted

- GIVEN a prepared native context-assessor call that the user session invoked unchanged
- WHEN the native run completes, its proposal passes its staging gate and every frozen input is unchanged
- THEN the Host accepts the assessment
- AND a sufficient result stays distinct from a business-blocked one
- AND the accepted evidence is written to the primary worktree's run records, not kept in the capsule

### scenario.planning.native-assessment-rejected — A foreign or malformed proposal is not accepted

- GIVEN a prepared native context-assessor call
- WHEN the proposal is submitted twice, names another invocation, does not match the output schema, or was altered after staging
- THEN the Host accepts nothing
- AND the result names the rejection

### scenario.planning.native-assessment-stale — Changed inputs invalidate a native assessment

- GIVEN a prepared native context-assessor call
- WHEN the configuration, registry, Spec, Agent definition or capture extension changes, or the capsule is missing, before the Host accepts the proposal
- THEN the Host rejects the proposal as stale
- BUT no earlier accepted assessment or gap changes

### scenario.planning.native-assessment-failed — A failed native run is an execution failure

- GIVEN a prepared native context-assessor call
- WHEN the native run fails or is cancelled, even after its staging gate passed
- THEN the result is an execution failure, not a Spec outcome
- BUT the Host accepts nothing and records no pending gap

### scenario.planning.assessment-preview — A preview writes no capsule

- GIVEN a selected Module and task
- WHEN `concorde-context-solve` runs in `describe-policy` mode
- THEN the Host returns the intended read policy with status `described`
- BUT no capsule is written and no Agent starts

### scenario.planning.collaboration-gap — An unexplained collaboration stops the assessment

- GIVEN a selected Module with a `uses`, `contains` or `participates` whose explanation does not resolve
- WHEN a context assessment is prepared
- THEN the Host reports a gap Issue for the collaboration and returns `spec_incomplete` with a blocker citing it
- BUT no Agent starts

### scenario.planning.collaboration-conflict — Inconsistent collaborations stop the assessment

- GIVEN a selected Module whose `relies_on` names a node the provider does not own, which uses itself, or whose context requirements are not reconciled
- WHEN a context assessment is prepared
- THEN the Host returns `conflicting` naming the findings
- BUT no Agent starts and no Issue is reported

## Planning

### scenario.planning.plan-current — A sufficient assessment admits a plan

- GIVEN a selected Module, task and constraints whose Spec is sufficient
- WHEN the plan workflow's planner returns a nonempty plan and the Host accepts it
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

### scenario.planning.native-plan-tasks — Native planning and task authoring succeed

- GIVEN a managed candidate for a selected Module with a current required Spec review, if one is required
- WHEN the user session invokes the prepared plan workflow and then the prepared task-author call
- THEN each assessor, planner and task author runs as a fresh Agent with its own frozen context and no implementation contents
- AND the planner starts only after the Host accepted a sufficient assessment
- AND the plan and task list are saved in the candidate with their run evidence in the primary worktree

### scenario.planning.native-plan-failure — A failed plan workflow replaces nothing

- GIVEN a candidate with an accepted plan and tasks for a Module
- WHEN a new plan workflow's Agent run fails, is cancelled or cannot be verified
- THEN the workflow stops at that step and the Host marks the candidate's progress blocked while its inputs are unchanged
- BUT the previously accepted plan and tasks stay unchanged

## Task authoring

### scenario.planning.tasks-from-plan — An accepted plan yields tasks

- GIVEN a managed candidate with a current accepted plan for the target
- WHEN a fresh task author returns a nonempty list of new, uniquely identified, incomplete tasks aimed at Modules in the Module's change scope
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
- WHEN the task author returns a task whose target lies outside the Module's change scope
- THEN the Host refuses the list with `permission_denied`
- BUT no task list is saved and no programmer starts for that target

See [accept only valid new task lists](workflow.md#req.planning.tasks-admission).

### scenario.planning.change-scope — A change spans every Module that must change with it

- GIVEN a Module that defines a contract another Module participates in, without using that Module
- AND a task that raises the contract's version, so every participant's declaration must move with it
- WHEN the task author returns tasks for the Module and for the participant
- THEN the Host accepts the list, because the participant lies in the Module's change scope
- AND the change scope also holds the Modules the Module contains or uses, the Modules whose Spec context selects its documents, the Modules referencing a node it defines and the Modules binding one of its files

### scenario.planning.task-history-identities — Task authors receive the reserved identities

- GIVEN a target that keeps task lists from earlier plans or repairs
- WHEN the Host prepares a fresh task author, including after a new plan
- THEN its inputs include every identity in the task history and every identity of the current list
- AND those identities constrain naming only and add no work to the new list

### scenario.planning.tasks-id-conflict — A reserved identity is reused

- GIVEN reserved task identities for a fresh task author
- WHEN the returned list reuses one of them
- THEN the Host rejects the list and reports the colliding identities
- AND the prior task list and task history stay unchanged
- BUT the Host never rewrites the Agent's answer to make it fit

See [collisions preserve history](workflow.md#req.planning.task-collision-preserves).

### scenario.planning.task-control-values — Task metadata values are checked as typed values

- GIVEN a `concorde-task-scope-feedback` or `concorde-task-identity-constraints` value as described in [task records](workflow.md)
- WHEN it is checked as a typed value
- THEN a valid version-1 value is returned unchanged
- BUT checking reads and writes no project file

### scenario.planning.task-control-values-refused — An invalid task metadata value is refused

- GIVEN a task metadata value with an unknown field, a malformed digest, another reason value, a blank or repeated reserved identity, a wrong type or another version
- WHEN it is checked as a typed value
- THEN it is refused with an error naming its code and field

## Repair

### scenario.planning.repair-current — Review repair with current review evidence

- GIVEN accepted tasks and a `repair_review` reference to the code review currently recorded for this target and task
- AND that review completed its coverage with blocking findings whose Issue receipts resolve
- WHEN task authoring admits it
- THEN the task author receives the current list, the review result and the context of the Issues it cites
- AND an accepted new list keeps the review reference for implementation

### scenario.planning.repair-stale — Review repair with stale evidence is refused

- GIVEN accepted tasks and a `repair_review` reference
- WHEN the referenced review is missing, corrupt, replaced by a later one, has no blocking finding, or was made for changed Spec, code or instructions
- THEN the request is refused before a task author starts
- BUT no task or task history changes

### scenario.planning.repair-replacement — Replacing repaired tasks keeps history

- GIVEN a target whose current tasks were admitted from review feedback
- WHEN the user session replaces them without repair feedback, or obtains a new plan
- THEN the old feedback is dropped from the target
- AND the replaced identities stay reserved in the task history
- BUT required independent reviews still need fresh evidence

### scenario.planning.scope-repair — Correcting task scope without a stale plan

- GIVEN a current accepted plan and an incomplete task list selected by its digest in `repair_task_scope`
- WHEN a fresh task author rewrites the acceptance conditions to stay within what the programmer can do
- THEN the Host accepts the new incomplete tasks
- AND moves the prior list to the task history with the reason `implementation_boundary`

### scenario.planning.scope-repair-refused — An invalid scope repair changes nothing

- GIVEN a task scope repair request
- WHEN the plan is stale, the digest does not match the current list, every task is complete, or a review repair is requested at the same time
- THEN the request is refused with `stale_context` or `incompatible_handoff` before a task author starts
- BUT the tasks and the task history stay unchanged

## Component requests

### scenario.planning.component-request — A derived component request is admitted

- GIVEN a candidate owned by a Module whose current accepted tasks name a component in its change scope
- WHEN the user session requests a plan for the component with the derived component task and the owner's constraints
- THEN the request is admitted in the owner's candidate
- AND the candidate's owner does not change

### scenario.planning.component-stale-parent — A component request needs the owner's current plan

- GIVEN a candidate owned by a Module with accepted tasks for a component
- WHEN the owner's Spec has changed since its plan, or the request's task or constraints differ from the derived component task
- THEN the request is refused before any Agent starts or any recorded work changes
- AND the user session must plan the owner again before retrying

## Pending gaps

### scenario.planning.pending-gap-blocks — A pending gap stops later steps

- GIVEN a candidate with a pending gap recorded for a Module's `context-solve` step against its current Spec revision
- WHEN the user session requests `concorde-plan`, `concorde-tasks` or `concorde-implement` for the same Module and task
- THEN the Host returns `spec_incomplete` with the recorded blocker
- BUT no Agent starts and repeating the request does not clear the gap

### scenario.planning.pending-gap-cleared — A repaired Spec clears the gap

- GIVEN a pending gap for a Module's `context-solve` step
- AND the Module's Spec was edited so its revision changed
- WHEN a context assessment for the same task is accepted without blockers
- THEN the gap is resolved and later steps may start
- BUT the Issue the gap cited stays open
