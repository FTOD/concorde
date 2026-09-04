---
id: module.concorde
kind: module
parent: null
modules:
  - module.concorde.understanding
  - module.concorde.lifecycle
  - module.concorde.reflections
  - module.concorde.capabilities
  - module.concorde.distribution
  - module.concorde.auto-docs
features:
  - feature.concorde.workflow
  - feature.concorde.define-project-ontology
  - feature.concorde.evolve-protocol
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-system-overview.html
---

# Architecture: Concorde

## Responsibility

Provide a standalone, module-centered development system in which durable architecture and feature
intent, executable reality, evidence, temporal work state, and a permission-bounded capability
structure have explicit, non-overlapping authority, and in which every capability a maintainer or
coding agent needs is owned by exactly one module.

## Boundary

Concorde owns six capability modules: understanding a project, changing one feature through its
lifecycle, recording and triaging reflections, running any capability on a coding agent,
distributing and installing the package, and publishing the documentation read model. It owns the
project-wide file roles those modules share (package manifest, specification, control state, source
code, tests, templates, generated projections), the Package Manifest 2 identity, the complete
normative Concorde Protocol, and the isolated process by which this repository evolves that Protocol
without self-hosting the cutover in an attempt. It does not own a coding-agent/model runtime, a
project's own virtual environment, project product code, Archify rendering, Docusaurus internals, or
Understand Anything graph semantics.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `module.concorde.understanding` | module | Knows what a project is: models it as a validated Profile 7 hierarchy, loads it deterministically, bounds one feature's context and permission paths, explores alignment with code evidence, and answers grounded questions. | `specs/concorde/modules/understanding/architecture.md` |
| `module.concorde.lifecycle` | module | Carries one selected feature from specification through permission-bounded planning, dependency-ordered tasks, reconciled implementation, deterministic validation gates, and cleanup-only delivery, including the bounded fast loop. | `specs/concorde/modules/lifecycle/architecture.md` |
| `module.concorde.reflections` | module | Records one tracked problem per file during workflow phases and triages it through the conditional permission-bounded reflection Operation until maintainer disposition closes it. | `specs/concorde/modules/reflections/architecture.md` |
| `module.concorde.capabilities` | module | Defines how every Concorde capability exists and runs on a coding agent: deterministic Tools behind portable entry points, exposure/effect-declared leaf Skills, acyclic paired LangGraph Operations, per-leaf permission compilation and enforced launch, and identical public projection into Codex and Claude. | `specs/concorde/modules/capabilities/architecture.md` |
| `module.concorde.distribution` | module | Packages, validates, installs, and updates Concorde while preserving identity, integrity, path safety, explicit ownership, and user-authored files. | `specs/concorde/modules/distribution/architecture.md` |
| `module.concorde.auto-docs` | module | Scaffolds and publishes validated module architectures, direct features, and architecture-owned diagrams as one searchable provenance-preserving site. | `specs/concorde/modules/auto-docs/architecture.md` |
| `entity.concorde.package-manifest` | configuration | Concorde 2.1.0 Package Manifest 2: the single version, profile, protocol, and inventory authority for Scripts, 17 leaf Skills, three Operation pairs, templates, the docsite template, the managed Operation runtime, and supported integrations. | `concorde.json` |
| `entity.concorde.protocol` | interface | Complete normative selected-feature change process, including Source Profile, workspace resolution, permission-bounded phases, attempts, reflections, validation, and delivery; Feature Workspace Protocol is one serialized component. | `concept:Concorde Protocol` |
| `entity.concorde.protocol-cutover` | pipeline | Concorde-repository-only procedure that directly evolves normative Protocol semantics from one clean Git checkpoint to one complete validated commit without an attempt or delivery. | `concept:Concorde Protocol evolution` |
| `entity.concorde.git` | external-system | Required version-control boundary for exact bootstrap checkpoints, isolated worktrees, reviewable diffs/commits, merge, abandonment, and revert. | `external:git` |
| `entity.concorde.specification` | directory | Concorde's self-applied module architectures and direct feature files; the maintained project documentation. | `specs/concorde` |
| `entity.concorde.control-state` | directory | Project configuration, feature selection, constitution, stable-ID attempts, the reflection collection, and installed framework, runtime, and receipt state. | `.concorde` |
| `entity.concorde.source-code` | package | The standard-library Python package in which every capability module's programs are realized. | `src/concorde` |
| `entity.concorde.tests` | test | Unit, contract, integration, and acceptance evidence for every capability module. | `tests/concorde` |
| `entity.concorde.templates` | directory | Complete Markdown format references for features, constitutions, plans, tasks, checklists, and reflections, each owned by the capability module that consumes it. | `templates` |
| `entity.concorde.generated` | directory | Disposable diagram and site projections that carry source provenance. | `concept:generated projections` |
| `entity.concorde.coding-agent` | external-system | Codex or Claude host that follows projected Skills and Operations under an enforced policy and authors only explicitly authorized sources. | `external:coding-agent` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.concorde.package-manifest` | `declares` | `module.concorde.capabilities` | Inventories every Script, leaf Skill, and Operation pair by globally unique safe name. |
| `entity.concorde.package-manifest` | `declares` | `entity.concorde.templates` | Inventories every complete Markdown format reference. |
| `entity.concorde.package-manifest` | `declares` | `module.concorde.auto-docs` | Inventories the docsite adapter as the packaged template root. |
| `entity.concorde.protocol` | `governs` | `module.concorde.understanding` | Defines Source Profile, workspace, context, validation, and authority semantics used by every phase. |
| `entity.concorde.protocol` | `governs` | `module.concorde.lifecycle` | Defines the normal selected-feature phases, temporal attempt, and cleanup-only delivery boundary. |
| `entity.concorde.protocol` | `governs` | `module.concorde.reflections` | Defines when process problems are recorded and how their resolution re-enters lifecycle capabilities. |
| `entity.concorde.protocol` | `governs` | `module.concorde.capabilities` | Defines the Tool/Skill/Operation and permission/effect rules under which phases execute. |
| `entity.concorde.protocol-cutover` | `evolves` | `entity.concorde.protocol` | Changes normative Protocol semantics outside the attempt/delivery lifecycle they govern. |
| `entity.concorde.protocol-cutover` | `depends_on` | `entity.concorde.git` | Keeps the valid base and complete target in separate worktrees and records one reviewable transition. |
| `entity.concorde.protocol-cutover` | `writes_to` | `entity.concorde.specification` | Reconciles Constitution, architecture, feature, interface, and guidance semantics directly. |
| `entity.concorde.protocol-cutover` | `writes_to` | `entity.concorde.control-state` | Changes tracked control authorities only when the target Protocol requires it and never creates a cutover attempt. |
| `entity.concorde.protocol-cutover` | `writes_to` | `entity.concorde.source-code` | Reconciles the implementation of the target Protocol in the same cutover. |
| `entity.concorde.protocol-cutover` | `writes_to` | `entity.concorde.tests` | Reconciles executable evidence and requires the complete target checks before merge. |
| `module.concorde.understanding` | `validates` | `entity.concorde.specification` | Loads and deterministically validates the Profile 7 model that every other module reads. |
| `module.concorde.understanding` | `reads_from` | `entity.concorde.control-state` | Resolves native selection, stable-ID attempt state, and reflection state into Protocol 13. |
| `module.concorde.lifecycle` | `calls` | `module.concorde.understanding` | Every phase resolves its workspace, bounded context, and validation through understanding Tools before it changes anything. |
| `module.concorde.lifecycle` | `writes_to` | `entity.concorde.control-state` | Phases create, update, and finally remove exactly one stable-ID attempt. |
| `module.concorde.lifecycle` | `writes_to` | `entity.concorde.specification` | Specification and implementation reconcile module architectures and direct feature files. |
| `module.concorde.lifecycle` | `writes_to` | `entity.concorde.source-code` | Implementation and the fast loop change code only within task-authorized paths. |
| `module.concorde.lifecycle` | `writes_to` | `entity.concorde.tests` | Implementation records executable evidence beside the code it proves. |
| `module.concorde.lifecycle` | `writes_to` | `module.concorde.reflections` | Planning, task generation, implementation, and the fast loop record one problem per file. |
| `module.concorde.reflections` | `composes` | `module.concorde.lifecycle` | Triage routes a reflection through analyze, fast-loop, plan, tasks, implement, and validate as opaque direct capabilities. |
| `module.concorde.capabilities` | `provides` | `module.concorde.understanding` | Declares, validates, launches, and projects the understanding Skills and Tools. |
| `module.concorde.capabilities` | `provides` | `module.concorde.lifecycle` | Declares, permission-bounds, launches, and projects the lifecycle Skills and Operations. |
| `module.concorde.capabilities` | `provides` | `module.concorde.reflections` | Declares, permission-bounds, launches, and projects the triage Operation and its agents. |
| `module.concorde.capabilities` | `reads_from` | `module.concorde.understanding` | Compiles Protocol 13 roles into concrete per-leaf policies before any launch. |
| `module.concorde.capabilities` | `configures` | `entity.concorde.coding-agent` | Renders the Codex permission profile, Claude strict sandbox, or approved outer boundary each leaf runs under. |
| `module.concorde.distribution` | `reads_from` | `entity.concorde.package-manifest` | Installs one allowlisted package from the native package identity. |
| `module.concorde.distribution` | `calls` | `module.concorde.capabilities` | Projects the 18 public capabilities and verifies every installed Operation through the managed launcher. |
| `module.concorde.distribution` | `writes_to` | `entity.concorde.control-state` | Writes the framework projection, the isolated Operation runtime, and the ownership receipt. |
| `module.concorde.auto-docs` | `reads_from` | `entity.concorde.specification` | Publishes only validated architectures, direct features, and architecture-owned diagrams. |
| `module.concorde.auto-docs` | `generates` | `entity.concorde.generated` | Renders diagram deliveries and the site as disposable provenance-bearing projections. |
| `entity.concorde.coding-agent` | `reads_from` | `entity.concorde.specification` | Reads only the bounded architecture and feature context its policy admits. |
| `entity.concorde.source-code` | `realizes` | `entity.concorde.specification` | Code is the actual implementation of every module's entities and features. |
| `entity.concorde.source-code` | `tested_by` | `entity.concorde.tests` | Tests provide bounded executable evidence. |

## Relationship Types

| Predicate | Direction and meaning |
|---|---|
| `composes` | From a controlling Operation or module to direct Skills, public Operations, or the module that owns them, whose identities and results it sequences without taking ownership or flattening internals. |
| `evolves` | From the Concorde-repository cutover process to the normative Concorde Protocol whose semantics it replaces as one validated Git transition. |
| `governs` | From the normative Concorde Protocol to each capability module whose selected-feature behavior it constrains. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.concorde.feature-work` | Maintainer invokes a lifecycle Skill or Operation for one selected feature. | `module.concorde.capabilities` compiles the leaf policy from `module.concorde.understanding` Protocol 13; `module.concorde.lifecycle` runs one phase against `entity.concorde.specification`, `entity.concorde.source-code`, and `entity.concorde.tests`; records evidence in `entity.concorde.control-state`; records problems in `module.concorde.reflections`; validates through `module.concorde.understanding`; delivery removes exactly the attempt. | Intent, architecture, implementation, tests, and temporal state remain reconciled at the completed boundary. | `contract.concorde.workflow` |
| `interaction.concorde.evolve-protocol` | Maintainer explicitly classifies and authorizes a normative Concorde Protocol change from one clean commit with no active attempts. | Create one isolated branch/worktree through `entity.concorde.git`; directly reconcile `entity.concorde.specification`, `entity.concorde.control-state`, `entity.concorde.source-code`, `entity.concorde.tests`, templates, fixtures, and projections without lifecycle capabilities; validate the complete target; review and merge one cutover commit or abandon/revert it on failure. | The valid base remains available until one complete, target-valid Protocol state replaces it without a self-invalidating attempt or compatibility reader. | `interface.concorde.protocol-evolution` |
| `interaction.concorde.install` | Maintainer previews or explicitly applies a checkout through the native installer. | `module.concorde.distribution` reads `entity.concorde.package-manifest`; calculates owned file and isolated-runtime actions; projects 18 public capabilities through `module.concorde.capabilities`; installs the pinned official Understand Anything Viewer inside the managed runtime; writes framework, runtime, and receipt into `entity.concorde.control-state`. | Idempotent Concorde 2.1.0 installation whose Operations and Viewer start offline, or exact conflict diagnostics. | `contract.concorde.installation` |
| `interaction.concorde.publish` | Maintainer or CI requests the project read model. | `module.concorde.understanding` validates `entity.concorde.specification`; `module.concorde.auto-docs` renders declared diagrams and builds a candidate; the candidate is promoted atomically into `entity.concorde.generated`. | Searchable Architecture/Features site with source provenance and a root architecture entry. | `interface.concorde.publish-docsite` |
| `interaction.concorde.reflect` | A phase records a problem or the maintainer selects a triage action. | `module.concorde.lifecycle` writes one document into `module.concorde.reflections`; `module.concorde.reflections` composes `module.concorde.lifecycle` on the chosen route under policies from `module.concorde.capabilities`; maintainer disposition closes the document. | Every retained problem is tracked once and is resolved or dismissed with Git history as its record. | `interface.concorde.reflections` |

## Modules

| Module | Responsibility | Boundary interaction |
|---|---|---|
| `module.concorde.understanding` | Know what a project is. | Validates the specification and supplies bounded context, Protocol 13, and planning context to every other module. |
| `module.concorde.lifecycle` | Change one feature safely from specify to deliver. | Calls understanding, writes specification/code/tests/attempts, and records reflections. |
| `module.concorde.reflections` | Record and resolve process problems. | Receives documents from lifecycle phases and composes lifecycle capabilities during triage. |
| `module.concorde.capabilities` | Run any Concorde capability on a coding agent under an enforced policy. | Provides the Tool, Skill, and Operation mechanism to the three capability modules and configures the coding agent. |
| `module.concorde.distribution` | Ship and install the package. | Reads the manifest, calls capabilities for projection and verification, and writes installed control state. |
| `module.concorde.auto-docs` | Publish the validated read model. | Reads the specification and writes generated projections. |

## Features

| Feature | Outcome |
|---|---|
| `feature.concorde.workflow` | Carry one direct feature from intent through reconciled implementation and cleanup-only delivery using installed capabilities as the sole conversational surface. |
| `feature.concorde.define-project-ontology` | Define and validate the recursive, capability-partitioned module architecture plus the Script/Tool/Skill/Operation structure that every Concorde project, including this one, follows. |
| `feature.concorde.evolve-protocol` | Evolve normative Concorde Protocol semantics directly in one isolated, attempt-free, fully validated Git cutover unique to this self-applying repository. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Child modules are partitioned by capability, use case, and axis of change (constitution A.VI), not
  by artifact type: each owns every Skill, Tool, Operation, template, schema, and rule its capability
  needs. The flat `skills/`, `operations/`, `templates/`, `scripts/`, and `agent-assets/` directories
  are the distribution format fixed by Package Manifest 2; ownership is expressed by stable entity
  identity in the owning module, never by directory.
- The root owns only project-wide features: the end-to-end workflow, the shared ontology, and the
  Concorde-repository-only Protocol-evolution boundary. Every capability-local use case descends to
  the module that provides it.
- Every Concorde project consumes `entity.concorde.protocol`; only this repository defines,
  implements, and self-applies it. Normative Protocol evolution therefore uses
  `entity.concorde.protocol-cutover`, never an attempt, fast loop, standard loop, or delivery.
- Scripts expose deterministic Tools; public/internal leaf Skills invoke Tools and own effects;
  paired LangGraph Operations compose ordered direct capabilities with explicit controls and
  per-leaf enforced launches. Every Operation Python has one associated Markdown skill, and both leaf
  and Operation skills are installed into one global `concorde-*` agent namespace.
- Package Manifest 2, one installation receipt, one isolated installed Operation environment, and
  version 2.1.0 replace independently composed or mixed-layout capability sources; the source root
  `.venv` and installed `.concorde/.venv` remain distinct and no compatibility shim remains.
- Stable architecture identity remains separate from mutable file/symbol locators.
- Code and tests remain implementation/evidence; plans and task state remain temporal; generated
  and installed projections never become specification or implementation authority.
