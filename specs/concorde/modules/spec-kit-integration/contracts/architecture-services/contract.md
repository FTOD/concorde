---
id: contract.integration.architecture-services
kind: contract
module: module.concorde.spec-kit-integration
role: required
flow: bidirectional
counterparties:
  - module.concorde.architecture-core
representation:
  kind: custom
  format: Concorde Architecture Service Protocol
  version: "1"
  definition: specs/concorde/features/001-concorde-starter-workflow/contracts/architecture-service.schema.json
examples:
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/context-response.json
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/validation-response.json
features:
  - feature.integration.compose-starter-workflow
evidence_status: verified
---

# Architecture Services Consumer Contract

## Purpose

Translate agent requests to deterministic Architecture Core operations.

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
