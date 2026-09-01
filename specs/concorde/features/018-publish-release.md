---
id: feature.concorde.install-with-spec-kit.publish-release
kind: feature
module: module.concorde
related_features:
  - feature.concorde.install-with-spec-kit
  - feature.distribution.package-concorde-bundle
interfaces:
  provided:
    - interface.concorde.publish-release
  required:
    - contract.concorde.spec-kit-installation
evidence_status: verified
---

# Feature Design: Publish a Concorde Release

## Outcome and Scope

A maintainer can turn a version tag and current canonical package sources into reproducible verified
archives/catalogs and publish them without mutating the checkout's installed workflow state.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.release-tooling` | Builds, verifies, and publishes allowlisted component archives/catalogs. |
| `entity.concorde.preset-package` | Supplies canonical preset archive members. |
| `entity.concorde.extension-package` | Supplies canonical extension archive members. |

## Interfaces

### `interface.concorde.publish-release` — Build and publish a tagged release

- **Consumer**: Concorde release maintainer and release automation.
- **Direction**: Version/tag/source input to archives/catalogs/publication result.
- **Entry points**: `scripts/release/build-components.py`, `verify-release.py`, and `publish-release.py`.
- **Inputs**: Matching semantic versions, repository/tag identity, download base, and canonical component/bundle sources.
- **Outputs**: Deterministic archives, updated catalogs with SHA-256/compatibility, isolated-install verification, and publication result.
- **Obligations**: Stable member ordering/metadata, exact allowlists, typed component identity, and verify before publish.
- **Failures**: Version/tag mismatch, unsafe members, digest drift, install/test failure, or remote publication conflict stops release.
- **Compatibility**: Profile 7 package manifests and Protocol 12 installed surfaces must verify together; old control-path promises are absent.
- **Implementing entities**: `entity.concorde.release-tooling`, `entity.concorde.preset-package`, `entity.concorde.extension-package`.

## Usage Scenarios

1. Build deterministic preset/extension/bundle artifacts and catalogs for a matching version tag.
2. Verify archives in clean isolated targets through installation, command composition, agent assets, and representative operations.
3. Publish only verified bytes/catalogs, or report conflicts without partially updating release state.

## Requirements

- **FR-001**: Release version, tag, manifests, bundle pin, catalogs, and archive filenames MUST agree.
- **FR-002**: Archive members/metadata/order/timestamps/permissions and catalog digests MUST be reproducible.
- **FR-003**: Verification MUST install only built artifacts in isolated targets and exercise declared Profile 7 surfaces.
- **FR-004**: Publication MUST be explicit, conflict-safe, and refuse unverified or stale artifacts.

## Edge Cases

- Rebuilding identical sources on another host must produce the same bytes.
- A remote tag/release/catalog object already exists with different content.
