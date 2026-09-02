---
id: module.concorde
kind: module
parent: null
modules:
  - module.concorde.commands
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
  - feature.concorde.release.publish
  - feature.concorde.install.one-command
diagrams: []
---

# Architecture: Concorde

## Responsibility

Provide a standalone, module-centered development workflow in which architecture, feature behavior,
implementation, executable evidence, and temporary work state have explicit, non-overlapping authority.

## Boundary

Concorde owns its root command and template sources, deterministic runtime, project-control model,
agent-surface projection, direct installer, standalone release, evidence-qualified alignment
exploration, and optional documentation projections. It does not own a coding-agent runtime, product
source code, Archify rendering, Docusaurus internals, or Understand Anything graph semantics.
Retained `speckit-*` command IDs are compatibility names; they do not identify a host or dependency.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `module.concorde.commands` | module | Canonical agent instructions, complete Markdown format references, and agent projection. | `specs/concorde/modules/commands/architecture.md` |
| `module.concorde.runtime` | module | Deterministic repository operations, workspace routing, validation, reflection support, and delivery. | `specs/concorde/modules/runtime/architecture.md` |
| `module.concorde.workspace` | module | Durable specification, project control, source/evidence, and projection placement rules. | `specs/concorde/modules/workspace/architecture.md` |
| `module.concorde.distribution` | module | One native package, owned installation, reproducible release, and immutable publication. | `specs/concorde/modules/distribution/architecture.md` |
| `module.concorde.auto-docs` | module | Validation-gated publication of maintained architecture, feature, and documentation sources. | `specs/concorde/modules/auto-docs/architecture.md` |
| `entity.concorde.package-manifest` | configuration | Single package identity and inventory for commands, templates, runtime, protocols, and integrations. | `concorde.json` |
| `entity.concorde.commands` | directory | All canonical lifecycle command instructions, including compatibility-named `speckit.*` commands. | `commands` |
| `entity.concorde.templates` | directory | Complete feature, plan, task, checklist, constitution, and reflection Markdown format references. | `templates` |
| `entity.concorde.agent-assets` | directory | Canonical reflection-triage roles and integration templates. | `agent-assets` |
| `entity.concorde.runtime` | package | Standard-library implementation of the Concorde source, workflow, and read-only alignment contracts. | `src/concorde` |
| `entity.concorde.cli` | program | Structured command dispatcher for initialization, context, exploration, validation, delivery, and agent assets. | `src/concorde/cli.py#create_parser` |
| `entity.concorde.workspace-resolver` | program | Resolves one direct feature, its module/ancestry/relations, and stable-ID control paths. | `src/concorde/feature_workspace.py#resolve_phase_paths` |
| `entity.concorde.alignment-explorer` | program | Validates a pinned optional implementation graph and explicit alignment claims, then returns a bounded evidence-qualified read-only query result. | `src/concorde/alignment.py#explore_alignment` |
| `entity.concorde.installer` | program | Previews and applies one digest-owned native package to Codex or Claude projects. | `scripts/install-concorde.py` |
| `entity.concorde.agent-surface-sync` | program | Verifies or refreshes this checkout's generated integration surfaces from root authorities. | `scripts/development/sync-agent-surfaces.py` |
| `entity.concorde.release-tooling` | program | Builds, verifies, and publishes one deterministic standalone archive and pointer. | `scripts/release` |
| `entity.concorde.specification` | directory | Concorde's self-applied module architectures and direct feature authorities. | `specs/concorde` |
| `entity.concorde.control-state` | directory | Project configuration, selection, constitution, attempts, reflections, and native install ownership. | `.concorde` |
| `entity.concorde.coding-agent` | external-system | Agent that follows projected commands and authors only phase-authorized sources. | `external:coding-agent` |
| `entity.concorde.archify` | external-system | Renderer for architecture-owned explanatory diagrams. | `external:archify` |
| `entity.concorde.understand-anything` | external-system | Optional executable graph provider for evidence-qualified alignment exploration. | `external:Egonex-AI/Understand-Anything@ba450c4` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.commands` | Inventories every distributed command from the root command authority. |
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.templates` | Inventories every complete Markdown format reference. |
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.runtime` | Pins the runtime profile/protocol shipped in the native package. |
| `module.concorde.commands` | `calls` | `module.concorde.runtime` | Requests deterministic workspace, validation, initialization, and delivery operations. |
| `module.concorde.commands` | `reads_from` | `module.concorde.workspace` | Uses bounded durable/control/executable paths returned for the selected feature. |
| `module.concorde.runtime` | `validates` | `module.concorde.workspace` | Loads and checks the same Profile 7 authority model used by every operation. |
| `module.concorde.distribution` | `reads_from` | `entity.concorde.package-manifest` | Builds one allowlisted archive from the native package identity. |
| `entity.concorde.installer` | `transforms` | `entity.concorde.commands` | Renders canonical commands into the selected integration without another composer. |
| `entity.concorde.installer` | `provides` | `entity.concorde.coding-agent` | Installs owned framework and agent surfaces under explicit preview/apply control. |
| `entity.concorde.agent-surface-sync` | `transforms` | `entity.concorde.commands` | Keeps this checkout's Codex and Claude projections byte-current. |
| `module.concorde.auto-docs` | `reads_from` | `module.concorde.workspace` | Builds only from validated maintained architecture, feature, diagram, and documentation sources. |
| `module.concorde.auto-docs` | `calls` | `entity.concorde.archify` | Renders declared architecture views before site publication. |
| `entity.concorde.workspace-resolver` | `reads_from` | `entity.concorde.specification` | Selects exactly one direct feature and its providing structural context. |
| `entity.concorde.workspace-resolver` | `reads_from` | `entity.concorde.control-state` | Resolves native selection, stable-ID attempt state, and the reflection authority. |
| `entity.concorde.cli` | `calls` | `entity.concorde.alignment-explorer` | Dispatches the native read-only `explore` operation and its filters. |
| `entity.concorde.alignment-explorer` | `reads_from` | `entity.concorde.specification` | Projects validated Profile 7 modules, entities, features, interfaces, relationships, and interactions. |
| `entity.concorde.understand-anything` | `provides` | `entity.concorde.alignment-explorer` | Supplies optional pinned graph evidence without replacing Concorde identity. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.concorde.feature-work` | Maintainer invokes a projected lifecycle command. | Resolve one Protocol 12 workspace; read the direct feature/module/code evidence; perform the phase within its authority; run deterministic checks; record attempt evidence. | Feature intent, architecture, implementation, tests, and temporal state remain reconciled at the phase boundary. | `contract.concorde.workflow` |
| `interaction.concorde.install` | Maintainer previews and accepts a native installation. | Read `concorde.json`; calculate owned create/adopt/update/remove actions; reject collisions and symlinks; atomically write one framework projection, selected agent surfaces, defaults, and receipt. | Idempotent standalone installation or an unchanged target with exact conflict diagnostics. | `contract.concorde.installation` |
| `interaction.concorde.publish` | Maintainer or CI requests project documentation. | Load validated maintained sources; render declared diagrams; create Manifest 10; build a candidate; atomically promote it. | Searchable read model with source provenance. | `contract.auto-docs.architecture-site` |
| `interaction.concorde.explore` | Maintainer invokes the native explorer for a stable subject. | Validate Profile 7; project the bounded subject graph; strictly load an optional pinned UA graph and explicit revision-bound sidecar; reduce absent, stale, or invalid evidence to unknown; apply text/status filters; serialize one canonical result. | Read-only architecture and implementation subjects remain distinct while explicit alignments expose provenance, freshness, and bounded status. | `contract.concorde.alignment-explorer` |
| `interaction.concorde.deliver` | Maintainer invokes delivery for a complete selected attempt. | Revalidate eligibility, digest, paths, tasks, checklists, and evidence; remove exactly that stable-ID attempt. | Durable sources remain authoritative with no active attempt or implementation narrative. | `contract.concorde.workflow` |

## Modules

| Module | Responsibility | Boundary interaction |
|---|---|---|
| `module.concorde.commands` | Own canonical phase intent and Markdown formats. | Calls Runtime and reads Workspace. |
| `module.concorde.runtime` | Own deterministic path-safe operations. | Reads/validates Workspace and returns structured results. |
| `module.concorde.workspace` | Own source roles, paths, identity, and lifetime rules. | Supplies maintained, temporal, executable, and generated authorities. |
| `module.concorde.distribution` | Own one native package and its installation/release lifecycle. | Projects Commands/Runtime to supported agent integrations. |
| `module.concorde.auto-docs` | Own the validated documentation read model. | Consumes Workspace and Archify outputs. |

## Features

| Feature | Outcome |
|---|---|
| `feature.concorde.workflow` | Carry one direct feature from intent through reconciled implementation and cleanup-only delivery. |
| `feature.concorde.publish-project-docsite` | Publish validated project knowledge as a searchable site. |
| `feature.concorde.install` | Preview and own one standalone Concorde installation without a host framework. |
| `feature.concorde.maintain-agent-surfaces` | Keep the framework checkout's generated Codex and Claude surfaces current with root commands/assets. |
| `feature.concorde.record-workflow-reflections` | Preserve difficult choices/problems and safely triage eligible merged-small work. |
| `feature.concorde.explore-alignment` | Browse evidence-qualified specification-to-code relationships. |
| `feature.concorde.define-project-ontology` | Define and validate recursive module architecture and direct feature interfaces. |
| `feature.concorde.workflow.initialize-architecture` | Propose and apply a minimal reviewed root architecture. |
| `feature.concorde.workflow.retrieve-bounded-context` | Retrieve exactly one module or feature altitude. |
| `feature.concorde.workflow.answer-workflow-questions` | Answer read-only framework questions from bounded sources. |
| `feature.concorde.workflow.manage-feature-workspaces` | Resolve native feature selection and stable-ID temporal paths. |
| `feature.concorde.workflow.specify-behavior` | Author one complete direct feature authority. |
| `feature.concorde.workflow.plan-delivery` | Plan from feature, architecture, code, and tests into one attempt. |
| `feature.concorde.workflow.execute-and-reconcile` | Execute traced tasks and reconcile every affected authority. |
| `feature.concorde.workflow.validate-architecture` | Diagnose layout, identity, relationship, interface, evidence, and freshness state. |
| `feature.concorde.workflow.accept-milestone` | Remove one eligible completed attempt without creating prose history. |
| `feature.concorde.workflow.fast-loop` | Reconcile one eligible small established change without an attempt. |
| `feature.concorde.release.publish` | Publish immutable verified native release assets. |
| `feature.concorde.install.one-command` | Install a checkout/archive into a target with one explicit apply. |

## Decisions

- Concorde is the lifecycle owner; it no longer has preset, extension, bundle, catalog, or host layers.
- Root commands and templates are readable canonical assets; installed agent files are generated projections.
- `speckit-*` IDs remain temporarily for user muscle memory and are not architectural dependencies.
- One manifest, one archive, one installation receipt, and one version replace independently composed packages.
- Stable architecture identity remains separate from mutable file/symbol locators.
- Understand Anything node/edge types remain adapter metadata; only explicit revision-current sidecar
  claims can qualify an alignment, and names/similarity never verify one.
- Code and tests remain implementation/evidence; plans and task state remain temporal.
