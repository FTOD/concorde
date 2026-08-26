---
id: contract.distribution.bundle-lifecycle
kind: contract
module: module.concorde.distribution
role: provided
flow: bidirectional
counterparties:
  - external.maintainer
  - external.spec-kit
representation:
  kind: standard
  format: Spec Kit bundle lifecycle
  version: "0.16.4"
  definition: specs/concorde/features/003-install-concorde-speckit/contracts/bundle-distribution.md
features:
  - feature.distribution.package-concorde-bundle
evidence_status: partial
---

# Bundle Lifecycle Contract

## Purpose

Expose preview, installation, status, update, and removal of the Concorde bundle.

## Information

The standard format carries bundle identity, compatible versions, the expanded component plan,
catalog trust and provenance, operation status, ownership, and diagnostics.

## Obligations

Preview and apply resolve the same plan; repeats are idempotent; project sources and shared components
are preserved. Verification executes the installed winning command surfaces in a clean target rather
than accepting archive membership or matching text as workflow evidence.

## Failure Semantics

Incompatibility or incomplete component operations return non-success and never claim a completed
bundle record. Residual state is named.

## Compatibility

This release supports Spec Kit 0.16.4 only. Expanding the range requires lifecycle acceptance.

## Evidence

Package lifecycle behavior is verified by `tests/concorde/integration/test_bundle_lifecycle.py`.
Evidence remains partial until the installed acceptance journey covers the complete normal-command
phase matrix, all Concorde-specific commands, checkout isolation, and preset recomposition.
