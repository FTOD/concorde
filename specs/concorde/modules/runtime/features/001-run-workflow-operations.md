---
id: feature.runtime.run-workflow-operations
kind: feature
module: module.concorde.runtime
related_features:
  - feature.concorde.workflow
  - feature.concorde.explore-alignment
  - feature.concorde.maintain-agent-surfaces
  - feature.concorde.record-workflow-reflections
interfaces:
  provided:
    - contract.runtime.operations
  required:
    - contract.workspace.feature-workspace
    - contract.workspace.records
evidence_status: verified
---

# Run Workflow Operations

## Outcome and Scope

Commands and automation can invoke portable deterministic operations that resolve Profile 7
sources/native control state, validate typed architecture/interfaces, initialize safely, return
bounded context, explore evidence-qualified alignment, and close attempts atomically.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.runtime.cli` | Dispatches operations into one envelope contract. |
| `entity.runtime.repository-loader` | Loads normalized Profile 7 modules/entities/features/interfaces and control authorities. |
| `entity.runtime.alignment-explorer` | Projects bounded Profile subjects beside optional pinned UA graph/evidence with conservative status. |
| `entity.runtime.workspace-resolver` | Emits Protocol 12 stable-ID paths and bounded relations. |
| `entity.runtime.validator` | Produces exhaustive deterministic findings. |
| `entity.runtime.delivery` | Applies digest-bound cleanup-only Delivery 8. |

## Interfaces

### `contract.runtime.operations` — Deterministic runtime operations

- **Consumer**: Source-checkout or installed Concorde commands, CI, and supported tooling.
- **Direction**: Safe operation arguments to one structured result envelope.
- **Entry points**: Colocated POSIX/PowerShell launchers and Python `scripts/concorde.py` in root or `.concorde/framework`; operations include `init`, `context`, `explore`, `validate`, `deliver`, and `agent-assets`.
- **Inputs**: Project root, operation, stable target, format, and operation-specific proposal/options; exploration additionally accepts safe graph/sidecar paths, expected revision, text query, and effective-status filters.
- **Outputs**: Operation/target/status, artifacts, findings, and versioned result payload; exploration returns Alignment Schema 1 specification/implementation/provenance/alignment projections.
- **Obligations**: Deterministic behavior, safe paths, non-mutating read operations, atomic reviewed mutations, and actionable diagnostics.
- **Failures**: Invalid config/source/target/path/proposal or filesystem failure returns failure and preserves unrelated/current authority.
- **Compatibility**: Envelopes expose Profile 7, Protocol 12, Initialization 2, Delivery 8, and Alignment Schema 1 terminology only; native package version 1.1.0 adds `explore` without changing existing operations.
- **Implementing entities**: `entity.runtime.cli`, `entity.runtime.repository-loader`, `entity.runtime.alignment-explorer`, `entity.runtime.validator`, `entity.runtime.delivery`.
- **Example**: `concorde.py --project-root . validate` emits a JSON envelope whose findings carry stable rule IDs and remediations.

## Usage Scenarios

A launcher locates the installed runtime, the CLI loads the same repository model used by validation,
and the operation returns exactly one machine-readable result without becoming a conversational UI.
For exploration, optional implementation evidence is validated and bounded after Profile validation;
no operation writes an explorer index or repairs input.

## Requirements

- **FR-001**: All platform launchers MUST preserve the same Python runtime semantics.
- **FR-002**: Every operation MUST validate safe project-relative targets before reading/writing.
- **FR-003**: Read-only failures and rejected mutation proposals MUST be byte-preserving.
- **FR-004**: Exploration MUST preserve Profile identity separately from adapter metadata and reduce absent, stale, candidate-only, or invalid evidence to unknown.

## Edge Cases

- A target or attempt path is a symlink.
- PowerShell and POSIX quoting produce equivalent arguments.
- A valid implementation graph has no explicit alignment sidecar or current expected revision.
