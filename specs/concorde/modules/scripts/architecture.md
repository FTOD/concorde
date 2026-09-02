---
id: module.concorde.scripts
kind: module
parent: module.concorde
modules: []
features:
  - feature.scripts.run-workflow-operations
diagrams: []
---

# Architecture: Scripts

## Responsibility

Provide portable, deterministic, path-safe operations for Profile 7 discovery/control state, bounded context,
initialization, validation, workspace routing, reflection support, projection, and cleanup-only delivery.

## Boundary

Scripts owns launch adapters, normalized in-memory architecture entities, safe repository loading,
operation envelopes, deterministic findings, and atomic filesystem transactions. It does not own
agent-authored feature/architecture prose, user product implementation, command conversation, or
generated documentation presentation.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.scripts.posix-launcher` | script | Locates the installed extension and invokes its Python entry adapter on POSIX systems. | `extensions/concorde/scripts/bash/concorde.sh` |
| `entity.scripts.powershell-launcher` | script | Equivalent portable launcher for PowerShell projects. | `extensions/concorde/scripts/powershell/concorde.ps1` |
| `entity.scripts.python-adapter` | program | Adds the installed runtime package to the import path and enters the CLI. | `extensions/concorde/scripts/python/concorde.py` |
| `entity.scripts.workspace-adapter` | program | Emits Protocol 12 paths for one selected direct feature file and corresponding stable-ID control attempt. | `extensions/concorde/scripts/python/workspace.py` |
| `entity.scripts.reflection-queue` | program | Maintains reflection-triage/v3 queue/plan state, allocates IDs from the tracked log high-water, and atomically removes eligible merged-small entries. | `extensions/concorde/scripts/python/reflections_queue.py` |
| `entity.scripts.runtime-model` | package | Immutable operation, module, entity, relation, interface, context, and finding records. | `extensions/concorde/runtime/concorde/model.py` |
| `entity.scripts.repository-loader` | program | Discovers Profile 7 architectures/direct feature files/diagrams plus declared control authorities and constructs the normalized package. | `extensions/concorde/runtime/concorde/repository.py#ProjectRepository.load` |
| `entity.scripts.context-builder` | program | Projects one bounded module or feature altitude with entity/interface relationships. | `extensions/concorde/runtime/concorde/context.py#bounded_context` |
| `entity.scripts.workspace-resolver` | program | Resolves selection, module ancestry, related summaries, stable-ID attempt/reflection state, and executable roots. | `extensions/concorde/runtime/concorde/feature_workspace.py#resolve_phase_paths` |
| `entity.scripts.validator` | program | Runs deterministic layout/hierarchy/entity/interface/evidence/diagram/freshness/reflection rules. | `extensions/concorde/runtime/concorde/validate.py#validate_project` |
| `entity.scripts.initializer` | program | Generates and applies Initialization Proposal 2 with configuration, root architecture, and reflection log. | `extensions/concorde/runtime/concorde/initialize.py` |
| `entity.scripts.delivery` | program | Proposes and atomically applies removal of one eligible complete attempt. | `extensions/concorde/runtime/concorde/delivery.py` |
| `entity.scripts.cli` | program | Parses operations and returns one structured result envelope. | `extensions/concorde/runtime/concorde/cli.py` |
| `entity.scripts.runtime-tests` | test | Unit/integration/contract/acceptance evidence for deterministic semantics and failure safety. | `tests/concorde` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.scripts.posix-launcher` | `calls` | `entity.scripts.python-adapter` | Forwards project-root and operation arguments without redefining semantics. |
| `entity.scripts.powershell-launcher` | `calls` | `entity.scripts.python-adapter` | Provides equivalent Windows invocation. |
| `entity.scripts.python-adapter` | `calls` | `entity.scripts.cli` | Enters the canonical dispatcher. |
| `entity.scripts.cli` | `calls` | `entity.scripts.context-builder` | Dispatches bounded context operations. |
| `entity.scripts.cli` | `calls` | `entity.scripts.validator` | Dispatches deterministic validation. |
| `entity.scripts.cli` | `calls` | `entity.scripts.initializer` | Dispatches reviewed initialization proposal/apply. |
| `entity.scripts.cli` | `calls` | `entity.scripts.delivery` | Dispatches cleanup-only delivery propose/apply. |
| `entity.scripts.repository-loader` | `reads_from` | `module.concorde.workspace-files` | Loads only canonical maintained Profile 7 sources, control authorities, and declared diagrams. |
| `entity.scripts.workspace-resolver` | `reads_from` | `entity.scripts.repository-loader` | Uses normalized IDs/paths to construct bounded phase context. |
| `entity.scripts.validator` | `reads_from` | `entity.scripts.repository-loader` | Validates the same normalized source package used by operations. |
| `entity.scripts.delivery` | `validates` | `module.concorde.workspace-files` | Checks attempt eligibility, paths, digest freshness, and project findings before removal. |
| `entity.scripts.validator` | `tested_by` | `entity.scripts.runtime-tests` | Focused and integrated test cases provide executable evidence for validation behavior. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.scripts.operation` | A composed skill invokes a launcher with one operation. | Launcher selects Python; CLI loads configuration/package; operation validates inputs and safe paths; one envelope serializes status, artifacts, findings, and result. | Deterministic success/failure with no conversational side channel. | `contract.scripts.operations` |
| `interaction.scripts.workspace` | A host phase requests the selected feature workspace. | Resolve `feature_path` or a stable ID; load its module ancestry/relations; derive the stable-ID control attempt and executable paths; return Protocol 12 JSON. | Exactly one canonical direct feature plus bounded durable/control context is routed. | `contract.workspace-files.feature-workspace` |
| `interaction.scripts.deliver` | Maintainer requests delivery of a complete control attempt. | Propose verifies task/checklist/validation/digest state; apply rechecks target/path/digest and feature-specific tombstone; atomically removes the stable-ID attempt or rolls back. | No matching attempt remains on success; the feature file, reflection log, and every other authority remain unchanged. | `contract.scripts.operations`, `contract.workspace-files.feature-workspace` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.scripts.run-workflow-operations` | Skills can invoke portable deterministic operations with structured, path-safe, non-ambiguous results. |

## Decisions

- Python standard-library semantics are canonical; shell and PowerShell only locate/forward.
- Every operation uses the same repository loader and structured envelope.
- `tested_by` direction is production subject → test; tests do not become architectural owners.
