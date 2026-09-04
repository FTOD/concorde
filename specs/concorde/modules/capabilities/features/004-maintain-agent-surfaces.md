---
id: feature.capabilities.maintain-agent-surfaces
kind: feature
module: module.concorde.capabilities
related_features:
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
  - id: feature.lifecycle.standard-development-loop
    relation: relates_to
  - id: feature.distribution.install-concorde
    relation: relates_to
interfaces:
  provided:
    - interface.concorde.agent-surfaces
  required: []
---

# Feature Design: Maintain Checkout Agent Surfaces

## Outcome and Scope

A Concorde maintainer can check or refresh this repository's generated Codex and Claude public-leaf,
Operation, and internal reflection-agent surfaces directly from canonical sources while both internal
planner leaves remain package-only. The checkout does not install a duplicate framework copy into
itself.

## Usage

Run `python3 scripts/development/sync-agent-surfaces.py status` to inspect drift and `... apply` to
replace only the exact generated output paths. Root `skills/`, `operations/`, `agent-assets/`, and
projector code remain unchanged.

## Interfaces

### `interface.concorde.agent-surfaces` — Source-checkout projection sync

- **Consumer**: Concorde maintainer and CI.
- **Direction**: Root package sources to checkout agent projections and freshness status.
- **Entry points**: `scripts/development/sync-agent-surfaces.py status|apply [--format json]`.
- **Inputs**: Root 17-leaf sources with exposure/effects, three paired Operations, reflection assets,
  both integration renderers, and observed generated paths.
- **Outputs**: Capability-surface status schema 2 with `tool`, output count, and sorted
  action/path/digest entries; refreshed regular files on apply.
- **Obligations**: Render both integrations from the same sources, filter internal leaves, preserve
  target→kind ownership (including plan Skill→Operation transition), use checkout runtime paths,
  replace legacy generated symlinks, and never modify canonical inputs.
- **Failures**: Invalid Skill/Operation/asset source, missing pair, output collision, or non-file
  target conflict returns failure without a false current status.
- **Compatibility**: Package Manifest 2 uses stable `concorde-*` capability names and distinguishes
  `kind: skill` from `kind: operation`; retired dotted identities are not aliases.
- **Example**: Status reports 40 outputs: 18 public capabilities per integration plus four specialist
  agents.
- **Implementing entities**: `entity.capabilities.checkout-sync`, `entity.capabilities.skill-sources`,
  `entity.capabilities.operation-sources`, and `module.concorde.reflections`.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.capabilities.skill-sources` | Canonical public/internal leaf lifecycle prose and effects. |
| `entity.capabilities.operation-sources` | Canonical Python/Markdown graph pairs. |
| `entity.capabilities.checkout-sync` | Checkout drift/apply driver comparing desired and observed bytes for both integrations. |
| `entity.capabilities.projector` | Renders only public leaf and Operation sources into integration-native Skill files. |
| `module.concorde.reflections` | Supplies canonical reflection investigator/implementer roles and templates the projector renders as integration-specific agents. |

## Related Features

- `feature.capabilities.provide-capability-surfaces` defines leaf and Operation skill projection
  semantics that this checkout sync reuses.
- `feature.lifecycle.standard-development-loop` provides one paired graph whose projection this sync
  verifies.
- `feature.distribution.install-concorde` uses the same renderers with installed package paths for
  user projects.

## User Scenarios & Testing

### User Story 1 — Detect Drift (Priority: P1)

**Independent Test**: Modify one generated skill, run status, and observe its exact `update` action
without source mutation.

1. **Given** current projections, **When** status runs, **Then** every action is `current`.
2. **Given** a missing, stale, or legacy symlink output, **When** status runs, **Then** it reports
   `create`, `update`, or `replace-symlink` for that exact path.

### User Story 2 — Refresh Both Integrations (Priority: P2)

**Independent Test**: Apply from drift and prove all capability/reflection-agent outputs match render
results.

1. **Given** conflict-free generated paths, **When** apply runs, **Then** Codex and Claude surfaces
   become byte-current and no root source changes.

## Requirements

- **FR-001**: Root `skills/`, `operations/`, and agent-asset sources MUST be the only projection inputs.
- **FR-002**: Status MUST classify current/create/update/replace-symlink/conflict without mutation.
- **FR-003**: Apply MUST write regular files for both integrations and remove no unrelated agent asset.
- **FR-004**: Generated skills MUST contain no unresolved package tokens or host-owned paths.
- **FR-005**: A second status after apply MUST be `current`.
- **FR-006**: Internal leaves MUST have no desired output and the public `concorde-plan` target MUST
  carry `kind: operation`/entry-point provenance in both integrations.

## Success Criteria

- **SC-001**: Both integration projections are reproducible from root sources in one shell invocation.
- **SC-002**: No canonical package directory is duplicated beneath `.concorde` in this checkout.
- **SC-003**: Each integration has exactly 18 public capabilities; total maintained checkout output is 40.

## Edge Cases

- A stale generated Skill is a symlink into a removed package directory.
- A desired output path exists as a directory and therefore cannot be replaced safely.
