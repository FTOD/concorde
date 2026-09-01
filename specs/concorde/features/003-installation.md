---
id: feature.concorde.install-with-spec-kit
kind: feature
module: module.concorde
related_features:
  - feature.concorde.install-with-spec-kit.publish-release
  - feature.concorde.install-with-spec-kit.one-command-install
  - feature.distribution.package-concorde-bundle
interfaces:
  provided:
    - contract.concorde.spec-kit-installation
  required:
    - contract.concorde.spec-kit-platform
evidence_status: partial
---

# Feature Design: Install and Set Up Concorde with Spec Kit

## Outcome and Scope

A maintainer can inspect, install, update, and remove one supported Concorde bundle whose preset,
extension, agent projections, compatibility, provenance, and ownership are explicit and verified.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.distribution` | Packages/catalogs the tested bundle and verifies release/installation behavior. |
| `entity.concorde.installer` | Drives preview/apply/update/remove against a target. |
| `entity.concorde.spec-kit` | Resolves/materializes components and owns installed lifecycle state. |

## Interfaces

### `contract.concorde.spec-kit-installation` — Concorde bundle lifecycle

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Bundle/target/lifecycle request to preview/applied/unchanged/removed structured result.
- **Entry points**: One-command installer and standard Spec Kit bundle/component lifecycle.
- **Inputs**: Target, supported bundle/version/catalog, integration, preview/apply/update/remove intent, and trust policy.
- **Outputs**: Exact component/agent-asset plan, versions/provenance/digests, ownership records, verification, and diagnostics.
- **Obligations**: Resolve compatible trusted artifacts, preview before mutation, preserve unrelated/user files, and roll back failed owned writes.
- **Failures**: Missing/incompatible/untrusted artifacts, digest mismatch, composition conflict, or installed-surface verification failure leaves actionable state.
- **Compatibility**: Bundle pins one Profile 7 preset/extension pair tested with Spec Kit 0.16.4.
- **Implementing entities**: `module.concorde.distribution`, `entity.concorde.installer`, `entity.concorde.spec-kit`.
- **Example**: Preview lists `preset:concorde` and `extension:concorde`; apply materializes both plus supported active-integration agent assets.

### `contract.concorde.spec-kit-platform` — Required component host

- **Provider**: `external:specify-cli==0.16.4`.
- **Consumer**: Concorde installer, bundle lifecycle, and self-hosting transaction.
- **Direction**: Component/catalog/bundle requests to previewed/applied ownership state.
- **Entry points**: Native Spec Kit catalog, bundle, preset, and extension operations.
- **Inputs**: Target project, trusted sources, kind-qualified component IDs, versions, integration, and lifecycle verb.
- **Outputs**: Exact plan, registry/ownership updates, installed files, unchanged/failure state, and diagnostics.
- **Obligations**: Preview/apply consistency, compatible source resolution, typed identity, rollback, and owned-only update/removal.
- **Failures**: Trust/compatibility/collision/materialization errors preserve unrelated and prior valid state.
- **Compatibility**: Required range is `>=0.16.4,<0.16.5`.
- **Implementing entities**: `entity.concorde.spec-kit`.
- **Example**: Applying the bundle delegates `preset:concorde` and `extension:concorde` to their native component handlers.

## Usage Scenarios

1. Inspect a catalog/bundle and preview exact component/projection ownership before mutation.
2. Install into a clean or existing project, verify winning command/template/runtime surfaces, and report unchanged idempotent repeats.
3. Explicitly update or remove only recorded ownership while preserving lower layers and user changes.

## Requirements

- **FR-001**: The bundle MUST pin exactly one compatible `preset:concorde` and `extension:concorde` version pair.
- **FR-002**: Catalog/archive trust, compatibility, URL, digest, and typed identity MUST be inspectable before apply.
- **FR-003**: Preview/apply MUST resolve the same plan; failed apply MUST roll back owned writes.
- **FR-004**: Installed Profile 7 commands/templates/runtime/agent assets MUST be verified from a clean target.
- **FR-005**: Update/removal MUST preserve unrelated, inactive-integration, lower-layer, and user-modified paths.

## Edge Cases

- The same string ID names a preset and extension, so every operation must retain component kind.
- A local bundle is trusted directly but references a component that cannot resolve from allowed catalogs.
