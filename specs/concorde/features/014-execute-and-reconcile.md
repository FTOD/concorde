---
id: feature.concorde.workflow.execute-and-reconcile
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.concorde.workflow.plan-delivery
  - feature.concorde.workflow.accept-milestone
interfaces:
  provided:
    - interface.concorde.implement
  required:
    - contract.concorde.workflow
evidence_status: partial
---

# Feature Design: Execute and Reconcile

## Outcome and Scope

A coding agent executes every dependency-ready task, reconciles affected architecture/design/code/
test/projection sources, and records proportionate evidence before marking work complete.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.skills` | Defines execution authority, ordering, evidence, reflection, and halt rules. |
| `entity.concorde.workspace-resolver` | Returns the selected attempt plus protected durable/code context. |
| `entity.concorde.coding-agent` | Performs test-first implementation and task/evidence updates. |
| `entity.concorde.runtime` | Supplies deterministic validation and safe structured diagnostics. |

## Interfaces

### `interface.concorde.implement` — Execute a traced attempt

- **Consumer**: Maintainer delegating an approved dependency-ordered implementation.
- **Direction**: Complete attempt input to reconciled sources, tests, evidence, tasks, and reflections.
- **Entry points**: Leaf Skills `concorde-implement`, `concorde-analyze`, and `concorde-converge`.
- **Inputs**: Feature design, module architecture, source/tests, complete plan/tasks/checklists, and active reflection context.
- **Outputs**: Product/specification changes authorized by tasks, passing evidence in the selected stable-ID control attempt's `validation.md`, checked tasks, and appended difficult choices/problems.
- **Obligations**: Respect dependencies/file ownership, test before code where required, protect authorities, and never claim skipped/failed checks as passed.
- **Failures**: A failed blocking task or unexpected protected-source change stops dependent work and preserves truthful task state.
- **Compatibility**: Implementation updates code/spec owners directly; it never writes an accepted realization narrative.
- **Implementing entities**: `entity.concorde.skills`, `entity.concorde.workspace-resolver`, `entity.concorde.coding-agent`, `entity.concorde.runtime`.

## Usage Scenarios

1. Verify checklist/task/plan readiness and capture protected-authority digests before mutation.
2. Execute tests before corresponding code, respecting phase/task/file dependencies and parallel ownership.
3. Record compact evidence, mark only passed tasks, append difficult choices/problems, and rerun integrated gates.

## Requirements

- **FR-001**: Implementation MUST execute only dependency-ready tasks with exact trace and file authority.
- **FR-002**: Required tests MUST fail for the intended missing behavior before implementation and pass afterward where TDD applies.
- **FR-003**: Each checked task MUST have passed command/check, outcome, artifact path, trace, and limitations in attempt validation.
- **FR-004**: Unexpected protected-authority changes or blocking failures MUST stop dependents and remain truthfully unchecked/reflected.
- **FR-005**: Completion MUST reconcile every affected module architecture, feature design/interface, code, test, fixture, guide, and generated projection.

## Edge Cases

- Parallel tasks discover a shared file and must serialize without reverting either change.
- A test exists but is skipped or proves only structure; the implementation task remains incomplete.
