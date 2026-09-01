---
id: feature.scripts.run-workflow-operations
kind: feature
module: module.concorde.scripts
related_features:
  - feature.concorde.workflow
  - feature.concorde.self-host-framework
  - feature.concorde.record-workflow-reflections
interfaces:
  provided:
    - contract.scripts.operations
  required:
    - contract.workspace-files.feature-workspace
    - contract.workspace-files.records
evidence_status: verified
---

# Run Workflow Operations

## Outcome and Scope

Skills can invoke portable deterministic operations that resolve Profile 7 sources/control state, validate typed
architecture/interfaces, initialize safely, return bounded context, and close attempts atomically.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.scripts.cli` | Dispatches operations into one envelope contract. |
| `entity.scripts.repository-loader` | Loads normalized Profile 7 modules/entities/features/interfaces and control authorities. |
| `entity.scripts.workspace-resolver` | Emits Protocol 12 stable-ID paths and bounded relations. |
| `entity.scripts.validator` | Produces exhaustive deterministic findings. |
| `entity.scripts.delivery` | Applies digest-bound cleanup-only Delivery 8. |

## Interfaces

### `contract.scripts.operations` — Deterministic runtime operations

- **Consumer**: Installed Concorde operation skills, CI, and supported tooling.
- **Direction**: Safe operation arguments to one structured result envelope.
- **Entry points**: POSIX/PowerShell launchers and Python `concorde.py`.
- **Inputs**: Project root, operation, stable target, format, and operation-specific proposal/options.
- **Outputs**: Operation/target/status, artifacts, findings, and versioned result payload.
- **Obligations**: Deterministic behavior, safe paths, non-mutating read operations, atomic reviewed mutations, and actionable diagnostics.
- **Failures**: Invalid config/source/target/path/proposal or filesystem failure returns failure and preserves unrelated/current authority.
- **Compatibility**: Envelopes expose Profile 7, Protocol 12, Initialization 2, and Delivery 8 terminology only.
- **Implementing entities**: `entity.scripts.cli`, `entity.scripts.repository-loader`, `entity.scripts.validator`, `entity.scripts.delivery`.
- **Example**: `concorde.py --project-root . validate` emits a JSON envelope whose findings carry stable rule IDs and remediations.

## Usage Scenarios

A launcher locates the installed runtime, the CLI loads the same repository model used by validation,
and the operation returns exactly one machine-readable result without becoming a conversational UI.

## Requirements

- **FR-001**: All platform launchers MUST preserve the same Python runtime semantics.
- **FR-002**: Every operation MUST validate safe project-relative targets before reading/writing.
- **FR-003**: Read-only failures and rejected mutation proposals MUST be byte-preserving.

## Edge Cases

- A target or attempt path is a symlink.
- PowerShell and POSIX quoting produce equivalent arguments.
