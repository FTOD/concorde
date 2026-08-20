---
id: contract.core.architecture-services
kind: contract
module: module.concorde.architecture-core
role: provided
flow: bidirectional
counterparties:
  - module.concorde.spec-kit-integration
  - module.concorde.documentation
representation:
  kind: custom
  format: Concorde Architecture Service Protocol
  version: "1"
  definition: specs/concorde/features/001-concorde-starter-workflow/contracts/architecture-service.schema.json
examples:
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/context-response.json
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/validation-response.json
features:
  - feature.architecture-core.manage-bounded-sources
evidence_status: verified
---

# Architecture Services Contract

## Purpose

Provide deterministic initialization, bounded context, and validation over a configured specification
hierarchy.

## Information

The custom JSON protocol passes operation, stable target, options, sorted source paths and findings,
status, summaries, proposals, bounded context, and normalized source digests. Complete field semantics
and examples are defined by the linked schema and Feature 001 contracts.

## Obligations

Results are byte-stable for unchanged inputs, paths remain project-relative, reads never mutate
sources, and writes require an accepted proposal.

## Failure Semantics

Invalid sources return `invalid`, write collisions return `conflict`, and environmental failures
return `failed`; none silently rewrite intent.

## Compatibility

Protocol v1 allows additive optional result fields. Required-field or semantic changes require a new
major protocol version and migration guidance.

## Evidence

Verified by runtime unit/contract/integration tests and zero-finding self-application to
`specs/concorde/`.
