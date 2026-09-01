---
id: feature.workspace-files.manage-feature-workspace
kind: feature
module: module.concorde.workspace-files
related_features:
  - feature.concorde.workflow
  - feature.concorde.record-workflow-reflections
  - feature.concorde.publish-project-docsite
interfaces:
  provided:
    - contract.workspace-files.feature-workspace
    - contract.workspace-files.records
  required: []
evidence_status: partial
---

# Manage Feature Workspace Files

## Outcome and Scope

Every host phase receives one authoritative direct feature file with its module architecture/
ancestry, related summaries, stable-ID project-control attempt, reflection log, and executable roots.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.workspace.selection` | Selects the current canonical direct feature path. |
| `entity.workspace.feature-design` | Supplies sole durable behavior/interface authority. |
| `entity.workspace.module-architecture` | Supplies typed structure/relationships for the providing level. |
| `entity.workspace.attempt` | Holds one phase's plan/tasks/checklists/evidence under `.concorde/attempts/<stable-feature-id>/` while active. |
| `entity.workspace.protocol12` | Serializes one `feature_path` plus bounded durable, control, process, and executable context. |

## Interfaces

### `contract.workspace-files.feature-workspace` — Feature Workspace Protocol 12

- **Consumer**: Every normal Spec Kit/Concorde phase and delivery.
- **Direction**: Project/phase/selection input to canonical path/context JSON.
- **Entry points**: Installed `workspace.py` adapter and runtime resolver.
- **Inputs**: Project root, phase, and explicit or selected `feature_path`.
- **Outputs**: Feature/module identity, direct feature path, architecture/ancestry, related feature paths, stable-ID attempt paths/state, `.concorde/reflections/log.md`, and source/test roots; planned features expose unavailable attempt fields until their ID exists.
- **Obligations**: Resolve only real project-contained direct features and control paths, bind attempts by validated stable ID, bound relation bodies, rerun after new front matter, and never create future artifacts implicitly.
- **Failures**: Missing/legacy/ambiguous/unsafe/symlinked features or control roots, malformed IDs, orphan/colliding attempts, or attempted orphan adoption stop resolution.
- **Compatibility**: `schema_version: 12`; module-local attempts, specification-root reflections, `feature_directory`, `feature_design`, and all earlier removed authority fields are forbidden.
- **Implementing entities**: `entity.workspace.selection`, `entity.workspace.protocol12`, `entity.workspace.feature-design`, `entity.workspace.module-architecture`.
- **Example**: A plan-phase result names `feature_path: specs/example/features/001-change.md`, feature ID `feature.example.change`, its module architecture/relations, and `attempt_dir: .concorde/attempts/feature.example.change`.

### `contract.workspace-files.records` — Authority and lifecycle records

- **Consumer**: Skills, runtime, Auto-Docs, reflection triage, and maintainers.
- **Direction**: Maintained/temporal/executable/generated artifacts to role/lifecycle interpretation.
- **Entry points**: Profile 7 path model and validation.
- **Inputs**: Canonical architecture/direct-feature/control-attempt/reflection/code/test/projection paths.
- **Outputs**: Durable/temporal/executable/generated role, allowed phase effects, and freshness/ownership facts.
- **Obligations**: One source authority per fact; attempts excluded from publication; generated artifacts never treated as intent.
- **Failures**: Mixed legacy layout, duplicate authority, unsafe role crossing, or stale projection yields findings.
- **Compatibility**: Module `features/` contains only direct durable files; project `.concorde/attempts/` contains only temporary stable-ID directories; code/tests replace accepted realization prose.
- **Implementing entities**: `entity.workspace.module-architecture`, `entity.workspace.feature-design`, `entity.workspace.attempt`, `entity.workspace.reflections`.

## Usage Scenarios

Planning creates a missing control attempt for the selected stable feature ID, later phases update its
exact files and product sources, and eligible delivery removes only that attempt while the selected
feature file, selection, architecture, and code remain.

## Requirements

- **FR-001**: Every feature MUST have one canonical direct `feature_path`, one providing module, and no wrapper directory.
- **FR-002**: Protocol 12 MUST expose bounded ancestry/relations, a stable-ID-derived attempt path, and the centralized reflection path without unrelated feature bodies.
- **FR-003**: Delivery MUST transition one complete control attempt to absent without moving or rewriting the feature file or reflection log.
- **FR-004**: A not-yet-authored feature MUST receive unavailable attempt fields until valid stable-ID front matter exists and the specify gate reruns.

## Edge Cases

- The selected feature file was renamed while its stable ID remains unchanged; the same attempt must resolve.
- Related features form a cycle in a non-directional relationship versus a forbidden directional refinement cycle.
- A stable feature ID is unsafe, duplicated, case-variant, or changed while its former attempt remains.
- A planned feature path exists only as selection and therefore cannot yet name an attempt.
