# Planning workflow and records

The exact mechanics behind the [Planning entry](module.md): how the Host prepares and accepts a
native Agent step, the steps of the planning workflow, what the plan and task records contain, and
the Module-wide obligations of Planning.

## Native preparation

The Pi session asks the launcher's native preparation entry to prepare a step. The Host then:

1. Runs Request admission and dispatch as for any request. A mutating request received in the
   primary worktree is prepared inside the candidate worktree by the candidate's own launcher.
2. Checks the prerequisites. Plan and tasks require a current Spec review when the candidate records
   one as required. A gap recorded for the same step, target and task that is still unchanged
   returns `spec_incomplete` without starting a model. Context assessment first runs the
   collaboration pre-check described in the entry.
3. Freezes the context snapshot and writes a capsule directory with: the Module's Spec documents;
   the Module's declared external references when the role reads references; an index
   `context.json`; a Pi Agent definition `.pi/agents/concorde-<role>.md` with the role's instructions
   and tools plus `report_issue`, no nested subagents and no inherited project, global or skill
   context; a capture extension through which the Agent submits its proposal; and a descriptor that
   records the digests of everything delivered.
4. Returns the exact native call: the Agent name, a task naming the invocation's ticket, the capsule
   as working directory, a fresh context, and an output schema that requires the ticket and a typed
   stage result.

The user session must invoke that call unchanged and only once. A second or altered call is
refused.

## Acceptance

When a native step ends, the Host accepts its proposal only when all of the following hold:

- the native run completed, and was not interrupted, stopped, timed out or failed;
- the proposal was submitted through the capture extension, is at most 1 MiB, names this ticket and
  matches the role's output schema;
- its context identity is the frozen one, and its outcome agrees with its blockers: `spec_incomplete`
  has blockers, `sufficient` and `completed` have none;
- every Issue it cites was recorded during this run;
- the snapshot, configuration, instruction digest, registry digest, candidate state and delivered
  files are unchanged, and the native runtime is the one that was prepared;
- the role's business rules below hold.

Before writing anything the Host reserves a terminal receipt for the step, so an uncertain failure
can never apply the same result twice. It then writes the result into the candidate and records the
run's evidence under `.concorde/runs/<invocation>/native-context.json` in the primary worktree.

A direct Agent step, `concorde-context-solve` or `concorde-tasks`, is accepted by the Pi session's
result hook when the native call returns. The planning workflow accepts its steps itself.

## The planning workflow

`pi/workflows/plan.js` is authored native control flow. Its only inputs are the Host-issued call
and three fixed Host commands. It runs:

| Step | Kind | What happens |
| --- | --- | --- |
| `bind` | Host | Waits for the workflow's launch binding, rechecks the inputs and preflights the assessor call |
| `assessor` | Agent | A fresh context assessor runs; its staging gate records the proposal without accepting it |
| `advance` | Host | Verifies the assessor's native run and accepts the assessment; if it is sufficient, prepares the planner, otherwise ends with the assessment |
| `planner` | Agent | A fresh planner runs; its staging gate records the proposal |
| `finalize` | Host | Verifies exactly the two expected native runs, accepts the plan and saves it |

The workflow stops at the first child that did not complete, failed its staging gate or lost its
evidence. Before preparing the planner, `advance` rechecks the assessed contracts, registry,
configuration, instruction digest and candidate state against the state recorded when the
assessment was accepted, so the assessment's own recorded effects do not count as a change.

The user session polls the `concorde` tool with `action: "result"`. The answer separates the
native state (running, complete, failed or stopped) from the Host's `accepted` flag and business
outcome. When the native run failed or was stopped, the Host marks the candidate's progress as
blocked with `execution_failed` or `execution_cancelled`, but only while the candidate's inputs are
still the ones this workflow was prepared for. Shutting down the Pi session stops the run and
invalidates its later Host steps.

## Plan record

An accepted plan's text is written to `.concorde/work/<target>/plan.md` in the candidate. The
target's entry in the change record is updated: `plan`, `spec_digest` (the Spec revision),
`task` and `constraints` (the request's), `completed_operations`, `phase: plan` and
`status: active`; `tasks` and `checks` are emptied and `implementation_digest` is cleared. A
previous task list moves to `task_history` with the reason `replan`, and any pending repair review,
component coordination and component revisions are dropped.

## Task record

Each task has exactly `id`, `target_id`, `description`, `acceptance` and `complete`. The task author
receives the plan as `concorde-plan-artifact` and the reserved identities as
`concorde-task-identity-constraints`, even when that list is empty. A scope repair adds the current
list as `concorde-implementation-task` and `concorde-task-scope-feedback` with the list's digest and
the reason `implementation_boundary`. A review repair adds the current list and the verified review
result, together with the context of the Issues it cites.

An accepted list replaces `tasks`. The replaced list moves to `task_history` with the reason
`review_feedback`, `implementation_boundary` (with its digest and Spec revision) or
`caller_replacement`. `checks` are emptied, `implementation_digest` is cleared and `phase` becomes
`tasks`. A review repair's reference is kept for implementation; any other replacement drops it.

A scope repair needs the exact current list: nonempty, matching the digest, not all complete, and
not combined with a review repair. Otherwise the request is refused with `incompatible_handoff`.

## Requirements

### req.planning.admitted-contract — Plan only after a sufficient assessment

Planning SHALL save a plan only after a sufficient context assessment of the selected Module's current Spec for the same task.

### req.planning.assessment-context — Assess only the selected context

Planning SHALL assess a task only against the frozen context of the selected Module.

The assessor never reads implementation contents or another Module's context to fill a gap.

### req.planning.assessment-gap — Report necessary gaps as Issues

Planning SHALL report every missing promise that a task needs as an Issue cited by a blocker that names the blocked step.

### req.planning.spec-only — No implementation contents

Planning SHALL give its Agents the names of implementation files but not their contents.

### req.planning.review-gate — Required Spec review first

Planning SHALL refuse to prepare a planner or task author while a Spec review that the candidate requires for the Module is missing, blocking or stale.

### req.planning.plan-rejection-preserves — Rejected plans preserve accepted state

Planning SHALL leave the previously accepted plan and tasks unchanged when it rejects a returned plan.

### req.planning.tasks-require-plan — Tasks require a current plan

Planning SHALL refuse task authoring unless the target has an accepted plan that is current for the Module's Spec revision and the request's task and constraints.

### req.planning.tasks-admission — Accept only valid new task lists

Planning SHALL accept only nonempty task lists whose tasks are uniquely identified, initially incomplete, disjoint from the reserved identities and targeted at the selected Module, a Module it uses or one of its direct children.

### req.planning.task-collision-preserves — Collisions preserve history

Planning SHALL keep the prior task list and task history unchanged when it rejects a list for reusing reserved identities.
