---
id: contract.workspace-files.records
kind: contract
module: module.concorde.workspace-files
role: provided
flow: bidirectional
counterparties:
  - module.concorde.skills
  - module.concorde.scripts
  - module.concorde.auto-docs
representation:
  kind: standard
  format: Concorde workspace file model
  version: "1"
  definition: specs/concorde/design.md
features:
  - feature.workspace-files.manage-feature-workspace
evidence_status: verified
---

# Workspace Records Contract

## Purpose

Expose the canonical roles, paths, and lifetimes of Concorde project files.

## Information

Records are classified as durable architecture, durable feature intent, durable accepted
realization, durable reflection memory, temporal attempt memory, selection state, or generated
projection.

## Obligations

Consumers preserve lifetime boundaries, follow registered nesting, and never promote temporal or
generated content implicitly.

## Failure Semantics

Missing durable roots, misplaced files, legacy aliases, and invalid promotion targets are explicit
findings.

## Compatibility

Version 1 uses `attempt/` as the only temporal workspace and `.specify/feature.json` as the single
selection pointer.

## Evidence

Covered by workspace layout, nested selection, validation, and documentation source tests.
