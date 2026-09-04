---
id: feature.lifecycle.execute-and-reconcile
kind: feature
module: module.concorde.lifecycle
related_features:
  - id: feature.concorde.workflow
    relation: composed_by
  - id: feature.lifecycle.plan-attempt
    relation: depends_on
  - id: feature.lifecycle.deliver-attempt
    relation: depended_on_by
interfaces:
  provided:
    - interface.concorde.implement
  required: []
---

# Feature Design: Execute and Reconcile

## Outcome and Scope

A coding agent executes every dependency-ready task, reconciles affected architecture/design/code/
test/projection sources, and records proportionate evidence before marking work complete.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.lifecycle.implement-skill` | Defines execution authority, ordering, evidence, reflection, and halt rules. |
| `entity.lifecycle.analyze-skill` | Reports plan/task/checklist and architecture consistency without mutation. |
| `entity.lifecycle.converge-skill` | Appends remaining verified work discovered during implementation to the active task list. |
| `module.concorde.understanding` | Returns the selected attempt plus protected durable/code context and deterministic validation results. |
| `entity.concorde.coding-agent` | Performs test-first implementation and task/evidence updates. |
| `entity.lifecycle.attempt` | Holds the tasks, checklists, and per-task validation evidence this phase reads and updates. |

## Interfaces

### `interface.concorde.implement` — Execute a traced attempt

- **Consumer**: Maintainer delegating an approved dependency-ordered implementation.
- **Direction**: Complete attempt input to reconciled sources, tests, evidence, tasks, and reflections.
- **Entry points**: Leaf Skills `concorde-implement`, `concorde-analyze`, and `concorde-converge`.
- **Inputs**: Feature design, module architecture, source/tests, complete plan/tasks/checklists, and active reflection context.
- **Outputs**: Product/specification changes authorized by tasks; checked tasks; appended difficult
  choices/problems; and one delivery-readable block per task in the selected stable-ID attempt's
  `validation.md`, beginning with a top-level `- **T### · <trace>**` boundary and containing a nested
  `- **Outcome**: passed|failed|skipped` field.
- **Obligations**: Respect dependencies/file ownership, test before code where required, protect
  authorities, keep each evidence boundary on one complete top-level line, record Check/Evidence/
  Scope/Limitation fields inside that task's block, and never claim skipped/failed checks as passed.
- **Failures**: A failed blocking task or unexpected protected-source change stops dependent work and preserves truthful task state.
- **Compatibility**: Implementation updates code/spec owners directly; it never writes an accepted realization narrative.
- **Implementing entities**: `entity.lifecycle.implement-skill`, `entity.lifecycle.analyze-skill`,
  `entity.lifecycle.converge-skill`, `module.concorde.understanding`, `entity.concorde.coding-agent`.

## Related Features

- `feature.concorde.workflow` is the root umbrella feature this phase realizes as its central
  reconciliation stage.
- `feature.lifecycle.plan-attempt` supplies the complete plan and dependency-ordered tasks this phase
  executes.
- `feature.lifecycle.deliver-attempt` consumes this phase's completed tasks and recorded evidence to
  become eligible for cleanup-only delivery.

## Usage Scenarios

1. Verify checklist/task/plan readiness and capture protected-authority digests before mutation.
2. Execute tests before corresponding code, respecting phase/task/file dependencies and parallel ownership.
3. Record each compact evidence block in the canonical top-level boundary/nested Outcome grammar,
   mark only tasks whose current block says `**Outcome**: passed`, append difficult choices/problems,
   and rerun integrated gates.

## Requirements

- **FR-001**: Implementation MUST execute only dependency-ready tasks with exact trace and file authority.
- **FR-002**: Required tests MUST fail for the intended missing behavior before implementation and pass afterward where TDD applies.
- **FR-003**: Each checked task MUST have one current attempt-validation block whose top-level line is
  exactly `- **T### · <trace>**`, whose nested fields include an exact
  `- **Outcome**: passed` plus Check/Evidence/Scope/Limitation, and whose task ID matches the checked
  task; `failed` and `skipped` outcomes MUST remain unchecked.
- **FR-004**: Unexpected protected-authority changes or blocking failures MUST stop dependents and remain truthfully unchecked/reflected.
- **FR-005**: Completion MUST reconcile every affected module architecture, feature design/interface, code, test, fixture, guide, and generated projection.

## Edge Cases

- Parallel tasks discover a shared file and must serialize without reverting either change.
- A test exists but is skipped or proves only structure; the implementation task remains incomplete.
