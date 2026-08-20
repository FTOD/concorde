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
  definition: specs/concorde/features/001-concorde-starter-workflow/contracts/bundle-distribution.md
features:
  - feature.distribution.package-starter-bundle
evidence_status: verified
---

# Bundle Lifecycle Contract

## Purpose

Expose preview, installation, status, update, and removal of the Concorde starter bundle.

## Information

The standard format carries bundle identity, compatible versions, the expanded component plan,
catalog trust and provenance, operation status, ownership, and diagnostics.

## Obligations

Preview and apply resolve the same plan; repeats are idempotent; project sources and shared components
are preserved.

## Failure Semantics

Incompatibility or incomplete component operations return non-success and never claim a completed
bundle record. Residual state is named.

## Compatibility

This release supports Spec Kit 0.16.4 only. Expanding the range requires lifecycle acceptance.

## Evidence

Verified by `tests/concorde/integration/test_bundle_lifecycle.py` and the installed acceptance journey.
