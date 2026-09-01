---
id: feature.concorde.install-with-spec-kit.one-command-install
kind: feature
module: module.concorde
related_features:
  - feature.concorde.install-with-spec-kit
  - feature.distribution.package-concorde-bundle
interfaces:
  provided:
    - interface.concorde.one-command-install
  required:
    - contract.concorde.spec-kit-installation
evidence_status: unknown
---

# Feature Design: One-Command Installation

## Outcome and Scope

A maintainer can install the supported Concorde bundle into a target project with one command and
receive a usable verified Profile 7 workflow or an unchanged target with actionable diagnostics.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.installer` | Resolves the bundle/catalog and delegates component lifecycle to Spec Kit. |
| `entity.concorde.preset-package` | Provides feature/plan/task templates and normal phase commands. |
| `entity.concorde.extension-package` | Provides operations, runtime, launchers, and agent assets. |
| `entity.concorde.spec-kit` | Owns preview, materialization, registry, update, and removal. |

## Interfaces

### `interface.concorde.one-command-install` — Install the supported bundle

- **Consumer**: Project maintainer starting or upgrading a Concorde-enabled project.
- **Direction**: Installer arguments to preview/applied/unchanged/failure result.
- **Entry points**: `scripts/install-concorde.py` through the documented `uvx` invocation.
- **Inputs**: Target root, bundle/version or trusted catalog input, integration choice, and preview/apply intent.
- **Outputs**: Exact component/projection plan, ownership records, verified installed surfaces, and diagnostics.
- **Obligations**: Preview before apply, resolve only trusted compatible components, use Spec Kit ownership, and preserve user/unrelated paths.
- **Failures**: Trust, compatibility, integrity, composition, projection, or verification errors roll back owned changes.
- **Compatibility**: Installs Profile 7/Protocol 12/Initialization 2/Delivery 8 sources as one tested bundle.
- **Implementing entities**: `entity.concorde.installer`, `entity.concorde.preset-package`, `entity.concorde.extension-package`, `entity.concorde.spec-kit`.

## Usage Scenarios

1. Install from public catalog into an empty/initialized target with one documented command.
2. Use development/local sources while still exercising native Spec Kit preview/apply/ownership.
3. Repeat, update, or remove safely and verify the exact active/inactive integration surfaces.

## Requirements

- **FR-001**: One invocation MUST sequence project readiness, trusted catalogs, bundle preview/apply, agent-asset sync, and verification.
- **FR-002**: The installer MUST be idempotent and distinguish unchanged, applied, rejected, and failed outcomes.
- **FR-003**: Local development mode MUST not bypass component validation, composition, ownership, or rollback rules.
- **FR-004**: Failures MUST name the stage/finding/remediation and preserve unrelated/user state.

## Edge Cases

- Target is initialized but has conflicting lower-layer command winners.
- Network catalog/archive resolution fails after preview but before apply.
