---
id: contract.integration.workflow-composition
kind: contract
module: module.concorde.spec-kit-integration
role: provided
flow: output
counterparties:
  - external.spec-kit
representation:
  kind: standard
  format: Spec Kit preset template composition
  version: "0.16.4"
  definition: https://github.com/github/spec-kit/blob/v0.16.4/presets/ARCHITECTURE.md
features:
  - feature.integration.compose-starter-workflow
  - feature.integration.manage-feature-workspace
evidence_status: partial
---

# Workflow Composition Contract

## Purpose

Append Concorde architecture guidance to Spec Kit's normal lifecycle and preserve the selected
feature's durable/temporal path boundary.

## Information

The standard preset format carries template identity, source path, priority, and append strategy.

## Obligations

Composition preserves core phase semantics and one canonical root `spec.md` while adding ownership,
contract, view, evidence, and freshness gates. Installed phase adapters resolve planning and delivery
artifacts below `implementation/` and never create root aliases.

## Failure Semantics

Missing fragments or an incompatible resolver stop composition with a diagnostic.

## Compatibility

Validated against the Spec Kit 0.16.4 composition stack.

## Evidence

Append-only templates are verified by resolver-stack tests. Evidence remains partial until public
preset command composition delivers the complete phase path matrix in clean installed projects.
