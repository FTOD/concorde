---
id: contract.concorde.spec-kit-installation
kind: contract
module: module.concorde
role: provided
flow: bidirectional
representation:
  kind: standard
  format: Spec Kit bundle, preset, extension, and catalog contracts
  version: "0.16.4"
  definition: https://github.com/github/spec-kit/tree/v0.16.4
counterparties:
  - external.maintainer
  - external.spec-kit
consumers:
  - external.maintainer
  - external.spec-kit
features:
  - feature.concorde.install-with-spec-kit
evidence_status: verified
---

# Concorde Spec Kit Installation Contract

## Purpose

Let a maintainer inspect, install, verify, update, and remove Concorde through the normal Spec Kit
ecosystem without a separate installer or a replacement feature lifecycle.

## Information

This contract adopts the public Spec Kit `0.16.4` bundle, preset, extension, catalog, provenance, and
active-integration formats. The information passed includes package identities and versions,
compatibility constraints, download locations and digests, trust policy, the expanded component plan,
preset composition settings, extension command registrations, installation results, ownership state,
and actionable diagnostics.

The bundle is a recipe that pins one independently packaged preset and extension. Catalogs advertise
those packages. Spec Kit applies the preset through template resolution and the extension through the
active coding-agent integration. None of those setup roles owns Feature 001's Concorde workflow
semantics; Architecture Core begins handling project architecture only after setup activates the
extension commands.

## Obligations

- Preview MUST identify every component and version that setup would add or change.
- Installation MUST match the accepted plan and record component provenance and ownership.
- The preset MUST append guidance without replacing core artifacts or creating a duplicate feature
  specification.
- The extension commands MUST be discoverable through the target project's active integration.
- Repeated installation MUST be idempotent.
- Update and removal MUST preserve project-authored `.concorde/` and `specs/` sources and shared
  components.

## Failure Semantics

An unsupported host version, untrusted source, invalid manifest, digest mismatch, unresolved
component, command collision, or failed registration MUST stop setup with an actionable diagnostic.
A failed installation or update MUST NOT be recorded as successful, and any residual state MUST be
reported.

## Compatibility

The initial contract supports Spec Kit `0.16.4`. Broader support requires equivalent preview,
installation, verification, update, and removal evidence before it is advertised.

## Evidence

Verified by clean-project native component lifecycle, catalog, source, manifest, archive,
idempotency, update/removal, preset-composition, Codex skills, Gemini slash-command, and installed
journey acceptance under `tests/concorde/`.
