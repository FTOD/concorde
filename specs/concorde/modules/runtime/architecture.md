---
id: module.concorde.runtime
kind: module
parent: module.concorde
modules: []
features:
  - feature.runtime.run-workflow-operations
diagrams: []
---

# Architecture: Runtime

## Responsibility

Provide portable, deterministic, path-safe operations for Profile 7 discovery, native selection,
bounded context, evidence-qualified alignment exploration, initialization, validation, workspace
routing, reflection support, agent projection, and cleanup-only delivery.

## Boundary

Runtime owns the normalized in-memory model, repository loader, operation envelopes, safe path rules,
portable entry adapters, and atomic mutations explicitly defined by Concorde. It does not own
agent-authored architecture/feature prose, product implementation, public command conversation, or
generated documentation presentation.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.runtime.posix-launcher` | script | Invokes the colocated Python adapter on POSIX systems. | `scripts/concorde.sh` |
| `entity.runtime.powershell-launcher` | script | Invokes the same Python adapter on PowerShell systems. | `scripts/concorde.ps1` |
| `entity.runtime.python-adapter` | program | Adds the colocated package `src` directory to imports and enters the CLI. | `scripts/concorde.py` |
| `entity.runtime.workspace-adapter` | program | Emits Protocol 12 paths for one native-selected direct feature. | `scripts/workspace.py` |
| `entity.runtime.reflection-queue` | program | Allocates reflection IDs and maintains triage plan/merged-small state. | `scripts/reflections_queue.py` |
| `entity.runtime.model` | package | Immutable operation, module, entity, relation, interface, context, and finding records. | `src/concorde/model.py` |
| `entity.runtime.repository-loader` | program | Discovers Profile 7 module architectures, direct features, diagrams, and control authorities. | `src/concorde/repository.py#ProjectRepository.load` |
| `entity.runtime.context-builder` | program | Projects one bounded module or feature altitude. | `src/concorde/context.py#bounded_context` |
| `entity.runtime.alignment-explorer` | program | Strictly validates optional pinned UA graph/sidecar inputs and projects bounded specification, implementation, provenance, and effective alignment records without mutation. | `src/concorde/alignment.py#explore_alignment` |
| `entity.runtime.workspace-resolver` | program | Resolves native selection, ancestry, related summaries, attempt/reflection state, and executable roots. | `src/concorde/feature_workspace.py#resolve_phase_paths` |
| `entity.runtime.validator` | program | Runs layout, hierarchy, entity, interface, evidence, diagram, freshness, and reflection rules. | `src/concorde/validate.py#validate_project` |
| `entity.runtime.initializer` | program | Proposes and atomically applies Initialization Proposal 2. | `src/concorde/initialize.py` |
| `entity.runtime.delivery` | program | Proposes and applies digest-bound removal of one complete attempt. | `src/concorde/delivery.py` |
| `entity.runtime.agent-projector` | program | Renders and verifies command/reflection assets without an external command composer. | `src/concorde/command_assets.py` |
| `entity.runtime.cli` | program | Dispatches supported operations and serializes one structured envelope. | `src/concorde/cli.py` |
| `entity.runtime.tests` | test | Unit, contract, integration, and acceptance evidence for runtime semantics. | `tests/concorde` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.runtime.posix-launcher` | `calls` | `entity.runtime.python-adapter` | Forwards arguments without redefining behavior. |
| `entity.runtime.powershell-launcher` | `calls` | `entity.runtime.python-adapter` | Provides equivalent Windows entry behavior. |
| `entity.runtime.python-adapter` | `calls` | `entity.runtime.cli` | Enters the canonical dispatcher from source or installed package layout. |
| `entity.runtime.cli` | `calls` | `entity.runtime.context-builder` | Dispatches bounded context. |
| `entity.runtime.cli` | `calls` | `entity.runtime.alignment-explorer` | Dispatches read-only evidence-qualified exploration. |
| `entity.runtime.cli` | `calls` | `entity.runtime.validator` | Dispatches deterministic validation. |
| `entity.runtime.cli` | `calls` | `entity.runtime.initializer` | Dispatches reviewed initialization. |
| `entity.runtime.cli` | `calls` | `entity.runtime.delivery` | Dispatches cleanup-only delivery. |
| `entity.runtime.repository-loader` | `reads_from` | `module.concorde.workspace` | Loads only canonical maintained/control sources and declared diagrams. |
| `entity.runtime.workspace-resolver` | `reads_from` | `entity.runtime.repository-loader` | Builds bounded phase context from normalized IDs and paths. |
| `entity.runtime.alignment-explorer` | `reads_from` | `entity.runtime.repository-loader` | Projects the same validated Profile 7 identities used by every operation. |
| `entity.runtime.validator` | `reads_from` | `entity.runtime.repository-loader` | Validates the same package used by every operation. |
| `entity.runtime.delivery` | `validates` | `module.concorde.workspace` | Checks attempt eligibility, freshness, and exact removal safety. |
| `entity.runtime.agent-projector` | `reads_from` | `module.concorde.commands` | Projects canonical root command and reflection assets. |
| `entity.runtime.validator` | `tested_by` | `entity.runtime.tests` | Executable cases establish bounded runtime evidence. |
| `entity.runtime.alignment-explorer` | `tested_by` | `entity.runtime.tests` | Unit, contract, integration, acceptance, installed, and release cases establish its bounded claims. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.runtime.operation` | A command invokes a runtime entry point. | Locate colocated `src`; parse operation; load configuration/package; validate inputs and paths; execute the operation; serialize one canonical envelope. | Deterministic success/failure with stable diagnostics and no conversational side channel. | `contract.runtime.operations` |
| `interaction.runtime.workspace` | A phase requests selected feature context. | Resolve explicit path, `CONCORDE_FEATURE_PATH`, or `.concorde/feature.json`; load the direct feature and module; derive stable-ID attempt/reflection and executable context; return Protocol 12. | Exactly one canonical direct feature plus bounded context is routed. | `contract.workspace.feature-workspace` |
| `interaction.runtime.explore` | A caller requests one stable module, entity, feature, or interface. | Validate Profile 7; project the target altitude; strictly validate optional UA graph and schema-1 sidecar inputs; compare explicit revisions; qualify records; apply text/status bounds; serialize canonical JSON. | Current explicit evidence may be partial, verified, or disagreeing; every absent, stale, incompatible, or candidate-only claim is unknown. | `contract.concorde.alignment-explorer`, `contract.runtime.operations` |
| `interaction.runtime.deliver` | Maintainer requests delivery. | Verify tasks, checklists, passing evidence, validation, digest, safe real attempt path, and retained authorities; atomically remove or roll back. | One complete attempt disappears and every durable/executable authority is retained. | `contract.runtime.operations`, `contract.workspace.feature-workspace` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.runtime.run-workflow-operations` | Commands invoke portable deterministic Concorde operations with structured, safe, unambiguous results. |

## Decisions

- Python standard-library behavior is canonical; shell and PowerShell only locate and forward.
- Source and installed packages preserve the same relative `scripts/` + `src/` layout.
- Native selection lives at `.concorde/feature.json`; no compatibility reader exists for host state.
- Every operation uses the same loader and envelope.
- Exploration never normalizes or rewrites input graphs and never treats adapter vocabulary or text
  similarity as identity/evidence.
- Test relationships point from production subject to evidence (`tested_by`).
