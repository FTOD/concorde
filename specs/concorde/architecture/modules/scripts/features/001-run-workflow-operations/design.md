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
readiness, reflection, or implementation-acceptance behavior with complete structured results and
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
