---
id: contract.concorde.spec-kit-platform
kind: contract
module: module.concorde
role: required
flow: bidirectional
representation:
  kind: standard
  format: Spec Kit ecosystem contracts
  version: 0.16.4
  definition: spec-kit/docs
counterparties:
  - external.spec-kit
provider: external.spec-kit
features:
  - feature.concorde.install-starter-workflow
evidence_status: verified
---

# Spec Kit platform contract

## Purpose

Define the external capabilities Concorde requires from Spec Kit without depending on Spec Kit
implementation details.

## Information

This contract adopts the public formats and behaviors documented for Spec Kit `0.16.4`:

- bundle manifests and lifecycle operations;
- preset manifests, stacking, and runtime template resolution;
- extension manifests, commands, configuration, and hooks;
- active coding-agent integration command registration;
- project integration and installed-component provenance.

The authoritative definitions are maintained by the Spec Kit project in its bundle, preset, and
extension reference documentation.

## Preconditions

- The target is a supported Spec Kit project, or the bundle lifecycle can initialize one.
- The active agent integration can be identified before command registration.
- The source used for installation is permitted by the active catalog trust policy or supplied
  explicitly by the maintainer.

## Obligations

- Component installation and removal are scoped to the target project.
- Presets participate in the documented resolution precedence without modifying core templates.
- Extension commands are rendered into the active agent integration's supported command form.
- Bundle preview and install resolve the same component set.
- Installed-component provenance is available for safe update and removal.

## Failure Semantics

If any required capability is unavailable or incompatible, Concorde MUST stop with an actionable
diagnostic and MUST NOT claim a complete installation.

## Compatibility

The initial dependency is Spec Kit `0.16.4`. Support for additional versions is opt-in and requires
the same installation and workflow acceptance suite to pass for each advertised version.

## Evidence

The native lifecycle suite runs against Spec Kit `0.16.4` and covers catalog preview, directory,
manifest, archive, catalog-ID, and uninitialized-project installation; repeat install; compatible
update; failure recovery; provenance; shared ownership; and safe removal.
