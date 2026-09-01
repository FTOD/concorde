---
id: feature.workspace-files.manage-feature-workspace
kind: feature
module: module.concorde.workspace-files
refines:
  - feature.concorde.workflow
  - feature.concorde.record-workflow-reflections
  - feature.concorde.publish-project-docsite
scenarios:
  - scenario.workspace-files.manage-selected-feature
contracts:
  provided:
    - contract.workspace-files.feature-workspace
    - contract.workspace-files.records
  required: []
evidence_status: partial
canonical_design: specs/concorde/architecture/modules/workspace-files/features/001-manage-feature-workspace/design.md
---

# Manage Feature Workspace Files

**Status**: Automated behavior implemented; full installed human-journey evidence remains partial

## Outcome

A selected nested feature has one canonical durable root, one optional current `attempt/`, and one
unambiguous set of phase paths, allowing skills and scripts to preserve intent and promote an
accepted realization without duplicate memory.

## Representative Scenario

`scenario.workspace-files.manage-selected-feature` begins with Spec Kit selecting a registered
feature root. A plan skill reads `abstract.md` and `design.md`, writes `attempt/plan.md`, and leaves
the durable `implementation.md` unchanged. After tasks and checklists are complete, explicit
acceptance replaces `implementation.md` with the reviewed realization and removes that `attempt/`.

## Diagram Decision

The root [level view](../../../../diagrams/level-view.json) shows the two access paths: skills may
guide direct agent reads and writes, while scripts perform deterministic operations over the same
Workspace Files boundary. A child diagram would restate the file table in prose.

## Requirements

- A feature root MUST be registered beneath a module or parent feature and contain the canonical durable trio.
- `.specify/feature.json` MUST remain the only project selection pointer.
- Durable architecture, intent, accepted realization, and reflections MUST live outside `attempt/`.
- Current planning and delivery memory MUST live inside the selected feature's `attempt/`.
- Normal phases MUST NOT create root-level `plan.md`, `tasks.md`, checklist, or other temporal aliases.
- Generated documentation and diagrams MUST remain disposable projections.
- Acceptance MUST verify complete tasks and checklists, bind exact replacement/removal content to a digest, and require explicit approval.
- A failed resolution or acceptance MUST leave the selection, durable files, and attempt unchanged.

## Evidence

Workspace layout, nested selection, path-matrix, acceptance, reflection, and documentation source
tests cover automated behavior. Clean installed end-to-end evidence remains partial.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Canonical feature root` | The one registered directory that owns a feature's durable trio, contracts, diagrams, and optional attempt. | `is a` → `Feature workspace`; `selected by` → `Selection state` |
| `Current attempt` | The optional active temporal delivery memory belonging to one canonical feature root. | `is an` → `Attempt`; `belongs to` → `Canonical feature root` |
| `Acceptance transaction` | The digest-bound replacement of accepted realization and exact removal of a complete current attempt after approval. | `writes` → `Accepted realization`; `removes` → `Current attempt` |
