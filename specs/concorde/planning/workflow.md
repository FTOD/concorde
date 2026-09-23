# Planning reference

The exact mechanics behind the [Planning entry](module.md): what each Agent hook contributes, the
checks before an Agent starts, the plan workflow, the records Planning writes, the implementation
task contract, the change scope, component requests, pending gaps, and the Module-wide obligations
of Planning.

## Agent hooks

Planning implements the Agent hook and workflow hook interfaces of Agent execution. The native
driver freezes the context, prepares the call, stages and verifies the proposal and records the run;
the hooks do only what depends on Planning.

| Hook | Agent and phase | Stage inputs it supplies | Business rules on acceptance | What acceptance writes |
| --- | --- | --- | --- | --- |
| assessor | `context_assessor` in `context-solve` | none | outcome is `sufficient`, `spec_incomplete`, `unsupported` or `conflicting`; `spec_incomplete` has blockers and the others have none | pending gaps for `context-solve` |
| planner | `planner` in `plan` | none | outcome `completed` with a nonblank plan | the plan record |
| task author | `task_author` in `tasks` | plan artifact, task identity constraints, and for a repair the current implementation task and its feedback | see [task acceptance](#task-record) | the task record |
| plan workflow | assessor, then planner | as above | as above | as above |

`concorde-context-solve` is a single Agent call of the assessor hook, `concorde-tasks` a single Agent
call of the task-author hook, and `concorde-plan` a pi workflow of the plan workflow hook.

## Before an Agent starts

Preparing a planning step runs these checks in order, in `execute` mode, and stops at the first
failure without starting a model:

1. For `concorde-plan` and `concorde-tasks`: the required Spec review check of Review; refused with
   `review_required`.
2. For `concorde-plan` and `concorde-tasks`: the pending-gap check of the step; stopped with outcome
   `spec_incomplete` and the recorded blockers.
3. For `concorde-tasks`: a managed candidate (`missing_change`), an accepted plan (`missing_plan`),
   the plan's Spec revision equal to the Module's current one (`stale_context`), and the plan's task
   and constraints equal to the request's (`incompatible_handoff`).
4. For a request whose target does not own the candidate: the component request check below.
5. For every assessor step: the collaboration pre-check. A collaboration whose explanation does not
   resolve records a gap Issue per finding and stops with `spec_incomplete`; any other structural
   finding about the Module's own relations stops with `conflicting`.

`describe-policy` stops after the checks that need no candidate and returns the intended read
policy without writing a capsule or starting an Agent.

## The plan workflow

`pi/workflows/plan.js` is the authored control flow of `concorde-plan`. Its only inputs are the
Host-issued call for the assessor and three fixed Host-step commands, each an invocation of
`pi/native-plan-host.mjs` with the step name, the path of the workflow descriptor and its digest.
Every Host step speaks the [Host-step protocol](../harness/execution/interfaces.md#contract.execution.host-step):
it prints one JSON value, at most 30000 characters, which the workflow parses.

| Step | Kind | What happens | Time limit |
| --- | --- | --- | --- |
| `bind` | Host | Waits up to 15 seconds for the workflow's launch binding, runs the Host's `check` service, which rechecks every frozen input, and preflights the assessor call | 30 s |
| `assessor` | Agent | A fresh context assessor runs; its staging gate records the proposal as staged and not accepted | the Agent's own limit |
| `advance` | Host | Runs the Host's `workflow-advance` service: verifies the assessor's native terminal records, accepts the assessment through the assessor hook, and, when it is sufficient, prepares and preflights the planner and returns `prepared` with the planner call; otherwise saves the receipt and returns the assessment | 60 s |
| `planner` | Agent | A fresh planner runs; its staging gate records the proposal | the Agent's own limit |
| `finalize` | Host | Runs the Host's `workflow-finalize` service: verifies exactly the two expected native runs, accepts the plan through the planner hook, saves it and the workflow receipt | 60 s |

**Stop conditions.** The workflow stops with a `concorde.failure` event, and accepts nothing
further, at the first Agent step that did not complete, was detached, interrupted or stopped, has
not exactly one result, exited with an error, lost its metadata, output or transcript, or whose
staging gate did not pass or reported another ticket. `advance` returning anything other than
`prepared` ends the workflow with that value. Before preparing the planner, `advance` rechecks the
assessed contracts, registry, configuration, instruction digest and candidate state against the
state recorded when the assessment was accepted, so the assessment's own recorded effects do not
count as a change.

**Result and stop.** The user session polls with `action: "result"`. The answer separates the
native state (running, complete, failed or stopped) from the Host's `accepted` flag and business
outcome. When the native run failed or was stopped before a receipt exists, the Host marks the
candidate's progress `blocked` with `execution_failed` or `execution_cancelled`, but only while the
candidate's inputs are still the ones this workflow was prepared for. A stop request marks the
workflow stopped, and every later Host step refuses with `execution_cancelled`.

## Plan record

An accepted plan's text is written to `.concorde/work/<target>/plan.md` in the candidate. The
target's entry in the change record is updated: `plan`, `spec_digest` (the Spec revision), `task`
and `constraints` (the request's), `completed_operations`, `phase: plan` and `status: active`;
`tasks` and `checks` are emptied and `implementation_digest` is cleared. A previous task list moves
to `task_history` with the reason `replan`, and any pending repair review, component coordination
and component revisions are dropped. The `plan` step's pending gaps are then updated with no
blockers.

## Task record

The task author receives the plan as `concorde-plan-artifact` and the reserved identities as
`concorde-task-identity-constraints`, even when that list is empty. The reserved identities are
every identity in the target's task history plus every identity of the current list. A scope repair
adds the current list as a `concorde-implementation-task` and a `concorde-task-scope-feedback` with
the list's digest. A review repair adds the current list and the verified review result, together
with the Issue context of the findings it cites.

The Host accepts a returned list only when it is nonempty, its identities are unique, disjoint from
the reserved ones and every task is incomplete, and every `target_id` resolves to a Module in the
target's change scope. A reserved identity is refused with `invalid_completion` naming the
colliding identities; a target outside the scope with `permission_denied`.

An accepted list replaces `tasks`. The replaced list moves to `task_history` with the reason
`review_feedback`, `implementation_boundary` (with its digest and Spec revision) or
`caller_replacement`. `checks` are emptied, `implementation_digest` is cleared and `phase` becomes
`tasks`. A review repair's reference is kept for implementation; any other replacement drops it.

A scope repair needs the exact current list: nonempty, matching the digest, not all complete, and
not combined with a review repair. Otherwise the request is refused with `incompatible_handoff`.

## Record shapes

Planning registers these typed values with Spec tooling. Each is a `{"type_id", "schema_version",
"data"}` value at version 1.

| Type | `data` |
| --- | --- |
| `concorde-plan-artifact` | `plan`: the accepted plan text |
| `concorde-task-identity-constraints` | `reserved_task_ids`: sorted unique strings |
| `concorde-task-scope-feedback` | `tasks_digest`: the SHA-256 digest of the canonical current task list; `reason`: `implementation_boundary` |

## Implementation task contract

The accepted plan and task list reach the programmer, and the component tasks reach the user session,
in one shape.

```concorde-contract
{
  "id": "contract.planning.implementation-task",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["type_id", "schema_version", "data"],
    "properties": {
      "type_id": {"const": "concorde-implementation-task"},
      "schema_version": {"const": 1},
      "data": {
        "type": "object",
        "additionalProperties": false,
        "required": ["plan", "tasks"],
        "properties": {
          "plan": {"type": "string", "minLength": 1},
          "tasks": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["id", "target_id", "description", "acceptance", "complete"],
              "properties": {
                "id": {"type": "string", "minLength": 1},
                "target_id": {"type": "string", "minLength": 1},
                "description": {"type": "string", "minLength": 1},
                "acceptance": {"type": "string", "minLength": 1},
                "complete": {"type": "boolean"}
              }
            }
          }
        }
      }
    }
  },
  "semantics": "The accepted plan of one Module and tasks of its accepted task list. Each task has a unique id within the target's task history, a target_id inside the planning Module's change scope, a description of the work, an observable acceptance condition and a completion flag that only Implementation sets. The component task of another Module is derived from the tasks that target it, in list order: each task's description, a newline, 'Acceptance: ' and its acceptance, with the tasks separated by one blank line. A request whose task equals that text, with the owner's constraints, is the component request for that Module.",
  "example": {
    "type_id": "concorde-implementation-task",
    "schema_version": 1,
    "data": {
      "plan": "Retry a card charge once after a network timeout; never after a decline.",
      "tasks": [
        {
          "id": "retry-timeout",
          "target_id": "module.billing",
          "description": "Retry a charge once after a network timeout",
          "acceptance": "A test shows one retry after a timeout and none after a card decline",
          "complete": false
        }
      ]
    }
  }
}
```

## Change scope computation

The change scope of Module M is computed from the current registry alone, one level deep:

- M itself;
- every Module M `contains` or `uses`;
- for every document M owns, every Module in its `selected-by` index;
- for every contract M defines or participates in, its owner and every Module in its
  `referenced-by` index;
- for M and every node M defines, every Module in its `referenced-by` index;
- every Module that binds a file bound by M, pending entries included.

A Module in the scope does not bring its own scope. The result is limited to registered Modules and
sorted by identity.

## Component requests

A request for Module C in a candidate whose change record names another owner is a component
request when some Module O working in the candidate has all of: an accepted plan whose Spec revision
equals O's current one; tasks naming C; C in O's change scope; a request without `focus_id`; and a
request task and constraints equal to the component task derived from O's tasks for C and O's
constraints. The request is then admitted in the candidate without taking the candidate's
ownership. Otherwise a mutating request is refused before any Agent starts or any recorded work
changes, and the user session must plan O again before retrying.

## Pending gaps

The steps are ordered `spec-review`, `context-solve`, `plan`, `tasks`, `implementation`,
`code-review`. A pending gap is recorded per change, target Module, work scope, step and Issue.
The work scope is the Module's recorded intent in the candidate (its own task, its component task,
or the task of a required review of it); a request for an unrelated task gets a scope of its own.

**Recording.** When the Host accepts a result of a step in `execute` mode, it records each of the
result's blockers as an open gap of that step, bound to the step's revision: the Module's Spec
revision, and for `implementation` and `code-review` also its implementation revision; a review
gap also keeps the review's input digest. A `context-solve` result records only when its task
matches an intent the candidate records for the Module. Recording any blocker clears the
candidate's validation evidence.

**Blocking.** Preparing `concorde-plan` (both its steps), `concorde-tasks` or `concorde-implement`
returns `spec_incomplete` with the recorded blockers, without starting a model, when an open gap of
the same step is bound to the current revision, or an open gap of any earlier step exists for the
same Module and work scope. `concorde-context-solve` and the reviews are never blocked by pending
gaps; they are how a repair is checked.

**Clearing.** An accepted result of the step without blockers resolves that step's open gaps whose
revision, or review input digest, differs from the current one; a review result without blockers
also resolves the review step's gaps that need no Spec repair. Resolving a gap never closes its
Issue.

## Requirements

### req.planning.admitted-contract — Plan only after a sufficient assessment

Planning SHALL save a plan only after a sufficient context assessment of the selected Module's current Spec for the same task.

### req.planning.assessment-context — Assess only the selected context

Planning SHALL assess a task only against the frozen context of the selected Module.

The assessor never reads implementation contents or another Module's context to fill a gap.

### req.planning.assessment-gap — Report necessary gaps as Issues

Planning SHALL accept a `spec_incomplete` assessment only when every blocker it returns cites an Issue reported during that run and names the blocked step.

### req.planning.spec-only — No implementation contents

Planning SHALL give its Agents the names of implementation files but not their contents.

### req.planning.plan-rejection-preserves — Rejected plans preserve accepted state

Planning SHALL leave the previously accepted plan and tasks unchanged when it rejects a returned plan.

### req.planning.tasks-require-plan — Tasks require a current plan

Planning SHALL refuse task authoring unless the target has an accepted plan that is current for the Module's Spec revision and the request's task and constraints.

### req.planning.tasks-admission — Accept only valid new task lists

Planning SHALL accept only nonempty task lists whose tasks are uniquely identified, initially incomplete, disjoint from the reserved identities and targeted at a Module in the selected Module's [change scope](module.md#concept.planning.change-scope).

### req.planning.task-collision-preserves — Collisions preserve history

Planning SHALL keep the prior task list and task history unchanged when it rejects a list for reusing reserved identities.

### req.planning.component-request — Only derived component requests enter another Module's candidate

Planning SHALL admit a request for a Module that does not own the candidate only as a component request, as defined under [Component requests](#component-requests).

### req.planning.pending-gap-blocks — Pending gaps stop later steps

Planning SHALL refuse to prepare a plan, task or implementation step while a pending gap blocks it, as defined under [Pending gaps](#pending-gaps).
