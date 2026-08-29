---
id: contract.distribution.component-packages
kind: contract
module: module.concorde.distribution
role: required
flow: input
counterparties:
  - module.concorde.spec-kit-integration
representation:
  kind: standard
  format: Spec Kit preset and extension packages
  version: "0.16.4"
  definition: https://github.com/github/spec-kit/tree/v0.16.4
features:
  - feature.distribution.package-concorde-bundle
evidence_status: verified
---

# Component Packages Contract

## Purpose

Receive independently valid Concorde preset and extension packages for bundle composition.

## Information

The standard manifests exchange stable identity, semantic version, compatibility, files, commands,
templates, and dependencies.

## Obligations

Every declared file resolves and component metadata agrees with its catalog and archive.

## Failure Semantics

An invalid, unavailable, or mismatched component prevents bundle installation.

## Compatibility

The initial consumer profile is Spec Kit 0.16.4.

## Evidence

Verified by manifest installation, archive reproducibility, catalog parity, and release digest tests.
