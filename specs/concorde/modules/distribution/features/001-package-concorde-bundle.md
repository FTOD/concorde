---
id: feature.distribution.package-concorde-bundle
kind: feature
module: module.concorde.distribution
related_features:
  - feature.concorde.install-with-spec-kit
  - feature.concorde.self-host-framework
interfaces:
  provided:
    - contract.distribution.bundle-lifecycle
  required:
    - contract.distribution.component-packages
evidence_status: verified
---

# Package the Concorde Bundle

## Outcome and Scope

Spec Kit and maintainers can inspect one passive bundle recipe that pins a tested preset/extension
pair, resolve trusted archives, and safely own install/update/remove lifecycle state.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.distribution.bundle` | Pins the tested component pair and compatibility. |
| `entity.distribution.bundle-catalog` | Enables trusted bundle discovery. |
| `entity.distribution.installer` | Converts preview/apply intent into Spec Kit component lifecycle. |
| `entity.distribution.release-verifier` | Proves built artifacts in isolated targets. |

## Interfaces

### `contract.distribution.bundle-lifecycle` — Bundle preview/install/update/remove

- **Consumer**: Spec Kit and project maintainer.
- **Direction**: Bidirectional lifecycle request/result.
- **Entry points**: Spec Kit bundle operations and Concorde installer.
- **Inputs**: Bundle identity/version/source, target, lifecycle verb, trust/integration choices.
- **Outputs**: Exact component plan, versions/provenance/digests, owned changes, status, and diagnostics.
- **Obligations**: Preview/apply equivalence, idempotency, explicit update, and owned-only removal.
- **Failures**: Unresolved/incompatible/untrusted/digest-mismatched components stop without partial ownership.
- **Compatibility**: Bundle pins Profile 7 / Protocol 12-compatible preset/extension manifests.
- **Implementing entities**: `entity.distribution.bundle`, `entity.distribution.installer`, `entity.distribution.spec-kit`.
- **Example**: `concorde-bundle` resolves exactly `preset:concorde` and `extension:concorde` at the pinned version.

## Usage Scenarios

Preview expands the passive recipe, apply delegates typed components to Spec Kit, verification checks
installed winners/assets, and later remove touches only recorded ownership.

## Requirements

- **FR-001**: Bundle inspection and apply MUST resolve the same components and provenance.
- **FR-002**: Update/removal MUST preserve unrelated and user-modified paths.
- **FR-003**: Release archives MUST be reproducible and isolated-install verified.

## Edge Cases

- Preset and extension share the ID `concorde` but have distinct typed component identity.
- A local bundle bypasses bundle discovery while referenced components still require safe resolution.
