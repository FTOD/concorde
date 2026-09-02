---
id: feature.skills.compose-workflow
kind: feature
module: module.concorde.skills
related_features:
  - feature.concorde.workflow
  - feature.concorde.record-workflow-reflections
  - feature.concorde.install-with-spec-kit
  - feature.concorde.self-host-framework
interfaces:
  provided:
    - contract.skills.workflow-guidance
    - contract.skills.agent-surface
    - contract.distribution.component-packages
  required:
    - contract.concorde.spec-kit-platform
    - contract.scripts.operations
    - contract.workspace-files.feature-workspace
    - contract.workspace-files.records
evidence_status: verified
---

# Compose Workflow Skills

## Outcome and Scope

Spec Kit can compose canonical Concorde commands/templates into platform-appropriate installed skills
whose phase paths, authorities, deterministic crossings, and failure behavior remain equivalent.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.skills.preset-manifest` | Declares composition strategy, commands, and templates. |
| `entity.skills.phase-commands` | Define normal/additive phase behavior. |
| `entity.skills.extension-commands` | Define Concorde-specific operation behavior. |
| `entity.skills.spec-kit-composer` | Resolves layers and materializes the selected integration. |

## Interfaces

### `contract.skills.workflow-guidance` — Canonical phase intent

- **Consumer**: Spec Kit composer and supported coding agents.
- **Direction**: Canonical command/template sources to composed executable instructions.
- **Entry points**: Preset command/template contributions.
- **Inputs**: Phase user input, Protocol 12 workspace, Constitution, and relevant stable-ID control attempt sources.
- **Outputs**: Exact read/write/script/evidence/reflection behavior for each phase, including
  deterministic reflection-ID allocation and eligible merged-small removal.
- **Obligations**: Preserve authority boundaries, bounded reads, trace/evidence rules, high-water ID
  retirement, automatic small-merge closure, retained-route maintainer disposition, and non-mutating failures across integrations.
- **Failures**: Missing composition inputs or incompatible hooks stop the phase with instructions/source state preserved.
- **Compatibility**: Profile 7 contains four templates and no abstract/implementation/specification-control creation; reflection-triage/v3 governs reflection allocation/removal.
- **Implementing entities**: `entity.skills.preset-manifest`, `entity.skills.phase-commands`.

### `contract.skills.agent-surface` — Installed operation surface

- **Consumer**: Maintainer invoking Codex, Claude, or supported slash-command integrations.
- **Direction**: Composed intent to discoverable installed skill/command files.
- **Entry points**: Integration-specific skill/command registries.
- **Inputs**: Canonical preset/extension winners and active integration.
- **Outputs**: Complete named operation inventory with matching descriptions and bytes.
- **Obligations**: Generated ownership/digests, no hidden duplicate command intent, and preservation of unrelated/inactive state.
- **Failures**: Collision, stale bytes, or unsupported projection is reported and rolled back by installation/self-hosting.
- **Compatibility**: Operation names remain stable while their Profile 7 control-state semantics replace the old profile.
- **Implementing entities**: `entity.skills.spec-kit-composer`, `entity.skills.phase-commands`, `entity.skills.extension-commands`.

### `contract.distribution.component-packages` — Canonical component package inputs

- **Consumer**: Distribution archive builder, catalogs, installer, and Spec Kit.
- **Direction**: Canonical preset/extension source to versioned component manifest/archive.
- **Entry points**: `presets/concorde/preset.yml` and `extensions/concorde/extension.yml` plus their allowlisted files.
- **Inputs**: Component ID/kind/version/compatibility and declared templates/commands/scripts/assets.
- **Outputs**: Independently valid preset/extension packages suitable for bundle pinning and reproducible release.
- **Obligations**: Every declared file resolves, package identity stays kind-qualified, and canonical sources contain no installed-only state.
- **Failures**: Invalid manifest, missing/undeclared source, incompatible host range, or stale composition prevents packaging.
- **Compatibility**: Profile 7 preset has four templates; extension exposes Protocol 12,
  Initialization 2, Delivery 8, and reflection-triage/v3 semantics.
- **Implementing entities**: `entity.skills.preset-manifest`, `entity.skills.extension-commands`.
- **Example**: Distribution packages `preset:concorde` and `extension:concorde` independently before the bundle pins their tested versions.

### `contract.concorde.spec-kit-platform` — Required command/template composer

- **Provider**: `external:specify-cli==0.16.4`.
- **Consumer**: Canonical Concorde preset and extension command/template sources.
- **Direction**: Layered sources and integration state to installed composed operation surfaces.
- **Entry points**: Spec Kit preset/template resolver and extension command installer.
- **Inputs**: Base layers, Concorde strategies/sources, active integration, project registry, and phase selection.
- **Outputs**: Winning template/command bytes, registries, provenance, and lifecycle diagnostics.
- **Obligations**: Deterministic composition, declared strategy semantics, and restoration/removal of lower layers.
- **Failures**: Missing inputs, incompatible versions, or path collisions reject composition without hidden partial winners.
- **Compatibility**: Concorde's manifest range is `>=0.16.4,<0.16.5`.
- **Implementing entities**: `entity.skills.spec-kit-composer`.
- **Example**: A `replace` command layer supplies the complete Protocol 12 workspace gate before the phase workflow body.

## Usage Scenarios

Install the preset and extension into a clean fixture, inspect every generated skill, run workspace
routing, and verify that all platforms name only architecture/design/code/test/attempt authorities.

## Requirements

- **FR-001**: Every canonical phase MUST resolve Protocol 12 before reading or writing phase artifacts.
- **FR-002**: Canonical and installed operation intent MUST remain byte/provenance verifiable.
- **FR-003**: Removed Profile 4 artifact names MUST NOT appear as current authorities.
- **FR-004**: Every installed phase that records a new reflection MUST allocate its ID through the
  tracked high-water helper, and every installed triage merge MUST remove an eligible merged-small
  entry while retaining all other routes for maintainer disposition.

## Edge Cases

- A lower preset layer reappears after update/removal.
- The active integration changes while inactive generated surfaces must remain preserved.
