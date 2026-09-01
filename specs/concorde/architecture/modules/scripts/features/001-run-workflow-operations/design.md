---
id: feature.scripts.run-workflow-operations
kind: feature
module: module.concorde.scripts
refines:
  - feature.concorde.workflow
  - feature.concorde.self-host-framework
  - feature.concorde.record-workflow-reflections
scenarios:
  - scenario.scripts.run-workflow-operations
contracts:
  provided:
    - contract.scripts.operations
  required:
    - contract.scripts.workspace-files
evidence_status: verified
canonical_design: specs/concorde/architecture/modules/scripts/features/001-run-workflow-operations/design.md
---

# Run Workflow Operations

**Status**: Implemented and verified

## Outcome

Skills can resolve a selected workspace and invoke deterministic initialization, context, validation,
readiness, reflection, or implementation-delivery behavior with complete structured results and
repository-safe file access.

## Representative Scenario

`scenario.scripts.run-workflow-operations` follows a validation skill through the portable launcher.
Scripts discover the configured specification root, parse the maintained files, evaluate every rule,
and return sorted findings and a source digest. No source is changed.

## Diagram Decision

The root [level view](../../../../diagrams/level-view.json) shows Skills invoking Scripts and Scripts
operating on Workspace Files. Operation internals are code structure rather than another maintained
architectural level, so a child diagram is unnecessary.

## Requirements

- Launchers MUST resolve the shipped runtime relative to the installed extension.
- Workspace routing MUST return canonical durable and temporal paths or actionable findings.
- Read operations MUST be deterministic and non-mutating.
- Write operations MUST separate proposal from explicitly approved, digest-bound apply.
- Results MUST preserve status, artifacts, findings, and operation-specific data across launchers.
- Unsafe, symlinked, ambiguous, stale, or conflicting paths MUST fail without partial mutation.
- `ask` MUST NOT appear as a runtime operation.
- The runtime MUST require only the declared Python baseline and standard library.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Operation envelope` | The serialized structured result shared by launchers and runtime operations. | `represents` → `Structured result` |
| `Read operation` | A runtime operation that observes repository state without mutating sources. | `is a` → `Runtime operation`; `returns` → `Operation envelope` |
| `Write operation` | A runtime operation that separates a reviewed mutation proposal from digest-bound apply. | `is a` → `Runtime operation`; `applies` → `Mutation proposal` |
| `Source digest` | A deterministic hash over the bounded source set used to detect stale proposals and evidence. | `binds` → `Operation envelope`; `binds` → `Mutation proposal` |
