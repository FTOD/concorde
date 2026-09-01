---
id: contract.concorde.workflow
kind: contract
module: module.concorde
role: provided
flow: bidirectional
representation:
  kind: custom
  format: Concorde Architecture Service Protocol
  version: "1"
  definition: specs/concorde/features/001-concorde-workflow/contracts/architecture-service.schema.json
examples:
  - specs/concorde/features/001-concorde-workflow/contracts/examples/context-response.json
  - specs/concorde/features/001-concorde-workflow/contracts/examples/validation-response.json
counterparties:
  - external.maintainer
  - external.coding-agent
consumers:
  - external.maintainer
  - external.coding-agent
features:
  - feature.concorde.workflow
evidence_status: partial
---

# Concorde Workflow Contract

## Purpose

Let a maintainer and coding agent direct feature work through a recursive specification hierarchy,
architecture review, bounded implementation context, and deterministic reconciliation while the
normal Spec Kit lifecycle remains authoritative for behavioral delivery. Normal phases target one
selected root; the additive fast-loop may begin from that anchor and reconcile a bounded set of
related existing feature roots.

## Information

The deterministic Scripts boundary uses Concorde Architecture Service Protocol v1. Its
normative schema is linked in the front matter, and representative context and validation values are
maintained with Feature 001. Feature placement and selection use the separately owned
`contract.workspace-files.feature-workspace` and its Concorde Feature Workspace Protocol v9; normal
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
- Each feature-workspace lookup MUST resolve one nested canonical Spec Kit root under its providing
  module. Normal phases consume the selected lookup; fast-loop MAY repeat explicit read-only lookups
  for every semantically affected existing root without creating a second selection registry.
- That workspace MUST keep the durable trio (`abstract.md`, `design.md`, and `implementation.md`) and `contracts/` at
  its feature root and one active delivery attempt (`checklists/`, `plan.md`, `tasks.md`, research,
  data model, validation/run guides, and implementation evidence) under `attempt/`.
- A completed implementation MAY be frozen, archived, or removed after acceptance without changing
  the feature identity; root-level compatibility copies or symlinks for plan-phase files MUST NOT be
  created.
- Context MUST expose exactly the requested module level and stable navigation references, not deeper
  hidden detail.
- Architecture readiness MUST be reviewed before implementation structure is approved.
- Fast-loop MAY directly reconcile bounded cross-feature behavior, inter-module contract/data-format
  detail, maintained views, and module design-reference detail when every affected feature has an
  accepted realization and no active attempt and module responsibilities/dependency direction remain
  stable. An explicit pure naming migration MAY replace identifiers, labels, paths, and references
  across those bounded authorities when it follows existing project-level compatibility/migration
  policy, preserves implementation logic and all non-name semantics, and passes a deterministic
  stale-name/alias/duplicate inventory. Architecture-source edits MUST report exact validated diffs
  and hashes but require no separate post-edit review under constitution A.V; actual project-level
  compatibility/migration policy changes MUST return to the full workflow.
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
