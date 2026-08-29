---
id: contract.skills.workspace-files
kind: contract
module: module.concorde.skills
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
  - feature.skills.compose-workflow
evidence_status: verified
---

# Workspace Files Consumer Contract

## Purpose

Require every skill to name the durable or temporal files it may read and write.

## Information

The boundary carries selected workspace paths, file lifetime, phase ownership, and promotion rules.

## Obligations

Skills must not create root-level aliases, treat `attempt/` content as accepted intent, or treat
generated views as maintained sources.

## Failure Semantics

An unresolved, unsafe, unregistered, or lifetime-incompatible path stops the phase with an
actionable finding.

## Compatibility

Version 1 uses the durable, temporal, selection, and generated classes defined at the root.

## Evidence

Covered by installed command-surface and feature-workspace path-matrix tests.
