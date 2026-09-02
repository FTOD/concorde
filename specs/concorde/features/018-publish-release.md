---
id: feature.concorde.release.publish
kind: feature
module: module.concorde
related_features:
  - feature.concorde.install
  - feature.distribution.package-concorde
interfaces:
  provided:
    - interface.concorde.publish-release
  required:
    - contract.concorde.installation
evidence_status: verified
---

# Feature Design: Publish a Standalone Concorde Release

## Outcome and Scope

A maintainer can build, verify, and immutably publish one Concorde archive plus one release pointer
whose version, profile/protocol, URL, digest, installed behavior, and reproducibility agree.

## Usage

Build `dist/` from `concorde.json`, verify it against the expected tag/base URL, then publish through
a draft transaction. A published identical release is a no-op; different published bytes are refused.

## User Scenarios & Testing

### User Story 1 — Build and Verify Reproducibly (Priority: P1)

**Independent Test**: Build twice and compare archive/pointer bytes after isolated native installation.

1. **Given** a valid package manifest, **When** build and verification run, **Then** the archive has one
   safe `concorde/` root and an isolated target installs successfully.
2. **Given** an unsafe member, wrong digest, mismatched tag, or non-reproducible rebuild, **When**
   verification runs, **Then** publication is blocked.

### User Story 2 — Publish Immutably (Priority: P2)

**Independent Test**: Exercise absent/draft/identical/divergent host states with a fake release host.

1. **Given** verified assets and an absent release, **When** publish runs, **Then** it creates a draft,
   uploads exactly two assets, and publishes.
2. **Given** a divergent published release, **When** publish runs, **Then** it returns divergence and
   never overwrites an asset.

## Interfaces

### `interface.concorde.publish-release` — Native release publication

- **Consumer**: Maintainer and release CI.
- **Direction**: Package source/tag to verified local assets and immutable publication record.
- **Entry points**: `scripts/release/build-release.py`, `verify-release.py`, and `publish-release.py`.
- **Inputs**: `concorde.json`, canonical allowlisted package files, version tag, release base URL, and release-host state.
- **Outputs**: `concorde-<version>.zip`, `release.json`, verification digests, notes, publication plan,
  and publication outcome.
- **Obligations**: Use one version authority; normalize archive metadata; verify safe members, identity, digest, isolated install, and byte-equivalent rebuild; publish via draft; never clobber published bytes.
- **Failures**: Identity/tag mismatch, missing/unsafe/non-installable/non-reproducible assets, host failure, or divergent published content returns a non-success outcome with residual draft state when relevant.
- **Compatibility**: Concorde 2.1.0 uses Package Manifest 2; release pointer schema 1 binds
  Architecture Profile 7, Workspace Protocol 13, and Delivery Proposal 9.
- **Example**: `python3 scripts/release/build-release.py --output dist` followed by `verify-release.py --dist dist`.
- **Implementing entities**: `entity.concorde.release-tooling`, `entity.concorde.package-manifest`, `entity.concorde.installer`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.concorde.package-manifest` | Single release identity/inventory. | Supplies version, profile, protocol, 17 leaves, three pairs, package roots, and templates. |
| `entity.concorde.release-tooling` | Build/verify/publish programs. | Produces two assets and proves installation/reproducibility. |
| `entity.concorde.installer` | Behavioral verification boundary. | Installs the extracted archive into an isolated target. |

## Related Features

- `feature.distribution.package-concorde` defines package/archive implementation details.
- `feature.concorde.install` consumes the same package contract verified before publication.

## Requirements

- **FR-001**: `concorde.json` version, tag, archive filename, embedded manifest, and pointer MUST agree.
- **FR-002**: Archive member order, timestamps, modes, paths, and content MUST be reproducible.
- **FR-003**: Verification MUST perform an isolated native Codex installation from extracted bytes,
  including all packaged leaves/exact pairs and exactly 18 public projections.
- **FR-004**: Release assets MUST be exactly one archive and one pointer.
- **FR-005**: Publication MUST never replace divergent published assets.

## Success Criteria

- **SC-001**: Two builds with the same source/base URL are byte-identical.
- **SC-002**: Release tests cover version mismatch, verification failure, absent/draft repair, identical no-op, divergence, and host failure.

## Edge Cases

- A draft exists after partial upload; the next run removes draft assets and repairs it.
- A published release has the expected tag but different archive or pointer bytes.
- A release archive installs but is not byte-reproducible from the same source/base URL.
