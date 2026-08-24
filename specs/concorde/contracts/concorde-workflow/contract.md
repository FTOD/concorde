---
id: contract.concorde.core-workflow
kind: contract
module: module.concorde
role: provided
flow: bidirectional
representation:
  kind: custom
  format: Concorde Architecture Service Protocol
  version: "1"
  definition: specs/concorde/features/001-concorde-starter-workflow/contracts/architecture-service.schema.json
examples:
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/context-response.json
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/validation-response.json
counterparties:
  - external.maintainer
  - external.coding-agent
consumers:
  - external.maintainer
  - external.coding-agent
features:
  - feature.concorde.core-workflow
evidence_status: partial
---

# Concorde Core Workflow Contract

## Purpose

Let a maintainer and coding agent direct one feature through a recursive specification hierarchy,
architecture review, bounded implementation context, and deterministic reconciliation while the
normal Spec Kit lifecycle remains authoritative for behavioral delivery.

## Information

The deterministic Architecture Core boundary uses Concorde Architecture Service Protocol v1. Its
normative schema is linked in the front matter, and representative context and validation values are
maintained with Feature 001. Feature placement and selection use the separately owned
`contract.integration.feature-workspace` and its Concorde Feature Workspace Protocol v2; normal
behavioral phases retain Spec Kit's standard contracts. Together these boundaries pass:

- the requested operation and stable module, feature, or project-relative target;
- options controlling proposal/application or bounded output;
- the operation status and sorted maintained source paths;
- proposed changes, bounded current-level context, or deterministic validation findings;
- source digests and explicit evidence state needed for review.

Complete workspace fields are normative in the Feature Workspace schema. Architecture Service v1's
common envelope is normative in its linked schema; operation-specific result shapes must be tightened
without changing existing operation meaning as part of this implementation. Active coding-agent
presentation never changes either contract.

## Obligations

- Initialization MUST separate a reviewable proposal from explicit accepted application.
- Feature work MUST resolve one nested canonical Spec Kit workspace under its providing module.
- That workspace MUST keep durable intent (`spec.md`, `contracts/`, and `checklists/`) at its feature
  root and one active delivery attempt (`plan.md`, `tasks.md`, research, data model, validation/run
  guides, and implementation evidence) under `implementation/`.
- A completed implementation MAY be frozen, archived, or removed after acceptance without changing
  the feature identity; root-level compatibility copies or symlinks for plan-phase files MUST NOT be
  created.
- Context MUST expose exactly the requested module level and stable navigation references, not deeper
  hidden detail.
- Architecture readiness MUST be reviewed before implementation structure is approved.
- Validation MUST be deterministic, read-only, and explicit about unknown or conflicting evidence.
- Generated read models MUST preserve provenance and MUST NOT become maintained intent.

## Failure Semantics

Unknown or duplicated targets, unsafe paths, invalid sources, unresolved contracts, hierarchy cycles,
stale projections, or changed proposal targets produce structured findings and do not silently mutate
maintained intent. Unsupported yet-required operations report the capability gap and its temporary
supported path rather than pretending completion.

## Compatibility

Each custom protocol v1 permits additive optional fields within its boundary. Removing a required
field, changing its meaning, or changing stable command intent requires a new major protocol version
and migration guidance. Normal Spec Kit artifact meanings remain governed by the supported Spec Kit
version.

## Evidence

Initialization, context, and validation are verified by runtime unit, contract, integration, and
self-application tests. Nested feature creation and selection remain planned, so the overall contract
evidence is `partial`.
