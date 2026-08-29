---
id: contract.scripts.workspace-files
kind: contract
module: module.concorde.scripts
role: required
flow: bidirectional
counterparties:
  - module.concorde.workspace-files
representation:
  kind: standard
  format: Concorde workspace file model
  version: "1"
  definition: specs/concorde/design.md
features:
  - feature.scripts.run-workflow-operations
evidence_status: verified
---

# Workspace Files Runtime Contract

## Purpose

Constrain every script read, proposal, validation, and approved write to a safe declared workspace
file.

## Information

The boundary carries canonical project-relative paths, source digests, file roles, and operation
results.

## Obligations

Scripts must reject unsafe or ambiguous paths, preserve unchanged files byte-for-byte, and mutate
durable files only through an explicitly accepted digest-bound operation.

## Failure Semantics

Unsafe paths, collisions, stale digests, and invalid structure return complete findings without
partial silent mutation.

## Compatibility

Version 1 matches the configured Concorde Profile 4 file hierarchy.

## Evidence

Covered by repository-safety, workspace, initialization, validation, and acceptance tests.
