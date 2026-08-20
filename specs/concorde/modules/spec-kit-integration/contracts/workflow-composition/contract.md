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
evidence_status: verified
---

# Workflow Composition Contract

## Purpose

Append Concorde architecture guidance to Spec Kit's normal specification, plan, and task artifacts.

## Information

The standard preset format carries template identity, source path, priority, and append strategy.

## Obligations

Composition preserves core content and one canonical feature `spec.md` while adding ownership,
contract, view, evidence, and freshness gates.

## Failure Semantics

Missing fragments or an incompatible resolver stop composition with a diagnostic.

## Compatibility

Validated against the Spec Kit 0.16.4 composition stack.

## Evidence

Verified by resolver-stack and nested module-owned workspace acceptance tests.
