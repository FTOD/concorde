---
id: contract.integration.feature-workspace
kind: contract
module: module.concorde.spec-kit-integration
role: provided
flow: bidirectional
counterparties:
  - external.maintainer
  - external.spec-kit
representation:
  kind: custom
  format: Concorde Feature Workspace Protocol
  version: "2"
  definition: specs/concorde/features/001-concorde-starter-workflow/contracts/feature-workspace.schema.json
examples:
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/feature-create-proposal.json
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/feature-select-response.json
  - specs/concorde/features/001-concorde-starter-workflow/contracts/examples/feature-harden-proposal.json
features:
  - feature.integration.manage-feature-workspace
evidence_status: partial
---

# Feature Workspace Contract

## Purpose

Place a feature under its providing module, select exactly that nested feature root for subsequent
normal Spec Kit phases, and explicitly harden a completed attempt into permanent design without
creating duplicate lifecycle artifacts.

## Information

The custom JSON representation passes the operation, stable module or feature target, safe workspace
paths, proposed or applied changes, deterministic findings, and the source digest that binds review
to the inspected hierarchy. The selected root is persisted using Spec Kit's project-local
`.specify/feature.json` `feature_directory` field; Concorde does not create another selection store.
Complete field types and allowed values are defined by the linked schema and examples.

## Obligations

- Creation proposes the providing module, stable feature ID, exact nested root, module registration,
  affected current-level view, and conflicts before maintained intent changes.
- Applying a creation requires explicit approval and refuses a stale source digest or occupied path.
- Creation establishes the permanent root `spec.md` and `design.md` pair.
- Selection resolves an existing root `spec.md`/`design.md` pair, verifies its module ownership and safe path, and
  atomically persists that root as the active Spec Kit workspace.
- Derived planning and task paths always use the selected root's `implementation/` child.
- The derived checklist path is exactly `<implementation>/checklists`; no root checklist alias or
  symlink is created.
- Read-only resolution never changes `.specify/feature.json`, and no operation creates root-level
  `plan.md` or `tasks.md` aliases.
- Hardening proves every canonical task is complete and every recognizable existing checklist item
  is satisfied, binds the reviewed design and exact removal set to a source digest, returns the exact
  proposal path and task/checklist summaries, requires explicit approval, atomically replaces root
  `design.md`, and removes only the selected feature's complete `implementation/` directory.

## Failure Semantics

Unknown or ambiguous IDs, unsafe paths, duplicate feature IDs, occupied workspace roots, stale
proposals, invalid feature specifications or designs, incomplete tasks, and conflicting or stale
active-attempt state produce `invalid` or `conflict` results with actionable findings. Failure leaves
maintained sources, the active attempt, and prior selection unchanged.

## Compatibility

Protocol v2 adds permanent feature-design and hardening proposal/result fields. Removing a required
field, changing the meaning of the selected root, or changing durable/temporal path authority
requires a new major version and migration guidance. The embedded Spec Kit selection field is
supported only for explicitly tested Spec Kit versions.

## Evidence

Automated evidence verifies creation proposals, selection, collision safety, idempotency, hardening
eligibility/apply/rollback, cross-integration command parity, and the complete phase-to-path matrix. Evidence remains `partial`
until the human placement and explicit architecture-approval protocols are completed.
