```concorde-document
{
  "id": "document.planning.tasks",
  "owner": "module.planning",
  "main_visible": true
}
```

# Task authoring capability

## Usage & Contract

The [common invocation envelope](../development/interfaces.md#capability-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/review-and-gaps.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a private, bound capability in the [current adapter inventory](../development/capabilities.md).
Only a declared in-process composition can call it; direct Skill/CLI invocation is rejected.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`tasks` requires a current managed change and accepted nonempty plan. Missing state is
missing_change; an absent plan is missing_plan. A fresh task author invocation receives
concorde-plan-artifact@1 and concorde-task-identity-constraints@1, even when the reservation list
is empty. Optional prior tasks and semantic scope/review feedback require explicit repair admission.
The [transport shapes](../spec/values.md#task-authoring-transport-values) are canonical there.

Task acceptance describes software behavior and implementation evidence within the programmer's
granted files and runtime. Host production/scaffold/export validation, independent reviews,
readiness, commit and delivery remain later responsibilities. Tasks support those checks through
implementation and tests; they never require the later steps to have finished first. Full software
acceptance stays in the plan and tasks, and all configured validation and required reviews still run.

Every fresh task author receives `concorde-task-identity-constraints@1` with a sorted, unique
`reserved_task_ids` list: all IDs from that target's retained task history, plus the current list
when scope or code-review repair replaces it. This input is required even when empty and survives
replanning through the retained history. It reserves identities without adding historical software
obligations. The Host rejects a collision with the specific IDs before accepting the new list;
it never rewrites author output or clears history to admit it.


The result is a nonempty list of internally unique, initially incomplete tasks, disjoint from
reserved IDs, each carrying id, target_id, description, acceptance and complete. The host accepts
and persists the list as a concorde-implementation-task@1 with its plan; it returns artifact
references through concorde-tasks-response@1. The author cannot complete tasks or mutate project files.

For scope recovery it receives the plan, prior list, reserved IDs and the fixed
implementation_boundary feedback, preserving software acceptance. A semantic change requiring a
new plan returns conflicting or a gap. Failed, malformed or colliding output never replaces the
old list or discards history. For review repair, only verified current blocking code feedback may
be supplied. The current adapter admits that feedback through dev-loop's bounded repair policy;
this is an adapter restriction, not permission for a new caller to invent a repair transition.
The caller owns ordering and invalidation, while this provider owns admissible input and new tasks.

### Requirements

#### req.planning.tasks-require-plan — Tasks require an accepted current plan

Planning SHALL reject task authoring without an accepted current plan.

#### req.planning.tasks-admission — Accept only valid new task lists

Planning SHALL accept only nonempty, internally unique, initially incomplete task lists whose IDs are disjoint from the admitted reserved IDs.

#### req.planning.task-collision-preserves — Identity collisions preserve task history

Planning SHALL preserve the prior task list and retained history when it rejects colliding task IDs.


### Scenarios

#### scenario.planning.tasks-from-plan — Accepted plan yields implementation tasks

- GIVEN a current managed change, accepted plan and complete reserved task-ID input
- WHEN a fresh task author returns a nonempty, internally unique, initially incomplete acceptance-task list disjoint from the reserved IDs
- THEN the host accepts and persists the list with its plan as the implementation task artifact
- AND its response supplies artifact references without completing tasks or granting the author project writes

#### scenario.planning.tasks-missing-plan — Task authoring has no prerequisite plan

- GIVEN a current managed change with no authored plan for the selected target
- WHEN a declared composing caller requests task authoring
- THEN the host rejects the request with missing_plan before launching a task author
- AND it does not create a task list or discard retained task history

#### scenario.planning.tasks-id-conflict — New output reuses a reserved identity

- GIVEN an accepted plan, prior tasks and retained history with IDs reserved for a fresh task author
- WHEN the returned task list reuses an admitted reserved ID
- THEN the host rejects the list and reports the conflicting IDs without rewriting author output
- AND the prior task list and retained history remain unchanged
