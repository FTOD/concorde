---
id: module.concorde
kind: module
parent: null
modules:
  - module.concorde.skills
  - module.concorde.operations
  - module.concorde.runtime
  - module.concorde.workspace
  - module.concorde.distribution
  - module.concorde.auto-docs
features:
  - feature.concorde.workflow
  - feature.concorde.publish-project-docsite
  - feature.concorde.install
  - feature.concorde.maintain-agent-surfaces
  - feature.concorde.record-workflow-reflections
  - feature.concorde.explore-alignment
  - feature.concorde.define-project-ontology
  - feature.concorde.workflow.initialize-architecture
  - feature.concorde.workflow.retrieve-bounded-context
  - feature.concorde.workflow.answer-workflow-questions
  - feature.concorde.workflow.manage-feature-workspaces
  - feature.concorde.workflow.specify-behavior
  - feature.concorde.workflow.plan-delivery
  - feature.concorde.workflow.execute-and-reconcile
  - feature.concorde.workflow.validate-architecture
  - feature.concorde.workflow.accept-milestone
  - feature.concorde.workflow.fast-loop
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-system-overview.html
---

# Architecture: Concorde

## Responsibility

Provide a standalone, module-centered development system in which durable architecture and feature
intent, executable reality, evidence, temporal work state, and a permission-bounded structural
capability hierarchy have explicit, non-overlapping authority.

## Boundary

Concorde owns Scripts that expose deterministic Tools, public/internal effect-declared leaf Skills,
acyclic paired LangGraph Operations, complete Markdown format references, project-control semantics, agent
projection, direct installation, evidence-qualified alignment exploration, and optional
documentation projections, including an isolated installed Python environment for Operation
dependencies. It does not own a coding-agent/model runtime, a project's own virtual environment, project product
code, Archify rendering, Docusaurus internals, or Understand Anything graph semantics.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `module.concorde.skills` | module | Canonical public/internal leaf prompts, effect/exposure metadata, format references, capability parsing, and public agent projection semantics. | `specs/concorde/modules/skills/architecture.md` |
| `module.concorde.operations` | module | Paired LangGraph control graphs, nested public planning, and per-leaf Codex/Claude policy/process enforcement. | `specs/concorde/modules/operations/architecture.md` |
| `module.concorde.runtime` | module | Deterministic Tools, repository loading, workspace routing, validation, reflection support, and delivery. | `specs/concorde/modules/runtime/architecture.md` |
| `module.concorde.workspace` | module | Durable specification, project control, source/evidence, installed, and projection placement rules. | `specs/concorde/modules/workspace/architecture.md` |
| `module.concorde.distribution` | module | One native package and its owned installation. | `specs/concorde/modules/distribution/architecture.md` |
| `module.concorde.auto-docs` | module | Validation-gated publication of maintained module architecture and direct feature specifications. | `specs/concorde/modules/auto-docs/architecture.md` |
| `entity.concorde.package-manifest` | configuration | Concorde 2.1.0 Package Manifest 2 identity and exact Script, 17-leaf, three-Operation, managed-runtime, template, docsite-template, protocol, and integration inventory. | `concorde.json` |
| `entity.concorde.scripts` | directory | Directly runnable entry points that expose bounded deterministic Tools, package automation, and the managed Operation bootstrap. | `scripts` |
| `entity.concorde.skills` | directory | Canonical leaf capability directories, each containing exactly one `SKILL.md`. | `skills` |
| `entity.concorde.operations` | directory | Canonical LangGraph capability directories, each containing exactly `operation.py` and associated `SKILL.md`. | `operations` |
| `entity.concorde.templates` | directory | Complete feature, plan, task, checklist, constitution, and reflection Markdown format references. | `templates` |
| `entity.concorde.agent-assets` | directory | Internal reflection-triage roles and integration templates. | `agent-assets` |
| `entity.concorde.runtime` | package | Standard-library implementation of Concorde source, Tool, workspace, capability validation, permission compilation/process handoff, and read-only alignment contracts plus lazy Operation support. | `src/concorde` |
| `entity.concorde.cli` | program | Structured Tool dispatcher for initialization, docsite scaffolding, context, exploration, validation, delivery, and agent assets. | `src/concorde/cli.py#create_parser` |
| `entity.concorde.workspace-resolver` | program | Resolves one direct feature, its module/ancestry/relations, and stable-ID control paths through Protocol 13. | `src/concorde/feature_workspace.py#resolve_phase_paths` |
| `entity.concorde.alignment-explorer` | program | Validates optional pinned graph/evidence and returns a bounded evidence-qualified read-only Tool result. | `src/concorde/alignment.py#explore_alignment` |
| `entity.concorde.installer` | program | Previews and applies one digest-owned native package plus its isolated `.concorde/.venv` Operation runtime to Codex or Claude projects. | `scripts/install-concorde.py` |
| `entity.concorde.agent-surface-sync` | program | Verifies or refreshes this checkout's generated integration surfaces from canonical capabilities/assets. | `scripts/development/sync-agent-surfaces.py` |
| `entity.concorde.specification` | directory | Concorde's self-applied module architectures and direct feature authorities. | `specs/concorde` |
| `entity.concorde.control-state` | directory | Project configuration, selection, constitution, attempts, reflections, and native install ownership. | `.concorde` |
| `entity.concorde.coding-agent` | external-system | Host that follows installed leaf or Operation skills and authors only explicitly authorized sources. | `external:coding-agent` |
| `entity.concorde.archify` | external-system | Renderer for architecture-owned explanatory diagrams. | `external:archify` |
| `entity.concorde.understand-anything` | external-system | Optional executable graph provider for evidence-qualified alignment exploration. | `external:Egonex-AI/Understand-Anything@ba450c4` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.scripts` | Inventories distributable deterministic entry points. |
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.skills` | Inventories every leaf Skill by globally unique safe name. |
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.operations` | Inventories every exact Python/Markdown Operation pair. |
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.templates` | Inventories every complete Markdown format reference. |
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.runtime` | Pins the runtime profile/protocol shipped in the native package. |
| `entity.concorde.package-manifest` | `declares` | `module.concorde.auto-docs` | Inventories the docsite adapter as the packaged template root. |
| `module.concorde.skills` | `calls` | `module.concorde.runtime` | Leaf Skills request deterministic workspace and lifecycle Tools. |
| `module.concorde.skills` | `reads_from` | `module.concorde.workspace` | Leaf Skills use bounded durable/control/executable paths for a selected feature. |
| `module.concorde.operations` | `composes` | `module.concorde.skills` | LangGraphs sequence canonical leaf Skills by effect-declared occurrence without duplicating prompts. |
| `module.concorde.operations` | `depends_on` | `module.concorde.runtime` | Uses shared package parsing and may cause Skills to invoke Tools. |
| `module.concorde.runtime` | `validates` | `module.concorde.workspace` | Loads and checks the Profile 7 authority model used by every Tool. |
| `module.concorde.distribution` | `reads_from` | `entity.concorde.package-manifest` | Installs one allowlisted package from the native package identity. |
| `entity.concorde.installer` | `transforms` | `entity.concorde.skills` | Projects canonical leaf Skills into the selected integration. |
| `entity.concorde.installer` | `transforms` | `entity.concorde.operations` | Installs each pair, provisions its pinned dependency in `.concorde/.venv`, and projects its Markdown through the managed bootstrap. |
| `entity.concorde.installer` | `provides` | `entity.concorde.coding-agent` | Installs owned framework, verified Operation runtime, and agent surfaces under preview/apply control without touching a project `.venv`. |
| `entity.concorde.agent-surface-sync` | `transforms` | `entity.concorde.skills` | Keeps checkout leaf Skill projections byte-current. |
| `entity.concorde.agent-surface-sync` | `transforms` | `entity.concorde.operations` | Keeps checkout Operation skill projections byte-current. |
| `module.concorde.auto-docs` | `reads_from` | `module.concorde.workspace` | Builds only from validated module architecture, direct feature, and architecture-owned diagram sources. |
| `module.concorde.auto-docs` | `calls` | `entity.concorde.archify` | Renders declared architecture views before site publication. |
| `entity.concorde.workspace-resolver` | `reads_from` | `entity.concorde.specification` | Selects exactly one direct feature and its bounded structural context. |
| `entity.concorde.workspace-resolver` | `reads_from` | `entity.concorde.control-state` | Resolves native selection, stable-ID attempt state, and reflection authority. |
| `entity.concorde.cli` | `calls` | `entity.concorde.alignment-explorer` | Dispatches the native read-only exploration Tool and its filters. |
| `entity.concorde.alignment-explorer` | `reads_from` | `entity.concorde.specification` | Projects validated Profile 7 identity and relationship truth. |
| `entity.concorde.understand-anything` | `provides` | `entity.concorde.alignment-explorer` | Supplies optional pinned graph evidence without replacing Concorde identity. |

## Relationship Types

| Predicate | Direction and meaning |
|---|---|
| `composes` | From a controlling Operation to direct Skills or public Operations whose identities/results it sequences without taking ownership or flattening internals. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.concorde.feature-work` | Maintainer invokes a leaf Skill or paired Operation skill. | Resolve Protocol 13; load bounded feature/module/code evidence; execute one phase or a declared LangGraph; invoke Tools explicitly; record attempt evidence. | Intent, architecture, implementation, tests, and temporal state remain reconciled at the completed boundary. | `contract.concorde.workflow`, `contract.skills.workflow-guidance`, `contract.operations.standard-development-loop` |
| `interaction.concorde.install` | Maintainer previews or explicitly applies a checkout through the native installer command. | Read Package Manifest 2; calculate owned file and isolated-runtime actions; reject collisions/symlinks; write framework and 18 projections; provision and verify `.concorde/.venv`; then write the receipt last while retaining two internal leaves only in the framework. | Idempotent Concorde 2.1.0 installation whose Operations start offline, or exact conflict/failure diagnostics in human or stable JSON form. | `contract.concorde.installation`, `interface.concorde.one-command-install` |
| `interaction.concorde.scaffold-docsite` | Maintainer requests a project docsite after initialization. | Verify the configured root architecture; read the packaged docsite template and derive site identity; emit a digest-bound Docsite Scaffold Proposal 1; after explicit acceptance, atomically promote exactly its files. | A project-owned docsite adapter and identity file ready for publication, or exact conflict diagnostics. | `interface.concorde.scaffold-docsite`, `contract.runtime.tools` |
| `interaction.concorde.publish` | Maintainer or CI requests the project read model. | Reject parallel root docs; load validated architecture/features; render declared diagrams; create Build Manifest 10; build a candidate; atomically promote it. | Searchable Architecture/Features site with source provenance and root architecture entry. | `contract.auto-docs.architecture-site` |
| `interaction.concorde.explore` | Maintainer invokes the exploration Tool for a stable subject. | Validate Profile 7; project bounded specification truth; validate optional graph/evidence; reduce absent/stale/invalid evidence to unknown; filter and serialize one Tool result. | Read-only specification and implementation subjects remain distinct with explicit provenance/freshness. | `contract.concorde.alignment-explorer`, `contract.runtime.tools` |
| `interaction.concorde.deliver` | Maintainer invokes the delivery Tool for a complete selected attempt. | Revalidate Proposal 9 eligibility, digest, paths, tasks, checklists, and evidence; remove exactly that stable-ID attempt. | Durable sources remain authoritative with no active attempt or implementation narrative. | `contract.concorde.workflow`, `contract.runtime.tools` |

## Modules

| Module | Responsibility | Boundary interaction |
|---|---|---|
| `module.concorde.skills` | Own canonical leaf phase prompts and capability projection semantics. | Invokes Runtime Tools and reads Workspace. |
| `module.concorde.operations` | Own paired LangGraph multi-Skill workflows and shared graph state/control. | Composes Skills and installs its Markdown pairs as user Skills. |
| `module.concorde.runtime` | Own deterministic path-safe Tools and envelopes. | Reads/validates Workspace and returns structured Tool results. |
| `module.concorde.workspace` | Own source roles, paths, identity, and lifetime rules. | Supplies maintained, temporal, executable, installed, and generated authorities. |
| `module.concorde.distribution` | Own one native package and its installation lifecycle. | Projects Skills/Operations/support assets and provisions their isolated installed Operation runtime. |
| `module.concorde.auto-docs` | Own the validated documentation read model. | Consumes Workspace and Archify outputs. |

## Features

| Feature | Outcome |
|---|---|
| `feature.concorde.workflow` | Carry one direct feature from intent through reconciled implementation and cleanup-only delivery. |
| `feature.concorde.publish-project-docsite` | Scaffold the project docsite from the packaged template and publish validated project knowledge as a searchable site. |
| `feature.concorde.install` | Preview or explicitly apply a checkout through one standalone native installer command without a host framework. |
| `feature.concorde.maintain-agent-surfaces` | Keep generated Codex and Claude leaf/Operation Skill surfaces current. |
| `feature.concorde.record-workflow-reflections` | Preserve one detailed problem per file, then analyze and route it only through reflection triage. |
| `feature.concorde.explore-alignment` | Browse evidence-qualified specification-to-code relationships through a read-only Tool. |
| `feature.concorde.define-project-ontology` | Define and validate recursive module architecture plus Script/Tool/Skill/Operation structure. |
| `feature.concorde.workflow.initialize-architecture` | Propose and apply a minimal reviewed root architecture. |
| `feature.concorde.workflow.retrieve-bounded-context` | Retrieve exactly one module or feature altitude. |
| `feature.concorde.workflow.answer-workflow-questions` | Answer read-only framework questions from bounded sources. |
| `feature.concorde.workflow.manage-feature-workspaces` | Resolve native feature selection and stable-ID temporal paths. |
| `feature.concorde.workflow.specify-behavior` | Author one complete direct feature authority. |
| `feature.concorde.workflow.plan-delivery` | Plan from feature, architecture, code, and tests into one attempt. |
| `feature.concorde.workflow.execute-and-reconcile` | Execute traced tasks and reconcile every affected authority. |
| `feature.concorde.workflow.validate-architecture` | Diagnose layout, identity, capability, relationship, interface, evidence, and freshness state. |
| `feature.concorde.workflow.accept-milestone` | Remove one eligible completed attempt without creating prose history. |
| `feature.concorde.workflow.fast-loop` | Reconcile one eligible small established change without an attempt. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Scripts expose deterministic Tools; public/internal leaf Skills invoke Tools and own effects;
  paired LangGraph Operations compose ordered direct capabilities with explicit controls and
  per-leaf enforced launches.
- Every Operation Python has one associated Markdown skill, and both leaf and Operation skills are
  installed into one global `concorde-*` agent namespace.
- Package Manifest 2, one installation receipt, one isolated installed Operation environment, and
  version 2.1.0 replace independently composed or mixed-layout capability sources; the source root
  `.venv` and installed `.concorde/.venv` remain distinct and no compatibility shim remains.
- Stable architecture identity remains separate from mutable file/symbol locators.
- Understand Anything types remain adapter metadata; only explicit revision-current sidecar claims
  qualify an alignment, and names/similarity never verify one.
- Code and tests remain implementation/evidence; plans and task state remain temporal.
