---
id: feature.concorde.workflow.plan-delivery
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
  - feature.concorde.workflow.specify-behavior
  - feature.concorde.workflow.execute-and-reconcile
  - feature.operations.permission-bounded-planning
interfaces:
  provided:
    - interface.concorde.plan
  required:
    - contract.concorde.workflow
evidence_status: partial
---

# Feature Design: Plan Delivery

## Outcome and Scope

A maintainer can invoke public `concorde-plan` to resolve a read-only bounded context, then turn the
selected feature, providing architecture/owned code/tests, exact required-interface provider feature
specifications, and known reflections into one temporal plan/task list without dependency internals.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.operations` | Supplies the public context → author planner and enforced launches. |
| `entity.concorde.skills` | Supplies internal context/author leaves plus public task-generation gates/templates. |
| `entity.concorde.workspace-resolver` | Returns Protocol 13 durable, executable, related, and control-state paths. |
| `entity.concorde.coding-agent` | Researches decisions and authors plan/tasks without changing product authorities. |

## Interfaces

### `interface.concorde.plan` — Create an implementation attempt

- **Consumer**: Maintainer and coding agent preparing a reviewed feature change.
- **Direction**: Durable feature/architecture/code context to a separate stable-ID control plan and tasks.
- **Entry points**: Paired Operation `concorde-plan`, public leaf `concorde-tasks`, and optional
  `concorde-taskstoissues`.
- **Inputs**: `feature_path`, providing architecture/owned locators, module ancestry/related summaries,
  exact `interfaces.required` owner feature specs/reasons, selected attempt, constitution/reflections.
- **Outputs**: `.concorde/attempts/<stable-feature-id>/plan.md`, research/data model/quickstart, and dependency-ordered tasks with exact traces/paths.
- **Obligations**: Run read-only context before author; include dependency bodies only for unique
  required-interface ownership; deny dependency architecture/source/tests/attempts; write only the
  selected attempt/authorized reflection; map every affected authority and preserve durable bytes.
- **Failures**: Context/policy/enforcement mismatch, ambiguous provider, Constitution violation,
  unresolved clarification, missing ownership, or incomplete trace coverage stops authorship.
- **Compatibility**: `concorde-plan` keeps its public name but is a paired Operation in 2.1.0; no leaf alias remains.
- **Implementing entities**: `module.concorde.operations`, `entity.concorde.skills`,
  `entity.concorde.workspace-resolver`, and `entity.concorde.coding-agent`.

## Usage Scenarios

1. Resolve context and research unknowns against providing architecture/owned code/tests and exact published dependency feature promises.
2. Produce data/interface delta and runnable quickstart artifacts only when useful.
3. Generate test-first, dependency-ordered, independently verifiable tasks with exact ownership/paths.

## Requirements

- **FR-001**: Planning MUST treat the direct feature file and module architecture as intent and code/tests as current realization/evidence.
- **FR-002**: Plan/research/data model/quickstart/task/checklist files MUST remain under `.concorde/attempts/<stable-feature-id>/`.
- **FR-003**: Tasks MUST cover each requirement, changed interface/entity, code/test path, projection, migration, and validation consequence.
- **FR-004**: Planning MUST preserve durable sources/code and record unresolved contradictions/compromises in `.concorde/reflections/log.md`.
- **FR-005**: Context MUST precede author, carry required-interface reasons, exclude provider
  internals/other attempts, and compile author writes to only selected attempt/reflections.

## Edge Cases

- Code has an architecturally significant entity missing from architecture.
- A required interface change affects several features/modules and expands the declared task ownership set.
- An incidental related feature remains a summary and never grants body access.
