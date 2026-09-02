---
id: feature.concorde.workflow.plan-delivery
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.concorde.workflow.specify-behavior
  - feature.concorde.workflow.execute-and-reconcile
interfaces:
  provided:
    - interface.concorde.plan
  required:
    - contract.concorde.workflow
evidence_status: partial
---

# Feature Design: Plan Delivery

## Outcome and Scope

A maintainer can turn the selected direct feature file, bounded module architecture, current code/tests,
and known reflections into one technical plan and dependency-ordered temporal task list.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.commands` | Supplies bounded planning/task-generation gates and templates. |
| `entity.concorde.workspace-resolver` | Returns Protocol 12 durable, executable, related, and control-state paths. |
| `entity.concorde.coding-agent` | Researches decisions and authors plan/tasks without changing product authorities. |

## Interfaces

### `interface.concorde.plan` — Create an implementation attempt

- **Consumer**: Maintainer and coding agent preparing a reviewed feature change.
- **Direction**: Durable feature/architecture/code context to a separate stable-ID control plan and tasks.
- **Entry points**: `concorde.plan`, `concorde.tasks`, and optional `concorde.taskstoissues`.
- **Inputs**: `feature_path`, module ancestry, related feature paths, source/test inventory, constitution, reflections, and checklist state.
- **Outputs**: `.concorde/attempts/<stable-feature-id>/plan.md`, research/data model/quickstart, and dependency-ordered tasks with exact traces/paths.
- **Obligations**: Resolve unknowns, keep proposals temporal, map every affected authority/evidence path, and preserve durable sources during planning.
- **Failures**: Constitution violations, unresolved clarifications, missing ownership, or incomplete trace coverage prevent implementation readiness.
- **Compatibility**: Plans against code reality, never an accepted `implementation.md` baseline.
- **Implementing entities**: `entity.concorde.commands`, `entity.concorde.workspace-resolver`, `entity.concorde.coding-agent`.

## Usage Scenarios

1. Research technical unknowns against bounded architecture plus actual repository code/tests.
2. Produce data/interface delta and runnable quickstart artifacts only when useful.
3. Generate test-first, dependency-ordered, independently verifiable tasks with exact ownership/paths.

## Requirements

- **FR-001**: Planning MUST treat the direct feature file and module architecture as intent and code/tests as current realization/evidence.
- **FR-002**: Plan/research/data model/quickstart/task/checklist files MUST remain under `.concorde/attempts/<stable-feature-id>/`.
- **FR-003**: Tasks MUST cover each requirement, changed interface/entity, code/test path, projection, migration, and validation consequence.
- **FR-004**: Planning MUST preserve durable sources/code and record unresolved contradictions/compromises in `.concorde/reflections/log.md`.

## Edge Cases

- Code has an architecturally significant entity missing from architecture.
- A required interface change affects several features/modules and expands the declared task ownership set.
