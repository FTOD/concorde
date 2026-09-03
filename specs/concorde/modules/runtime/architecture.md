---
id: module.concorde.runtime
kind: module
parent: module.concorde
modules: []
features:
  - feature.runtime.run-lifecycle-tools
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-runtime-system-overview.html
---

# Architecture: Runtime

## Responsibility

Provide portable, deterministic, path-safe Tools for Profile 7 discovery, native selection, bounded
context, evidence-qualified alignment exploration, initialization, docsite scaffolding, validation, workspace routing,
reflection queue support, capability validation, and cleanup-only delivery.

## Boundary

Runtime owns the normalized in-memory model, repository loader, Tool envelopes, safe path rules,
portable entry adapters, and atomic mutations explicitly defined by Concorde. It does not own
agent-authored architecture/feature prose, product implementation, leaf Skill prompts, LangGraph
Operation topology/policy/process handoff (even where physically under `src/concorde`), model
execution, or generated documentation presentation. Operation is not a synonym for a CLI action in this module.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.runtime.posix-launcher` | script | Invokes the colocated Python adapter on POSIX systems. | `scripts/concorde.sh` |
| `entity.runtime.powershell-launcher` | script | Invokes the same Python adapter on PowerShell systems. | `scripts/concorde.ps1` |
| `entity.runtime.python-adapter` | program | Adds the colocated package `src` directory to imports and enters the CLI. | `scripts/concorde.py` |
| `entity.runtime.workspace-adapter` | program | Emits Protocol 13 paths for one native-selected direct feature. | `scripts/workspace.py` |
| `entity.runtime.reflection-queue` | program | Implements reflection-triage/v5 per-file queue, ID-index allocation, plan/merged-small state, and bounded per-entry validation as a deterministic Tool. | `scripts/reflections_queue.py` |
| `entity.runtime.model` | package | Immutable Tool result, module, entity, relation, interface, context, and finding records. | `src/concorde/model.py` |
| `entity.runtime.tool-result` | type | Structured `tool`, target, status, artifacts, findings, and result payload for one bounded runtime action. | `src/concorde/model.py#ToolResult` |
| `entity.runtime.tool-envelope` | function | Serializes one Tool result with a `tool` discriminator. | `src/concorde/diagnostics.py#tool_envelope` |
| `entity.runtime.repository-loader` | program | Discovers Profile 7 module architectures, direct features, diagrams, and control authorities. | `src/concorde/repository.py#ProjectRepository.load` |
| `entity.runtime.context-builder` | program | Projects one bounded module or feature altitude. | `src/concorde/context.py#bounded_context` |
| `entity.runtime.alignment-explorer` | program | Validates optional pinned UA graph/sidecar inputs and projects bounded evidence-qualified alignment without mutation. | `src/concorde/alignment.py#explore_alignment` |
| `entity.runtime.workspace-resolver` | program | Resolves native selection, ancestry, related summaries, attempt/reflection state, executable roots, and safe concrete Protocol-13/task path roles without following symlinks. | `src/concorde/feature_workspace.py#resolve_phase_paths` |
| `entity.runtime.validator` | program | Runs layout/parallel-authority, hierarchy, entity, interface, capability, evidence, diagram, freshness, and reflection rules. | `src/concorde/validate.py#validate_project` |
| `entity.runtime.capability-validator` | program | Validates exact Script/public-internal-Skill/Operation pairs, effects, mixed literal topology/bindings, and direct/indirect cycles without importing Operation Python. | `src/concorde/validation/capabilities.py` |
| `entity.runtime.initializer` | program | Proposes and atomically applies Initialization Proposal 3 with a root Archify system overview. | `src/concorde/initialize.py` |
| `entity.runtime.delivery` | program | Proposes and applies digest-bound Delivery Proposal 9 removal of one complete attempt. | `src/concorde/delivery.py` |
| `entity.runtime.docsite-template` | program | Enumerates the packaged docsite template inventory and digest shared by the installer and scaffold Tool. | `src/concorde/docsite_template.py` |
| `entity.runtime.docsite-scaffold` | program | Proposes and atomically applies Docsite Scaffold Proposal 1 with a project-owned site identity and no synthetic project prose. | `src/concorde/docsite_scaffold.py` |
| `entity.runtime.cli` | program | Dispatches supported Tools and serializes one structured Tool envelope. | `src/concorde/cli.py` |
| `entity.runtime.tests` | test | Unit, contract, integration, and acceptance evidence for Runtime Tool semantics. | `tests/concorde` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.runtime.posix-launcher` | `calls` | `entity.runtime.python-adapter` | Forwards Tool arguments without redefining behavior. |
| `entity.runtime.powershell-launcher` | `calls` | `entity.runtime.python-adapter` | Provides equivalent Windows entry behavior. |
| `entity.runtime.python-adapter` | `calls` | `entity.runtime.cli` | Enters the canonical Tool dispatcher from source or installed layout. |
| `entity.runtime.cli` | `calls` | `entity.runtime.context-builder` | Dispatches bounded context retrieval. |
| `entity.runtime.cli` | `calls` | `entity.runtime.alignment-explorer` | Dispatches read-only evidence-qualified exploration. |
| `entity.runtime.cli` | `calls` | `entity.runtime.validator` | Dispatches deterministic validation. |
| `entity.runtime.cli` | `calls` | `entity.runtime.initializer` | Dispatches reviewed initialization. |
| `entity.runtime.cli` | `calls` | `entity.runtime.delivery` | Dispatches cleanup-only delivery. |
| `entity.runtime.cli` | `calls` | `entity.runtime.docsite-scaffold` | Dispatches reviewed docsite scaffolding. |
| `entity.runtime.docsite-scaffold` | `reads_from` | `entity.runtime.docsite-template` | Copies exactly the packaged adapter inventory and binds its digest into the proposal. |
| `entity.runtime.cli` | `calls` | `entity.runtime.tool-envelope` | Serializes every bounded action with Tool terminology. |
| `entity.runtime.repository-loader` | `reads_from` | `module.concorde.workspace` | Loads only canonical maintained/control sources and declared diagrams. |
| `entity.runtime.workspace-resolver` | `reads_from` | `entity.runtime.repository-loader` | Builds Protocol 13 context from normalized IDs and paths. |
| `entity.runtime.alignment-explorer` | `reads_from` | `entity.runtime.repository-loader` | Projects the same validated Profile 7 identities used by every Tool. |
| `entity.runtime.validator` | `reads_from` | `entity.runtime.repository-loader` | Validates the same package model used by every Tool. |
| `entity.runtime.validator` | `calls` | `entity.runtime.capability-validator` | Adds package-scoped structural checks for canonical capabilities. |
| `entity.runtime.delivery` | `validates` | `module.concorde.workspace` | Checks attempt eligibility, freshness, and exact removal safety. |
| `entity.runtime.tool-envelope` | `transforms` | `entity.runtime.tool-result` | Produces the public versioned JSON response. |
| `entity.runtime.validator` | `tested_by` | `entity.runtime.tests` | Executable cases establish bounded validation evidence. |
| `entity.runtime.alignment-explorer` | `tested_by` | `entity.runtime.tests` | Unit through acceptance cases establish its bounded claims. |
| `entity.runtime.delivery` | `tested_by` | `entity.runtime.tests` | Proposal, digest, rollback, and retention cases establish cleanup safety. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.runtime.tool` | A Skill, script, CI job, or maintainer invokes a Runtime entry point. | Locate colocated `src`; parse the Tool; load configuration/package; validate inputs and paths; execute the bounded action; serialize one canonical Tool envelope. | Deterministic success/failure with stable diagnostics and no conversational side channel. | `contract.runtime.tools` |
| `interaction.runtime.workspace` | A path-sensitive Skill or trusted Operation resolver requests selected feature context. | Resolve explicit path, environment selection, or `.concorde/feature.json`; load the direct feature/module; derive stable-ID attempt/reflection/executable context; validate concrete task/role paths and reject symlinks/escapes; return Protocol 13. | Exactly one canonical direct feature plus bounded safe role inputs is routed. | `contract.workspace.feature-workspace` |
| `interaction.runtime.explore` | A caller requests one stable module, entity, feature, or interface. | Validate Profile 7; project the target altitude; validate optional UA graph and schema-1 sidecar; compare revisions; qualify records; apply text/status bounds; serialize Tool JSON. | Current explicit evidence may qualify alignment; absent, stale, incompatible, or candidate-only claims are unknown. | `contract.concorde.alignment-explorer`, `contract.runtime.tools` |
| `interaction.runtime.deliver` | Maintainer requests cleanup after completed work. | Verify tasks, checklists, passing evidence, validation, digest, safe real attempt path, and retained authorities; atomically remove or roll back. | One complete attempt disappears and every durable/executable authority is retained. | `contract.runtime.tools`, `contract.workspace.feature-workspace` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.runtime.run-lifecycle-tools` | Skills, Operations, scripts, and automation invoke portable deterministic Concorde Tools with structured, safe results. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Python standard-library behavior is canonical; shell and PowerShell only locate and forward.
- Source and installed packages preserve the same relative `scripts/` plus `src/` layout.
- Native selection lives at `.concorde/feature.json`; no compatibility reader exists for host state.
- Every Runtime action uses the same loader and Tool envelope; Operation is reserved for LangGraph.
- Files under `src/concorde` retain module ownership by responsibility: Runtime owns deterministic
  workspace/validation Tools, while Operations owns graph/policy/process-handoff programs.
- Protocol 13, Delivery Proposal 9, architecture-service envelope 2, capability-surface status schema
  2, and reflection-triage/v5 use `tool` discriminators.
- The docsite template inventory rule lives in Runtime so the installer and the scaffold Tool never
  disagree about packaged adapter bytes.
- Exploration never normalizes or rewrites input graphs and never treats adapter vocabulary or text
  similarity as identity/evidence.
- Test relationships point from production subject to evidence (`tested_by`).
