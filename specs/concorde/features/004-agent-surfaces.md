---
id: feature.concorde.maintain-agent-surfaces
kind: feature
module: module.concorde
related_features:
  - feature.skills.project-workflow
  - feature.operations.standard-development-loop
  - feature.concorde.install
interfaces:
  provided:
    - interface.concorde.agent-surfaces
  required: []
evidence_status: verified
---

# Feature Design: Maintain Checkout Agent Surfaces

## Outcome and Scope

A Concorde maintainer can check or refresh this repository's generated Codex and Claude leaf Skill,
Operation skill, and internal reflection-agent surfaces directly from canonical sources. The checkout
does not install a duplicate framework copy into itself.

## Usage

Run `python3 scripts/development/sync-agent-surfaces.py status` to inspect drift and `... apply` to
replace only the exact generated output paths. Root `skills/`, `operations/`, `agent-assets/`, and
projector code remain unchanged.

## User Scenarios & Testing

### User Story 1 — Detect Drift (Priority: P1)

**Independent Test**: Modify one generated skill, run status, and observe its exact `update` action
without source mutation.

1. **Given** current projections, **When** status runs, **Then** every action is `current`.
2. **Given** a missing, stale, or legacy symlink output, **When** status runs, **Then** it reports
   `create`, `update`, or `replace-symlink` for that exact path.

### User Story 2 — Refresh Both Integrations (Priority: P2)

**Independent Test**: Apply from drift and prove all capability/reflection-agent outputs match render results.

1. **Given** conflict-free generated paths, **When** apply runs, **Then** Codex and Claude surfaces
   become byte-current and no root source changes.

## Interfaces

### `interface.concorde.agent-surfaces` — Source-checkout projection sync

- **Consumer**: Concorde maintainer and CI.
- **Direction**: Root package sources to checkout agent projections and freshness status.
- **Entry points**: `scripts/development/sync-agent-surfaces.py status|apply [--format json]`.
- **Inputs**: Root leaf Skill sources, paired Operations, reflection assets, both integration renderers,
  and observed generated paths.
- **Outputs**: Capability-surface status schema 2 with `tool`, output count, and sorted
  action/path/digest entries; refreshed regular files on apply.
- **Obligations**: Render both integrations from the same sources, use source-checkout runtime paths, replace legacy generated symlinks, and never modify canonical inputs.
- **Failures**: Invalid Skill/Operation/asset source, missing pair, output collision, or non-file target
  conflict returns failure without a false current status.
- **Compatibility**: Package Manifest 2 uses stable `concorde-*` capability names and distinguishes
  `kind: skill` from `kind: operation`; retired dotted identities are not aliases.
- **Example**: Status reports every declared capability and internal agent projection current after apply.
- **Implementing entities**: `entity.concorde.agent-surface-sync`, `entity.concorde.skills`, `entity.concorde.agent-assets`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.concorde.skills` | Canonical leaf lifecycle prose. | Projector renders one Skill per leaf source. |
| `entity.concorde.operations` | Canonical Python/Markdown graph pairs. | Projector renders associated Markdown as a Skill and records its paired entry point. |
| `entity.concorde.agent-assets` | Canonical reflection roles/templates. | Projector renders integration-specific agents. |
| `entity.concorde.agent-surface-sync` | Checkout drift/apply driver. | Compares desired and observed bytes for both integrations. |

## Related Features

- `feature.skills.project-workflow` defines leaf and Operation skill projection semantics.
- `feature.operations.standard-development-loop` provides one paired graph projection.
- `feature.concorde.install` uses the same renderers with installed package paths for user projects.

## Requirements

- **FR-001**: Root `skills/`, `operations/`, and agent-asset sources MUST be the only projection inputs.
- **FR-002**: Status MUST classify current/create/update/replace-symlink/conflict without mutation.
- **FR-003**: Apply MUST write regular files for both integrations and remove no unrelated agent asset.
- **FR-004**: Generated skills MUST contain no unresolved package tokens or host-owned paths.
- **FR-005**: A second status after apply MUST be `current`.

## Success Criteria

- **SC-001**: Both integration projections are reproducible from root sources in one shell invocation.
- **SC-002**: No canonical package directory is duplicated beneath `.concorde` in this checkout.

## Edge Cases

- A stale generated Skill is a symlink into a removed package directory.
- A desired output path exists as a directory and therefore cannot be replaced safely.
