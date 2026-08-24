# Phase 1 Data Model: Concorde Core Workflow

**Feature**: `feature.concorde.core-workflow`  
**Date**: 2026-08-23

This is the technical model for the active implementation attempt. Durable semantics remain in
`spec.md`, `design.md`, module/contract Markdown, Archify JSON, and the referenced contract representations.

## Relationship Summary

```text
Specification Package
└── Root Module
    ├── Contract *
    ├── Feature * ── Feature Design (1) ── Feature Workspace ── Implementation Workspace (0..1 active)
    │             └── Feature Diagram *
    ├── Immediate Module * ── repeats Specification Package
    └── Architecture View (required when non-leaf)

Feature ── owned by exactly one Module
Feature ── refines Feature at adjacent parent level (0..*)
Feature ── illustrated by Scenario (1..*)
Scenario Interaction ── governed by Contract when it crosses a boundary
Feature Selection ── points to exactly one Feature Workspace
Hardening Proposal ── promotes one completed Implementation Workspace into Feature Design
Workflow Distribution Handoff ── exposes Feature Selection + phase paths to Feature 003
Architecture Readiness Review ── gates plan approval for one Feature/source digest
Bounded Context ── projection of Feature + one Module level + relevant Contracts/Evidence
Validation Finding ── reports disagreement without changing any authority
```

## 1. Specification Package

The configured recursive source subtree for one Concorde project.

| Field | Type | Rules |
|---|---|---|
| `profile_version` | integer | Required; initially `1`. Unsupported versions fail. |
| `specification_root` | safe project-relative path | Required; no absolute path, traversal, backslash, empty segment, or symlink escape. |
| `root_module_id` | stable ID | Resolves exactly once to the package root. |
| `source_digest` | `sha256:<hex>` | Deterministic digest of maintained source bytes and relative paths. |

The package discovers module Markdown, contract Markdown and representations, feature-root
`spec.md`, paired `design.md`, and declared Archify JSON. Files below `implementation/` are addressable for active feature
context but are not parsed as durable architecture entities merely because they live under `specs/`.

## 2. Module

An architecturally meaningful ownership and boundary unit.

| Field | Type | Rules |
|---|---|---|
| `id` | stable ID | Globally unique module ID. |
| `parent` | module ID or null | Exactly one parent except the root. |
| `responsibility` | Markdown section | One clear responsibility. |
| `boundary` | Markdown section | Defines owned and excluded concerns. |
| `children` | module ID list | Immediate children only; containment is acyclic. |
| `features` | feature ID list | Current-level owned features only. |
| `contracts.provided` | contract ID list | Explicit, possibly empty. |
| `contracts.required` | contract ID list | Explicit, possibly empty. |
| `view` | safe path or null | Exactly one maintained view for a non-leaf; optional for a leaf. |

## 3. Feature

Durable observable behavior at one abstraction level.

| Field | Type | Rules |
|---|---|---|
| `id` | stable ID | Globally unique feature ID. |
| `module` | module ID | Exactly one providing module. |
| `outcome` | Markdown text | Primary behavioral meaning. |
| `refines` | feature ID list | Adjacent parent level only; graph is acyclic. |
| `scenarios` | scenario ID list | Representative, non-exhaustive; normally at least one. |
| `contracts.provided` | contract ID list | At least one. |
| `contracts.required` | contract ID list | Explicit, possibly empty. |
| `evidence_status` | enum | `unknown`, `partial`, `verified`, or `disagrees`. |
| `canonical_spec` | safe path | Exactly `<workspace>/spec.md` and resolves to this document. |
| `diagrams` | Feature Diagram reference list | Optional for a simple feature with rationale; a cross-component feature has one core architecture diagram or an explicit sufficiency rationale. |

A lower-level feature without a parent refinement must be marked internal with a non-empty rationale.

### 3a. Feature Design

The permanent accepted account of how related modules, lower-level features, contracts, and
implementation decisions realize one Feature without redefining module architecture.

| Field | Type | Rules |
|---|---|---|
| `path` | safe path | Exactly `<feature-workspace>/design.md`; required with `spec.md`. |
| `feature_id` | derived stable ID | Agrees with the paired feature specification. |
| `realization_overview` | Markdown | Concise accepted implementation shape. |
| `module_feature_collaboration` | Markdown | Uses maintained module/feature IDs and contracts without replacing architecture authority. |
| `scenario_realization` | Markdown | Explains how representative scenarios are achieved. |
| `durable_decisions` | Markdown | Retains accepted decisions, not transient task ordering or discarded alternatives. |
| `traceability_evidence` | Markdown | References reviewable code, tests, contracts, and generated evidence. |
| `known_limitations` | Markdown | States remaining accepted limits; no unresolved proposal placeholders. |

Normal specify, plan, tasks, implement, analyze, and converge operations may read this baseline but
must never update it. Only approved Feature Hardening may replace it.

## 4. Feature Workspace

The single nested location selected for the normal lifecycle.

| Field | Type | Rules |
|---|---|---|
| `root` | safe project-relative directory | `<module-package>/features/<number-name>/`. |
| `specification` | path | Exactly `<root>/spec.md`; required after specify. |
| `design` | path | Exactly `<root>/design.md`; required after specify and paired with the specification. |
| `contracts` | directory | Optional durable feature-level representations at `<root>/contracts/`. |
| `diagrams` | path list | Optional descriptively named Archify JSON under `diagrams/`; never named `architecture.json`. |
| `implementation` | directory or null | Exactly `<root>/implementation/` when an attempt exists. |
| `module_id` | stable ID | Must agree with the spec and containing module. |
| `feature_id` | stable ID | Must agree with the spec and module registration. |

Root `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, or delivery evidence are
invalid. Compatibility copies and symlinks are not allowed.

## 5. Implementation Workspace

One temporal delivery attempt for a durable feature.

| Field | Type | Rules |
|---|---|---|
| `root` | path | Exactly `<feature-root>/implementation/`. |
| `plan` | path | `plan.md`; required for task generation. |
| `tasks` | path | `tasks.md`; required for implementation. |
| `research` | path | Optional Phase 0 decisions. |
| `data_model` | path | Optional Phase 1 technical model. |
| `quickstart` | path | Optional runnable acceptance guide. |
| `validation` | path | Optional evidence record. |
| `checklists` | directory | Optional requirements-quality review state at `checklists/`; every checklist is temporal and blocks hardening while any item is unresolved. |
| `lifecycle` | derived/recorded enum | `absent`, `active`, `task-complete`, or `hardened`; `hardened` means the directory is absent after promotion. |

The first release permits at most one `active` directory. Task completion makes the attempt eligible
for hardening but is not user approval. Successful hardening removes the complete directory; history
belongs to version control and durable design/evidence references, not an archived attempt below the feature.

```text
absent -> active -> task-complete -> hardened (implementation/ absent)
             \-> active when any task remains incomplete
hardened -> active (a later implementation attempt, with design as baseline)
```

## 6. Feature Placement Proposal

A reviewable description of where a new feature belongs before maintained intent changes.

| Field | Type | Rules |
|---|---|---|
| `providing_module` | module ID | Required and uniquely resolved. |
| `feature_id` | stable ID | Proposed unique identity. |
| `short_name` | string | Safe normalized directory suffix. |
| `number` | string | Deterministically selected or explicitly supplied. |
| `workspace_root` | safe path | Derived from providing-module path and number/name. |
| `canonical_spec` | safe path | `<workspace_root>/spec.md`. |
| `module_changes` | ordered change list | Feature registration and any required contract references. |
| `view_changes` | ordered change list | Current-level scenario/connection changes, or explicit none. |
| `conflicts` | ordered conflict list | Existing path, duplicate ID, unsafe path, or stale target. |
| `source_digest` | digest | Binds approval to the inspected hierarchy. |

### Placement states

```text
requested -> proposed -> approved -> specified -> selected
     |          |           |
     +------> invalid    conflict
```

Approval is explicit. If source bytes change after proposal, application returns `conflict` and a
new proposal is required.

### 6a. Feature Hardening Proposal

A reviewable, digest-bound promotion of one task-complete attempt into permanent Feature Design.

| Field | Type | Rules |
|---|---|---|
| `proposal_version` | integer | Exactly `1` for the initial proposal representation. |
| `operation` | string | Exactly `feature.harden`. |
| `target` | stable feature ID | Resolves exactly to the selected Feature Workspace. |
| `source_digest` | digest | Covers the current design, maintained inputs, and attempt, excluding the proposal file itself. |
| `design.path` | safe path | Exactly the selected root `design.md`. |
| `design.content` | Markdown string | Complete candidate with every required Feature Design section. |
| `remove` | one-item path list | Exactly the selected feature's `implementation/` directory. |

Apply rechecks task completion and source digest. It stages the new design, renames the prior design
and attempt to bounded recovery paths, commits the design, then removes recovery artifacts. Any
commit failure restores both prior authorities.

## 7. Architecture Readiness Review

A deterministic review record that gates architecture-ready plan approval without replacing the plan.

| Field | Type | Rules |
|---|---|---|
| `feature_id` | stable ID | Exactly the active Feature. |
| `providing_module` | module ID | Agrees with Feature ownership and placement. |
| `abstraction_level` | module path/ID | Explicitly reviewed. |
| `participating_children` | module ID list | Immediate children only. |
| `refinements` | feature edge list | Adjacent and acyclic. |
| `contract_crossings` | interaction/contract list | Every boundary crossing resolved. |
| `dependency_direction` | ordered edge list | Uses visible participants and declared contracts. |
| `affected_views` | safe path list | Current-level views requiring change or explicit empty list. |
| `expected_evidence` | Evidence Reference list | Implementation, test, validation, and generated expectations. |
| `source_digest` | digest | Binds the result to reviewed durable sources. |
| `status` | enum | `incomplete`, `ready`, or `stale`. |
| `approval` | reviewer reference or null | Required before an AI-authored structural change becomes accepted. |

Missing required information yields `incomplete` with findings. Changed durable bytes make a prior
result `stale`; they do not silently preserve readiness.

## 8. Feature Selection

The ephemeral project context used by subsequent Spec Kit phases.

| Field | Type | Rules |
|---|---|---|
| `feature_directory` | safe project-relative directory | Points to one existing Feature Workspace root. |
| `source` | enum | `explicit-override` or `persisted-selection`. |
| `feature_spec` | derived path | `<feature_directory>/spec.md`. |
| `feature_design` | derived path | `<feature_directory>/design.md`. |
| `implementation_dir` | derived path | `<feature_directory>/implementation/`. |
| `checklists`, `plan`, `tasks`, `research`, `data_model`, `quickstart` | derived paths | Always below `implementation_dir`; checklist generation may create the directory before a plan exists. |

Persistence uses `.specify/feature.json`; Concorde does not create a parallel active-feature file.
Read-only resolution may inspect but must not rewrite the persisted selection.

### Selection states

```text
unselected -> selected -> replaced by explicit selection
                   \-> invalid if the workspace no longer resolves safely
```

## 9. Contract

A durable directional boundary agreement.

| Field | Type | Rules |
|---|---|---|
| `id` | stable ID | Unique. |
| `module` | module ID | Owning module. |
| `role` | enum | `provided` or `required`. |
| `flow` | string | Direction meaningful to the boundary. |
| `counterparties` | ID/string list | At least one. |
| `representation.kind` | enum | `standard` or `custom`. |
| `representation.format/version/definition` | strings | Required. |
| `features` | feature ID list | Affected behavior. |
| `evidence_status` | enum | Explicit. |

Standard representations name their authoritative definition and summarize the information passed.
Custom representations additionally require complete semantics, compatibility rules, a schema or
grammar, at least one example, and conformance evidence.

## 10. Scenario and Interaction

A representative current-level example.

| Field | Type | Rules |
|---|---|---|
| `id` | stable ID | Unique at its module level. |
| `module` | module ID | Defines visibility scope. |
| `participants` | participant ID list | Current module, immediate children, and permitted externals only. |
| `interactions` | ordered list | Each has `from`, `to`, description, and governing contract when crossing a boundary. |
| `prose_only` | boolean | Requires rationale when true. |

Scenarios never replace Feature outcome or requirements.

## 11. Architecture View

The maintained Archify JSON for one module level.

| Field | Type | Rules |
|---|---|---|
| `path` | safe path | Matches the owning module's `view`. |
| `current_module` | module ID | Exactly the owning module. |
| `components` | list | Immediate modules and permitted externals; no grandchildren or implementation details. |
| `connections` | list | Endpoints resolve in the same view and trace to contracts. |
| `scenarios` | ordered view list | Current-level representative traces. |
| `output` | safe generated path | Reproducible projection with provenance. |

## 12. Feature Diagram

A maintained visual explanation owned by one feature. It is either the feature's single optional
core component model or a supplemental view of a narrower dynamic question.

| Field | Type | Rules |
|---|---|---|
| `source` | safe path | Directly under the feature's `diagrams/`; descriptive filename other than `architecture.json`. |
| `role` | enum | `core` or `supplemental`; at most one core per feature. |
| `kind` | enum | `architecture`, `workflow`, `sequence`, `dataflow`, or `lifecycle`. |
| `scenarios` | scenario ID list | At least one, unless a named question is supplied. |
| `question` | string or null | The implementation-facing question explained when not scenario-specific. |
| `participants` | stable ID/component list | Consistent with maintained architecture and contract prose. |
| `contract_crossings` | interaction/contract list | Every visible boundary crossing resolves to maintained contract text. |
| `textual_counterpart` | spec section reference | Complete explanation that remains understandable without the diagram. |
| `output` | safe generated path | Provenance-bearing reproducible HTML; never maintained authority. |
| `validation` | evidence reference | Archify type/schema/showcase/freshness receipt and truthful visual-review status. |

The core Feature Diagram MUST use `architecture` and show stable components, responsibilities, and
interactions. Workflow, sequence, data-flow, and lifecycle kinds are supplemental only. Feature
Diagram is distinct from the canonical module Architecture View: it may explain feature component
collaboration or a representative scenario, but it cannot redefine module containment, feature
behavior, or boundary obligations.

## 13. Bounded Context

A deterministic read model for one module or active feature.

| Field | Type | Rules |
|---|---|---|
| `requested_id` | module or feature ID | Resolves exactly once. |
| `current_module` | projection | Responsibility, boundary, features, and I/O. |
| `children` | projection list | Immediate children with concise I/O only. |
| `feature_workspace` | projection or null | Root durable paths and active implementation paths for a feature request. |
| `feature_diagrams` | projection list | Only diagrams declared by the active feature, with source/output provenance. |
| `contracts` | ordered list | Only governing/relevant contracts. |
| `refinement_links` | ordered list | Adjacent links touching the current feature/level. |
| `evidence` | ordered list | Declared references and explicit status. |
| `deeper_references` | stable ID list | Navigation targets, not expanded bodies. |

## 14. Evidence Reference

| Field | Type | Rules |
|---|---|---|
| `kind` | enum | `implementation`, `test`, `validation`, or `generated`. |
| `target` | safe path or stable external reference | Must be reviewable. |
| `status` | enum | `unknown`, `partial`, `verified`, or `disagrees`. |
| `producer` | string | Command/tool that produced evidence when generated. |
| `source_digest` | digest or null | Required when freshness depends on maintained bytes. |

Architecture validation can verify the reference and status; it cannot infer code correctness.

## 15. Validation Finding

| Field | Type | Rules |
|---|---|---|
| `rule_id` | string | Stable `CONCORDE-<AREA>-<NNN>` ID. |
| `severity` | enum | `error`, `warning`, or `info`. |
| `source` | safe path | Maintained or selected source. |
| `line`, `column` | positive integer or null | Included when deterministic. |
| `subject_id` | stable ID or null | Entity involved. |
| `message` | string | Observable disagreement. |
| `remediation` | string | Concrete corrective action. |

Findings sort by rule, source, location, subject, and message. Validation is read-only; repeated runs
over unchanged inputs are byte-equivalent.

## 16. Workflow Distribution Handoff

The versioned, presentation-neutral boundary through which Feature 003 packages Feature 001 behavior.

| Field | Type | Rules |
|---|---|---|
| `protocol_version` | integer | Initially `2`; incompatible versions fail before command materialization. |
| `workspace_adapter` | installed-relative path | Resolves from the extension package, never the Concorde source checkout. |
| `normal_phase_obligations` | ordered command/phase list | Exactly the nine normal Spec Kit surfaces and their durable or temporal target. |
| `concorde_command_intents` | ordered command list | Exactly init, feature create/select/harden, context, and validate with presentation-neutral semantics. |
| `request_example` | durable contract reference | Demonstrates explicit/persisted selection input. |
| `result_example` | durable contract reference | Demonstrates root, implementation, phase target, status, and failures. |
| `source_digest` | digest | Binds the handoff to Feature 001 runtime/contract sources. |
| `evidence_status` | enum | Remains `partial` until Feature 003 supplies a matching clean-install receipt. |

The handoff contains no catalog URL, archive path, integration filename, preset strategy, or bundle
ownership record. Those are Feature 003 entities. Feature 003 may adapt presentation and packaging,
but cannot change path meanings or command intent without a reviewed Feature 001 contract change.

## Cross-Entity Invariants

1. Every Feature is owned by exactly one Module and registered by that Module.
2. Every selected Feature Workspace resolves to exactly one root `spec.md` and one root `design.md`.
3. Durable and temporal files never occupy each other's authority locations.
4. Every cross-boundary Scenario interaction resolves one declared Contract.
5. Feature refinement and Module containment graphs are acyclic and adjacent-level.
6. Bounded Context never expands beyond the current Module's immediate children.
7. Missing Evidence remains `unknown`; architectural validity never upgrades it.
8. Generated outputs are projections linked to maintained-source digests, never maintained intent.
9. Every declared Feature Diagram has an explicit core/supplemental role and textual counterpart;
   there is at most one core, its kind is architecture, and every diagrammed boundary crossing
   resolves to one maintained Contract.
10. Every release-installed command receipt from Feature 003 identifies the exact Workflow
    Distribution Handoff digest it implements; registration evidence cannot silently upgrade a
    changed handoff to verified.
11. Hardening can mutate only root `design.md` and the complete selected `implementation/`; incomplete
    tasks, absent/malformed task evidence, stale digests, or missing explicit approval preserve both.
