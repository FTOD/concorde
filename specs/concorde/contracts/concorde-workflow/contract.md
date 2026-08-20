---
id: contract.concorde.starter-workflow
kind: contract
module: module.concorde
role: provided
flow: bidirectional
representation:
  kind: standard
  format: Spec Kit bundle, preset, and extension contracts
  version: 0.16.4
  definition: spec-kit/docs/community/bundles.md
counterparties:
  - external.maintainer
  - external.coding-agent
consumers:
  - external.maintainer
  - external.coding-agent
features:
  - feature.concorde.install-starter-workflow
evidence_status: verified
---

# Concorde starter workflow contract

## Purpose

Let a maintainer install, inspect, update, remove, and use Concorde through the normal Spec Kit
ecosystem and the active coding-agent integration.

## Information

This contract uses the public Spec Kit bundle, preset, extension, and agent-command formats for version
`0.16.4`. Their authoritative definitions are the Spec Kit bundle, preset, and extension references.
The exchanged information consists of component identities and versions, compatibility constraints,
install plans and results, composed templates, registered command instructions, and diagnostics.

## Obligations

- Preview MUST identify every component and version that an installation would add.
- Install MUST produce one usable Concorde preset, one usable Concorde extension, and registered
  commands for the active agent integration.
- Repeating install MUST be idempotent.
- Update MUST preserve user-authored architecture sources and report compatibility failures.
- Remove MUST remove only Concorde-owned installed components and MUST preserve user-authored sources.
- `speckit.concorde.init`, `speckit.concorde.context`, and `speckit.concorde.validate` MUST have
  portable behavior across supported agent command syntaxes.

## Failure Semantics

An incompatible Spec Kit version, unresolved component, invalid manifest, or failed command
registration MUST stop the operation with an actionable diagnostic. A failed installation MUST NOT be
reported as installed. Any residual partial state MUST be identified explicitly.

## Compatibility

The starter contract supports Spec Kit `0.16.4`. Broader version ranges require compatibility evidence
before they are advertised. Command names and architecture IDs remain stable within a Concorde major
version; incompatible changes require a major version increment and migration guidance.

## Evidence

Verified by clean-project native bundle lifecycle, update/removal, preset composition, Codex skills,
Gemini slash-command, and installed starter-journey acceptance under `tests/concorde/`.
