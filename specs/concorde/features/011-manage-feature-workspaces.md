---
id: feature.concorde.workflow.manage-feature-workspaces
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
interfaces:
  provided:
    - interface.concorde.workspace
  required:
    - contract.concorde.workflow
evidence_status: partial
---

# Feature Design: Manage Feature Workspaces

## Outcome and Scope

Every normal phase receives one direct feature path, bounded module context, related feature paths,
code/tests, `.concorde/reflections/log.md`, and the corresponding stable-ID control attempt.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.workspace-resolver` | Resolves selection and emits Feature Workspace Protocol 13. |
| `entity.concorde.runtime` | Loads module/feature identities and safe canonical paths. |
| `entity.concorde.specification` | Supplies direct feature files and architecture. |
| `entity.concorde.control-state` | Supplies stable-ID attempt and reflection state. |

## Interfaces

### `interface.concorde.workspace` — Resolve selected feature phase paths

- **Consumer**: Concorde lifecycle Skills, Operation stages, and delivery Tool.
- **Direction**: Selection/phase input to structured workspace output.
- **Entry points**: `workspace.py --phase <phase>` with optional `--feature-path`.
- **Inputs**: Project root, phase, and native `.concorde/feature.json` selection or canonical direct feature file.
- **Outputs**: Protocol 13 Tool result containing identity/`feature_path`, module
  architecture/ancestry, related feature paths, stable-ID-derived attempt paths/state, reflection
  path, and executable roots; a first-pass planned feature has unavailable attempt fields.
- **Obligations**: Return only real project-contained direct features/control paths, validate stable-ID binding, require a second post-front-matter specify resolution, and never create later-phase artifacts implicitly.
- **Failures**: Invalid layout/ID, missing feature/architecture, orphan/colliding attempt, attempted orphan adoption, ambiguity, symlinks, or unsafe paths stop resolution.
- **Compatibility**: Protocol 13 removes specification-local control state while retaining `feature_path` and rejecting all earlier removed authority fields.
- **Implementing entities**: `entity.concorde.workspace-resolver`, `entity.concorde.runtime`.
- **Example**: `workspace.py --phase plan --feature-path specs/example/features/001-change.md` returns `schema_version: 13` and `attempt_dir: .concorde/attempts/feature.example.change` from the file's stable ID.

## Usage Scenarios

1. Resolve specification for an existing/new direct feature and persist only its canonical file selection.
2. Resolve planning/implementation paths under a fresh or active `.concorde/attempts/<stable-feature-id>/` without specification-local compatibility copies.
3. Resolve delivery eligibility paths after tasks/checklists exist, with related summaries and module ancestry bounded.

## Requirements

- **FR-001**: A valid feature MUST be one direct `<module>/features/<NNN-name>.md` file registered by that module, with no wrapper directory.
- **FR-002**: Protocol 13 MUST expose only `feature_path`, module architecture/ancestry, related feature paths, control attempt/reflection paths, and executable context fields.
- **FR-003**: Phase resolution MUST derive canonical temporal paths without reading other attempts or creating later artifacts.
- **FR-004**: Legacy trio/subfeature/contract/module-control layouts and unsafe/symlinked roots MUST be rejected with Profile 7 remediation.
- **FR-005**: Planned-feature resolution MUST not infer a stable ID from the filename and MUST rerun after front matter before checklist creation.

## Edge Cases

- Selection points to a removed feature-directory path while the stable feature exists at its direct file path.
- A related-feature ID resolves to the selected feature itself or a missing feature.
- An attempt stable ID has no feature, is unsafe/case-variant, or refers to an ID changed while work remains active.
