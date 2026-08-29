---
id: contract.workspace-files.feature-workspace
kind: contract
module: module.concorde.workspace-files
role: provided
flow: bidirectional
counterparties:
  - external.maintainer
  - external.spec-kit
  - module.concorde.skills
  - module.concorde.scripts
representation:
  kind: custom
  format: Concorde Feature Workspace Protocol
  version: "6"
  definition: specs/concorde/features/001-concorde-workflow/contracts/feature-workspace.schema.json
examples:
  - specs/concorde/features/001-concorde-workflow/contracts/examples/impl-accept-eligible-response.json
  - specs/concorde/features/001-concorde-workflow/contracts/examples/impl-accept-proposal.json
features:
  - feature.workspace-files.manage-feature-workspace
evidence_status: partial
---

# Feature Workspace Contract

## Purpose

Resolve the standard Spec Kit selection to exactly one nested canonical feature root before every
normal Spec Kit phase, return that root's validated durable/temporal paths and bounded relationship
context, and explicitly accept a completed attempt into durable feature `implementation.md`,
optionally amending the providing module's `design.md`, without creating
duplicate lifecycle artifacts.

## Information

The custom JSON representation passes the operation, stable feature target, safe workspace paths,
selected kind and relationship context, attempt state, proposed or applied acceptance changes,
deterministic findings, and the source digest that binds review to the inspected hierarchy
(including the current module `design.md`). The selected root is Spec Kit's project-local
`.specify/feature.json` `feature_directory` field, written by `speckit.specify` or set through
`SPECIFY_FEATURE_DIRECTORY`; Concorde does not create another selection store or a selection
command. Complete field types and allowed values are defined by the linked schema and examples.

## Obligations

- Resolution MUST accept only a selected root with a safe, canonical path directly beneath a
  module's `features/` or a top-level parent's `subfeatures/` directory, a real root
  `abstract.md`/`design.md`/`implementation.md` trio with no legacy names, and consistent module or parent
  registration; anything else returns actionable findings.
- Resolution MUST return the selected workspace kind, ID, providing module, durable and temporal
  paths, `attempt_state`, the providing module's `module.md` and `design.md` as navigation
  references, nullable read-only parent context, and ordered concise sibling summaries without
  bodies or attempt paths.
- Derived planning and task paths always use the selected root's `attempt/` child.
- The derived checklist path is exactly `<attempt>/checklists`; no root checklist alias or
  symlink is created.
- Read-only resolution never changes `.specify/feature.json`, and no operation creates root-level
  `plan.md` or `tasks.md` aliases.
- An existing non-empty `attempt/` attempt MUST be reported through `attempt_state:
  active` and MUST never be replaced, archived as a second authority, or removed except by an
  approved acceptance apply.
- Acceptance proves every canonical task is complete and every recognizable existing checklist item
  is satisfied, binds the reviewed realization, the optional module design-reference amendment, and
  the exact removal set to a source digest, returns the exact proposal path and task/checklist
  summaries, requires explicit approval, atomically replaces the selected feature's `implementation.md` and (when
  proposed) the providing module's `design.md`, and removes only the selected feature's complete
  `attempt/` directory; `abstract.md`, feature `design.md`, `module.md`, and every other root remain
  byte-identical.

## Failure Semantics

Unknown or ambiguous IDs, unsafe or symlinked paths, unregistered or misplaced roots, missing
durable trios, legacy names, stale proposals (including a changed module
`design.md`), an amendment targeting any path other than the providing module's `design.md`, invalid
feature specifications or realizations, incomplete tasks, and conflicting or stale active-attempt
state produce `invalid` or `conflict` results with actionable findings. Failure leaves maintained
sources, the active attempt, and the standard Spec Kit selection unchanged.

## Compatibility

Protocol v8 sets `schema_version` 8 and exposes `feature_abstract`, `feature_design`,
`feature_implementation`, `attempt_dir`, `attempt_state`, `module_summary`, and `module_design`.
Acceptance proposal v6 uses `implementation`, optional `module_design`, and `remove`, and results use
`implementation_digest_*`. Protocol v3 withdrew `feature.create` and `feature.select` together with their
creation/selection request options in favour of standard Spec Kit creation (`speckit.specify` with
`SPECIFY_FEATURE_DIRECTORY`) and selection (`.specify/feature.json`); `impl.accept` is the only
remaining operation. The constitution (v2.0.0, principle A.III) no longer requires one providing
module per feature, and the withdrawn operations encoded that assumption. Removing a required field,
changing the meaning of the selected root, or changing durable/temporal path authority requires a
new major version and migration guidance. The embedded Spec Kit selection field is supported only
for explicitly tested Spec Kit versions.

## Evidence

Automated evidence verifies selected-root resolution, collision and unsafe-path safety, idempotency,
acceptance eligibility/apply/rollback, cross-integration command parity, and the complete
phase-to-path matrix. Evidence remains `partial` until the human placement and explicit
architecture-approval protocols are completed.
