---
id: contract.skills.script-operations
kind: contract
module: module.concorde.skills
role: required
flow: bidirectional
counterparties:
  - module.concorde.scripts
representation:
  kind: custom
  format: Concorde Architecture Service Protocol
  version: "1"
  definition: specs/concorde/features/001-concorde-workflow/contracts/architecture-service.schema.json
examples:
  - specs/concorde/features/001-concorde-workflow/contracts/examples/context-response.json
  - specs/concorde/features/001-concorde-workflow/contracts/examples/validation-response.json
features:
  - feature.skills.compose-workflow
evidence_status: verified
---

# Script Operations Consumer Contract

## Purpose

Translate skill instructions into deterministic Scripts operations and present every structured
result without inventing approval or hiding findings.

## Information

Requests carry schema version, operation, target, and options. Responses carry status, artifacts,
sorted findings, and an operation-specific result; the normative schema defines every field.

## Obligations

Consumers preserve canonical JSON, show every finding, and never infer approval or stronger evidence.

## Failure Semantics

Invalid input, conflicts, and execution failures retain their protocol status and process exit.

## Compatibility

Protocol v1 permits additive optional result fields; required-field changes require a new version.

## Evidence

Verified by structured-result, example-shape, launcher, and installed command tests.
