---
id: feature.workspace.manage-feature-workspace
kind: feature
module: module.concorde.workspace
related_features:
  - feature.concorde.workflow
  - feature.concorde.record-workflow-reflections
  - feature.concorde.publish-project-docsite
  - feature.operations.permission-bounded-planning
interfaces:
  provided:
    - contract.workspace.feature-workspace
    - contract.workspace.records
  required: []
evidence_status: partial
---

# Manage Feature Workspace Files

## Outcome and Scope

Every Concorde phase receives one authoritative direct feature with module architecture/ancestry,
related summaries, stable-ID attempt, per-file reflection collection, and executable roots. Trusted Operation code
can validate those authorities, owned entity locators, exact task tokens, and required-interface
owners into concrete permission paths without granting the untrusted agent ambient discovery.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.workspace.selection` | Selects the current canonical direct feature path. |
| `entity.workspace.feature-design` | Supplies sole durable behavior/interface authority. |
| `entity.workspace.module-architecture` | Supplies typed structure/relationships for the providing level. |
| `entity.workspace.attempt` | Holds one phase's plan/tasks/checklists/evidence under `.concorde/attempts/<stable-feature-id>/` while active. |
| `entity.workspace.protocol13` | Serializes one `feature_path` plus bounded durable, control, process, and executable context using Tool terminology. |
| `entity.workspace.source-code` | Supplies only providing-module owned or explicitly task-authorized executable paths after trusted validation. |
| `entity.workspace.tests` | Supplies bounded executable evidence paths without exposing dependency-module tests to planning. |

## Interfaces

### `contract.workspace.feature-workspace` — Feature Workspace Protocol 13

- **Consumer**: Every path-sensitive Concorde leaf Skill, Operation stage, and delivery Tool.
- **Direction**: Project/phase/selection input to canonical path/context JSON.
- **Entry points**: Installed `workspace.py` adapter and runtime resolver.
- **Inputs**: Project root, phase, and explicit or selected `feature_path`.
- **Outputs**: Feature/module identity, direct feature path, architecture/ancestry, related summaries,
  stable-ID attempt paths/state, `.concorde/reflections/`, and source/test roots; trusted helpers
  may derive concrete task/control roles and Operations may add exact required-interface owner specs.
- **Obligations**: Resolve only real project-contained direct features/control paths, bind attempts by
  validated stable ID, keep relation bodies bounded, validate concrete roles without symlinks/escapes,
  rerun after new front matter, and never let an agent resolve or create future authority implicitly.
- **Failures**: Missing/legacy/ambiguous/unsafe/symlinked features or control roots, malformed IDs, orphan/colliding attempts, or attempted orphan adoption stop resolution.
- **Compatibility**: `schema_version: 13`; the result envelope uses `tool`; module-local attempts,
  specification-root reflections, `feature_directory`, `feature_design`, and all earlier removed
  authority fields are forbidden.
- **Implementing entities**: `entity.workspace.selection`, `entity.workspace.protocol13`,
  `entity.workspace.feature-design`, `entity.workspace.module-architecture`,
  `entity.workspace.source-code`, and `entity.workspace.tests`.
- **Example**: A plan-phase result names `feature_path: specs/example/features/001-change.md`, feature ID `feature.example.change`, its module architecture/relations, and `attempt_dir: .concorde/attempts/feature.example.change`.

### `contract.workspace.records` — Authority and lifecycle records

- **Consumer**: Skills, Operations, Runtime Tools, Auto-Docs, reflection-triage/v5, and maintainers.
- **Direction**: Maintained/temporal/executable/generated artifacts to role/lifecycle interpretation.
- **Entry points**: Profile 7 path model and validation.
- **Inputs**: Canonical architecture/direct-feature/control-attempt/reflection/code/test/installed/generated paths.
- **Outputs**: Durable/temporal/executable/installed/generated role, allowed phase effects, and freshness/ownership facts.
- **Obligations**: One source authority per fact; attempts/framework state excluded from publication; installed/generated artifacts never treated as intent.
- **Failures**: Mixed legacy layout, duplicate authority, unsafe role crossing, or stale projection yields findings.
- **Compatibility**: Module `features/` contains only direct durable files; project `.concorde/attempts/` contains only temporary stable-ID directories; code/tests replace accepted realization prose.
- **Implementing entities**: `entity.workspace.module-architecture`, `entity.workspace.feature-design`, `entity.workspace.attempt`, `entity.workspace.reflections`.

## Usage Scenarios

Planning creates a missing control attempt for the selected stable feature ID, later phases update its
exact files and product sources, and eligible delivery removes only that attempt while the selected
feature file, selection, architecture, and code remain.

## Requirements

- **FR-001**: Every feature MUST have one canonical direct `feature_path`, one providing module, and no wrapper directory.
- **FR-002**: Protocol 13 MUST expose bounded ancestry/relations, stable-ID attempt/reflection paths,
  and executable hints without unrelated bodies; trusted role resolution MUST reject escapes,
  symlinks, unknown tokens, dependency internals, and every other attempt.
- **FR-003**: Delivery Proposal 9 MUST transition one complete control attempt to absent without moving
  or rewriting the feature file or unrelated reflection documents.
- **FR-004**: A not-yet-authored feature MUST receive unavailable attempt fields until valid stable-ID front matter exists and the specify gate reruns.

## Edge Cases

- The selected feature file was renamed while its stable ID remains unchanged; the same attempt must resolve.
- Related features form a cycle in a non-directional relationship versus a forbidden directional refinement cycle.
- A stable feature ID is unsafe, duplicated, case-variant, or changed while its former attempt remains.
- A planned feature path exists only as selection and therefore cannot yet name an attempt.
- One related provider owns several interfaces; the permission context includes its feature body once
  with every exact required-interface reason and excludes its architecture/source/tests.
