---
id: feature.understanding.resolve-feature-workspace
kind: feature
module: module.concorde.understanding
related_features:
  - id: feature.concorde.workflow
    relation: composed_by
  - id: feature.auto-docs.publish-project-docsite
    relation: depended_on_by
  - id: feature.reflections.record-and-triage
    relation: depended_on_by
  - id: feature.understanding.bound-planning-context
    relation: refined_by
  - id: feature.lifecycle.plan-attempt
    relation: depended_on_by
  - id: feature.capabilities.permission-bounded-execution
    relation: depended_on_by
interfaces:
  provided:
    - interface.concorde.workspace
    - contract.understanding.feature-workspace
    - contract.understanding.records
  required: []
evidence_status: partial
---

# Feature Design: Resolve Feature Workspace

## Outcome and Scope

Every Concorde phase receives one authoritative direct feature path, bounded module architecture/
ancestry, related feature paths, code/tests, `.concorde/reflections/`, and the corresponding stable-ID
control attempt. Trusted Operation code can validate those authorities, owned entity locators, exact
task tokens, and required-interface owners into concrete permission paths without granting the
untrusted agent ambient discovery.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.understanding.workspace-resolver` | Resolves selection and emits Feature Workspace Protocol 13. |
| `entity.understanding.repository-loader` | Loads module/feature identities and safe canonical paths that resolution builds on. |
| `entity.understanding.selection` | Selects the current canonical direct feature path. |
| `entity.understanding.protocol13` | Serializes one `feature_path` plus bounded durable, control, process, and executable context using Tool terminology. |
| `entity.understanding.feature-design` | Supplies sole durable behavior/interface authority. |
| `entity.understanding.module-architecture` | Supplies typed structure/relationships for the providing level. |
| `entity.concorde.specification` | Supplies direct feature files and architecture. |
| `entity.concorde.control-state` | Supplies stable-ID attempt and reflection state. |
| `entity.concorde.source-code` | Supplies only providing-module owned or explicitly task-authorized executable paths after trusted validation. |
| `entity.concorde.tests` | Supplies bounded executable evidence paths without exposing dependency-module tests to planning. |

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
- **Implementing entities**: `entity.understanding.workspace-resolver`, `entity.understanding.repository-loader`.
- **Example**: `workspace.py --phase plan --feature-path specs/example/features/001-change.md` returns `schema_version: 13` and `attempt_dir: .concorde/attempts/feature.example.change` from the file's stable ID.

### `contract.understanding.feature-workspace` — Feature Workspace Protocol 13

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
- **Implementing entities**: `entity.understanding.selection`, `entity.understanding.protocol13`,
  `entity.understanding.feature-design`, `entity.understanding.module-architecture`,
  `entity.concorde.source-code`, and `entity.concorde.tests`.
- **Example**: A plan-phase result names `feature_path: specs/example/features/001-change.md`, feature ID `feature.example.change`, its module architecture/relations, and `attempt_dir: .concorde/attempts/feature.example.change`.

### `contract.understanding.records` — Authority and lifecycle records

- **Consumer**: Skills, Operations, Runtime Tools, Auto-Docs, reflection-triage, and maintainers.
- **Direction**: Maintained/temporal/executable/installed/generated artifacts to role/lifecycle interpretation.
- **Entry points**: Profile 7 path model and validation.
- **Inputs**: Canonical architecture/direct-feature/control-attempt/reflection/code/test/installed/generated paths.
- **Outputs**: Durable/temporal/executable/installed/generated role, allowed phase effects, and freshness/ownership facts.
- **Obligations**: One source authority per fact; attempts/framework state excluded from publication; installed/generated artifacts never treated as intent.
- **Failures**: Mixed legacy layout, duplicate authority, unsafe role crossing, or stale projection yields findings.
- **Compatibility**: Module `features/` contains only direct durable files; project `.concorde/attempts/` contains only temporary stable-ID directories; code/tests replace accepted realization prose.
- **Implementing entities**: `entity.understanding.module-architecture`, `entity.understanding.feature-design`, `entity.concorde.control-state`.

## Usage Scenarios

1. Resolve specification for an existing/new direct feature and persist only its canonical file selection.
2. Resolve planning/implementation paths under a fresh or active `.concorde/attempts/<stable-feature-id>/` without specification-local compatibility copies.
3. Resolve delivery eligibility paths after tasks/checklists exist, with related summaries and module ancestry bounded.
4. Planning creates a missing control attempt for the selected stable feature ID; later phases update its
   exact files and product sources; eligible delivery removes only that attempt while the selected
   feature file, selection, architecture, and code remain.

## Related Features

- `feature.concorde.workflow` composes this feature as the shared workspace-resolution step every
  lifecycle phase runs before acting on a selected feature.
- `feature.auto-docs.publish-project-docsite` depends on this feature's records contract to distinguish
  maintained specification content from excluded control/framework state before publication.
- `feature.reflections.record-and-triage` depends on this feature for stable-ID reflection paths and
  the records contract's role boundaries when filing and triaging one problem per file.
- `feature.understanding.bound-planning-context` depends on this feature's Protocol 13 result as the
  starting point it narrows to owned and required-interface paths.
- `feature.lifecycle.plan-attempt` depends on this feature for the attempt paths its plan-authoring
  leaf is authorized to write.
- `feature.capabilities.permission-bounded-execution` depends on this feature's resolved concrete
  paths and role validation to compile enforced read/write/deny sets.

## Requirements

- **FR-001**: A valid feature MUST be one direct `<module>/features/<NNN-name>.md` file registered by
  that module, with no wrapper directory, and MUST declare exactly one providing module.
- **FR-002**: Feature Workspace Protocol 13 MUST expose only `feature_path`, module architecture/
  ancestry, related feature paths, control attempt/reflection paths, and executable-context fields,
  without unrelated bodies.
- **FR-003**: Trusted role resolution MUST derive canonical temporal/task/permission paths without
  reading other attempts or creating later-phase artifacts, and MUST reject escapes, symlinks, unknown
  tokens, and dependency internals.
- **FR-004**: Legacy trio/subfeature/contract/module-control layouts and unsafe/symlinked roots MUST
  be rejected with Profile 7 remediation.
- **FR-005**: Planned-feature resolution MUST NOT infer a stable ID from the filename and MUST rerun
  after front matter exists and before checklist creation.
- **FR-006**: A completed control attempt MUST transition to absent, when the owning lifecycle delivery
  action applies, without moving or rewriting the selected feature file or unrelated reflection
  documents.

## Edge Cases

- Selection points to a removed feature-directory path while the stable feature exists at its direct file path.
- A related-feature ID resolves to the selected feature itself or a missing feature.
- Related features form a cycle in a non-directional relationship versus a forbidden directional refinement cycle.
- The selected feature file was renamed while its stable ID remains unchanged; the same attempt must resolve.
- A stable feature ID is unsafe, duplicated, case-variant, or changed while its former attempt remains.
- A planned feature path exists only as selection and therefore cannot yet name an attempt.
