---
id: feature.concorde.maintain-agent-surfaces
kind: feature
module: module.concorde
related_features:
  - feature.commands.project-workflow
  - feature.concorde.install
interfaces:
  provided:
    - interface.concorde.agent-surfaces
  required: []
evidence_status: verified
---

# Feature Design: Maintain Checkout Agent Surfaces

## Outcome and Scope

A Concorde maintainer can check or refresh this repository's generated Codex and Claude command and
reflection surfaces directly from root canonical sources. The checkout does not install a duplicate
framework copy into itself.

## Usage

Run `python3 scripts/development/sync-agent-surfaces.py status` to inspect drift and `... apply` to
replace only the exact generated output paths. Root `commands/`, `agent-assets/`, and projector code
remain unchanged.

## User Scenarios & Testing

### User Story 1 — Detect Drift (Priority: P1)

**Independent Test**: Modify one generated skill, run status, and observe its exact `update` action
without source mutation.

1. **Given** current projections, **When** status runs, **Then** every action is `current`.
2. **Given** a missing, stale, or legacy symlink output, **When** status runs, **Then** it reports
   `create`, `update`, or `replace-symlink` for that exact path.

### User Story 2 — Refresh Both Integrations (Priority: P2)

**Independent Test**: Apply from drift and prove all command/reflection outputs match render results.

1. **Given** conflict-free generated paths, **When** apply runs, **Then** Codex and Claude surfaces
   become byte-current and no root source changes.

## Interfaces

### `interface.concorde.agent-surfaces` — Source-checkout projection sync

- **Consumer**: Concorde maintainer and CI.
- **Direction**: Root package sources to checkout agent projections and freshness status.
- **Entry points**: `scripts/development/sync-agent-surfaces.py status|apply [--format json]`.
- **Inputs**: Root command sources, reflection assets, both integration renderers, and observed generated paths.
- **Outputs**: Schema 1 status, output count, and sorted action/path/digest entries; refreshed regular files on apply.
- **Obligations**: Render both integrations from the same sources, use source-checkout runtime paths, replace legacy generated symlinks, and never modify canonical inputs.
- **Failures**: Invalid command/asset source, output collision, or non-file target conflict returns failure without a false current status.
- **Compatibility**: All canonical `concorde.*` command IDs remain stable while rendered
  `concorde-*` skill metadata names Concorde ownership.
- **Example**: Status reports 38 current outputs after an apply.
- **Implementing entities**: `entity.concorde.agent-surface-sync`, `entity.concorde.commands`, `entity.concorde.agent-assets`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.concorde.commands` | Canonical lifecycle prose. | Projector renders one skill per file. |
| `entity.concorde.agent-assets` | Canonical reflection roles/templates. | Projector renders integration-specific agents. |
| `entity.concorde.agent-surface-sync` | Checkout drift/apply driver. | Compares desired and observed bytes for both integrations. |

## Related Features

- `feature.commands.project-workflow` defines projection and command semantics.
- `feature.concorde.install` uses the same renderers with installed package paths for user projects.

## Requirements

- **FR-001**: Root command and agent-asset sources MUST be the only projection inputs.
- **FR-002**: Status MUST classify current/create/update/replace-symlink/conflict without mutation.
- **FR-003**: Apply MUST write regular files for both integrations and remove no unrelated agent asset.
- **FR-004**: Generated skills MUST contain no unresolved package tokens or host-owned paths.
- **FR-005**: A second status after apply MUST be `current`.

## Success Criteria

- **SC-001**: Both integration projections are reproducible from root sources in one command.
- **SC-002**: No canonical package directory is duplicated beneath `.concorde` in this checkout.

## Edge Cases

- A legacy generated command is a symlink into a removed package directory.
- A desired output path exists as a directory and therefore cannot be replaced safely.
