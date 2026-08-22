# Phase 1 Data Model: Concorde Core Workflow

**Feature**: `feature.concorde.core-workflow`  
**Date**: 2026-08-22

This is the technical model for the active implementation attempt. Durable semantics remain in
`spec.md`, module/contract Markdown, Archify JSON, and the referenced contract representations.

## Relationship Summary

```text
Specification Package
└── Root Module
    ├── Contract *
    ├── Feature * ── Feature Workspace ── Implementation Workspace (0..1 active)
    ├── Immediate Module * ── repeats Specification Package
    └── Architecture View (required when non-leaf)

Feature ── owned by exactly one Module
Feature ── refines Feature at adjacent parent level (0..*)
Feature ── illustrated by Scenario (1..*)
Scenario Interaction ── governed by Contract when it crosses a boundary
Feature Selection ── points to exactly one Feature Workspace
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
`spec.md`, and declared Archify JSON. Files below `implementation/` are addressable for active feature
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

A lower-level feature without a parent refinement must be marked internal with a non-empty rationale.

## 4. Feature Workspace

The single nested location selected for the normal lifecycle.

| Field | Type | Rules |
|---|---|---|
| `root` | safe project-relative directory | `<module-package>/features/<number-name>/`. |
| `specification` | path | Exactly `<root>/spec.md`; required after specify. |
| `contracts` | directory | Optional durable feature-level representations at `<root>/contracts/`. |
| `checklists` | directory | Optional durable requirements-quality artifacts at `<root>/checklists/`. |
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
| `lifecycle` | derived/recorded enum | `absent`, `active`, `accepted`, `frozen`, `archived`, or `removed`. Archive naming is outside this slice. |

The first release permits at most one `active` directory. Acceptance may freeze, archive, or remove
the directory without changing Feature fields. A later attempt must not silently inherit a stale
plan as current design.

```text
absent -> active -> accepted -> frozen
                    |          \-> archived
                    \------------> removed
frozen -> archived | removed
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
| `implementation_dir` | derived path | `<feature_directory>/implementation/`. |
| `plan`, `tasks`, `research`, `data_model`, `quickstart` | derived paths | Always below `implementation_dir`. |

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

## 12. Bounded Context

A deterministic read model for one module or active feature.

| Field | Type | Rules |
|---|---|---|
| `requested_id` | module or feature ID | Resolves exactly once. |
| `current_module` | projection | Responsibility, boundary, features, and I/O. |
| `children` | projection list | Immediate children with concise I/O only. |
| `feature_workspace` | projection or null | Root durable paths and active implementation paths for a feature request. |
| `contracts` | ordered list | Only governing/relevant contracts. |
| `refinement_links` | ordered list | Adjacent links touching the current feature/level. |
| `evidence` | ordered list | Declared references and explicit status. |
| `deeper_references` | stable ID list | Navigation targets, not expanded bodies. |

## 13. Evidence Reference

| Field | Type | Rules |
|---|---|---|
| `kind` | enum | `implementation`, `test`, `validation`, or `generated`. |
| `target` | safe path or stable external reference | Must be reviewable. |
| `status` | enum | `unknown`, `partial`, `verified`, or `disagrees`. |
| `producer` | string | Command/tool that produced evidence when generated. |
| `source_digest` | digest or null | Required when freshness depends on maintained bytes. |

Architecture validation can verify the reference and status; it cannot infer code correctness.

## 14. Validation Finding

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

## Cross-Entity Invariants

1. Every Feature is owned by exactly one Module and registered by that Module.
2. Every selected Feature Workspace resolves to exactly one root `spec.md`.
3. Durable and temporal files never occupy each other's authority locations.
4. Every cross-boundary Scenario interaction resolves one declared Contract.
5. Feature refinement and Module containment graphs are acyclic and adjacent-level.
6. Bounded Context never expands beyond the current Module's immediate children.
7. Missing Evidence remains `unknown`; architectural validity never upgrades it.
8. Generated outputs are projections linked to maintained-source digests, never maintained intent.
