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
  - feature.concorde.self-host-framework
evidence_status: partial
---

# Concorde Spec Kit Installation Contract

## Purpose

Let a maintainer inspect, install, verify, update, and remove Concorde through the normal Spec Kit
ecosystem without a separate installer or replacement feature lifecycle, including installing and
refreshing the current trusted Concorde sources in the Concorde development checkout itself.

## Information

This contract adopts the public Spec Kit `0.16.4` bundle, preset, extension, catalog, provenance, and
active-integration formats. The information passed includes package identities and versions,
compatibility constraints, download locations and digests, trust policy, the expanded component plan,
preset template and command composition settings, resolved normal-command layers, extension command
registrations, materialized agent presentations, installation results, ownership state, and
actionable diagnostics.

The bundle is a recipe that pins one independently packaged preset and extension. Catalogs advertise
those packages. Spec Kit applies the preset through template and command resolution, materializes the
winning normal-command layers, and registers the extension's Concorde-specific commands through the
active coding-agent integration. None of those setup roles owns Feature 001's Concorde workflow
semantics; Architecture Core begins handling project architecture only after setup activates the
installed command surfaces.

For development self-hosting, the accepted local preset, extension, and bundle source state replaces
a published archive as the expected component input. The same component roles, compatibility,
preview, ownership, and active-integration obligations continue to apply. Project-local installed
copies remain replaceable materializations and cannot become release or source authority.

## Obligations

- Preview MUST identify every component and version that setup would add or change.
- Installation MUST match the accepted plan and record component provenance and ownership.
- The preset MUST compose guidance and authoritative selected-workspace routing into the nine
  affected normal lifecycle commands without replacing phase semantics or creating a duplicate
  feature specification.
- The extension's five Concorde-specific surfaces MUST be discoverable through the target project's
  active integration. Four use supporting adapters or runtime; the read-only `ask` procedure MUST
  materialize without a launcher or runtime verb.
- Clean-project verification MUST execute the winning installed command surfaces with the source
  checkout unavailable and prove the durable/temporal path matrix across skills and slash-command
  presentations.
- Preset disable and priority change MUST preserve registered command artifacts according to Spec Kit
  0.16.4 while changing future resolution; update/removal MUST materialize the accepted or next
  surviving normal-command layer without stale Concorde instructions.
- Repeated installation MUST be idempotent.
- Update and removal MUST preserve project-authored `.concorde/` and `specs/` sources and shared
  components.
- Development self-hosting MUST preview and bind the accepted local source state, preserve all
  project-authored content and unrelated agent assets, and report whether an agent reload or new
  session is required before refreshed instructions are active.
- A read-only self-hosting check MUST report source, materialization, registration, compatibility,
  and activation disagreements without claiming that file equality proves the running agent loaded
  the current instructions.

## Failure Semantics

An unsupported host version, untrusted source, invalid manifest, digest mismatch, unresolved
component, command collision, ambiguous or unsafe command composition, or failed materialization MUST
stop setup with an actionable diagnostic.
A failed installation or update MUST NOT be recorded as successful, and any residual state MUST be
reported.

## Compatibility

The initial contract supports Spec Kit `0.16.4`. Broader support requires equivalent preview,
installation, verification, update, and removal evidence before it is advertised.

## Evidence

Bundle lifecycle, catalog, source, manifest, archive, idempotency, update/removal, and basic command
registration are verified under `tests/concorde/`. Evidence remains partial until clean release
installation executes all nine normal and four runtime-backed Concorde winning surfaces and reviews
the installed `ask` procedure in both supported presentation styles, with checkout isolation and
lower-layer restoration.
