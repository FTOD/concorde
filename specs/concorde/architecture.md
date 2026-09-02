---
id: module.concorde
kind: module
parent: null
modules:
  - module.concorde.skills
  - module.concorde.scripts
  - module.concorde.workspace-files
  - module.concorde.distribution
  - module.concorde.auto-docs
features:
  - feature.concorde.workflow
  - feature.concorde.publish-project-docsite
  - feature.concorde.install-with-spec-kit
  - feature.concorde.self-host-framework
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
  - feature.concorde.install-with-spec-kit.publish-release
  - feature.concorde.install-with-spec-kit.one-command-install
diagrams: []
---

# Architecture: Concorde

## Responsibility

Provide an installable, skill-guided development workflow in which recursive module architecture,
level-local feature interfaces, current source code, executable evidence, and project-control workflow
state have explicit and non-overlapping authority.

## Boundary

Concorde owns its preset and extension package sources, installed workflow instructions, portable
launchers and deterministic Python runtime, workspace source profile, component distribution,
self-hosting transaction, and optional documentation/exploration projections. It does not own the
coding-agent runtime, Spec Kit's base lifecycle, user product code, Archify rendering semantics,
Docusaurus internals, or Understand Anything's graph semantics.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `module.concorde.skills` | module | User-visible authoring instructions and templates that compose Concorde with Spec Kit phases. | `specs/concorde/modules/skills/architecture.md` |
| `module.concorde.scripts` | module | Deterministic runtime operations, safe routing, launchers, and structured diagnostics. | `specs/concorde/modules/scripts/architecture.md` |
| `module.concorde.workspace-files` | module | Canonical paths, source roles, lifetimes, selection, attempt state, and delivery cleanup rules. | `specs/concorde/modules/workspace-files/architecture.md` |
| `module.concorde.distribution` | module | Versioned preset/extension/bundle packaging, catalogs, installation, and release verification. | `specs/concorde/modules/distribution/architecture.md` |
| `module.concorde.auto-docs` | module | Validation-gated read-only projection of module architectures, feature designs, and project documents. | `specs/concorde/modules/auto-docs/architecture.md` |
| `entity.concorde.preset-package` | directory | Canonical Spec Kit phase commands and templates distributed as the Concorde preset. | `presets/concorde` |
| `entity.concorde.extension-package` | directory | Canonical Concorde-specific commands, launchers, runtime, and reflection agent assets. | `extensions/concorde` |
| `entity.concorde.runtime` | package | Deterministic implementation of repository loading, context, validation, initialization, delivery, and projection. | `extensions/concorde/runtime/concorde` |
| `entity.concorde.cli` | program | Command dispatcher for initialize, context, validate, deliver, readiness, reflection, and agent-asset operations. | `extensions/concorde/runtime/concorde/cli.py#create_parser` |
| `entity.concorde.workspace-resolver` | program | Resolves one direct feature file, its module architecture/ancestry, related summaries, and stable-ID project-control paths. | `extensions/concorde/runtime/concorde/feature_workspace.py#resolve_phase_paths` |
| `entity.concorde.self-host` | program | Applies canonical package sources through the public installation path and verifies installed projections atomically. | `scripts/development/self-host-concorde.py` |
| `entity.concorde.installer` | program | Installs, updates, or removes the bundle and its preset/extension packages in another project. | `scripts/install-concorde.py` |
| `entity.concorde.release-tooling` | program | Builds reproducible component archives/catalogs and verifies installation from release artifacts. | `scripts/release` |
| `entity.concorde.preset-archive` | resource | Reproducible release projection containing the allowlisted Concorde preset package. | `concept:concorde-preset-<version>.zip` |
| `entity.concorde.extension-archive` | resource | Reproducible release projection containing the allowlisted Concorde extension package. | `concept:concorde-extension-<version>.zip` |
| `entity.concorde.specification` | directory | Concorde's self-hosted durable module architecture, feature designs, and explanatory diagram sources. | `specs/concorde` |
| `entity.concorde.control-state` | directory | Project-wide configuration, stable-ID active attempts, tracked reflection log, and reflection-triage state outside the specification hierarchy. | `.concorde` |
| `entity.concorde.spec-kit` | external-system | Host lifecycle and component materializer into which Concorde composes. | `external:specify-cli==0.16.4` |
| `entity.concorde.coding-agent` | external-system | Agent that follows installed skills, authors maintained files/code, and runs deterministic checks. | `external:coding-agent` |
| `entity.concorde.archify` | external-system | Renderer for maintained architecture diagrams and disposable HTML deliveries. | `external:archify` |
| `entity.concorde.understand-anything` | external-system | Optional implementation graph provider used by evidence-qualified alignment exploration. | `external:Egonex-AI/Understand-Anything@ba450c4` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.concorde.spec-kit` | `serves` | `entity.concorde.preset-package` | Resolves and composes the preset into normal host phases. |
| `entity.concorde.spec-kit` | `serves` | `entity.concorde.extension-package` | Installs Concorde-specific commands and launchers. |
| `entity.concorde.preset-package` | `provides` | `module.concorde.skills` | Supplies host-phase workflow guidance and templates. |
| `entity.concorde.extension-package` | `provides` | `module.concorde.skills` | Supplies Concorde-specific operation guidance and reflection assets. |
| `module.concorde.skills` | `calls` | `module.concorde.scripts` | Requests deterministic routing, validation, initialization, context, or delivery. |
| `module.concorde.skills` | `reads_from` | `module.concorde.workspace-files` | Uses design, architecture, code context, and attempt memory named by the phase. |
| `module.concorde.skills` | `writes_to` | `module.concorde.workspace-files` | Authors only phase-authorized durable or temporal sources. |
| `module.concorde.scripts` | `validates` | `module.concorde.workspace-files` | Loads Profile 7 sources/control state and returns structured non-mutating findings. |
| `module.concorde.distribution` | `provides` | `entity.concorde.spec-kit` | Publishes the bundle and independently versioned component packages. |
| `module.concorde.auto-docs` | `reads_from` | `module.concorde.workspace-files` | Builds a read model only from validated maintained sources. |
| `module.concorde.auto-docs` | `calls` | `entity.concorde.archify` | Renders declared module diagram sources before publication. |
| `entity.concorde.workspace-resolver` | `reads_from` | `entity.concorde.specification` | Resolves selected `feature_path`, providing architecture, and bounded related summaries. |
| `entity.concorde.workspace-resolver` | `reads_from` | `entity.concorde.control-state` | Resolves stable-ID attempt paths/state and the centralized reflection authority. |
| `entity.concorde.cli` | `calls` | `entity.concorde.runtime` | Dispatches deterministic operations and serializes their envelopes. |
| `entity.concorde.self-host` | `calls` | `entity.concorde.installer` | Uses public component materialization rather than a private installation path. |
| `entity.concorde.release-tooling` | `reads_from` | `entity.concorde.preset-package` | Selects allowlisted canonical preset members. |
| `entity.concorde.release-tooling` | `reads_from` | `entity.concorde.extension-package` | Selects allowlisted canonical extension members. |
| `entity.concorde.release-tooling` | `generates` | `entity.concorde.preset-archive` | Produces a deterministic preset release projection. |
| `entity.concorde.release-tooling` | `generates` | `entity.concorde.extension-archive` | Produces a deterministic extension release projection. |
| `entity.concorde.understand-anything` | `provides` | `entity.concorde.runtime` | Supplies optional graph input; its nodes never replace Concorde architecture identity. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.concorde.feature-work` | Maintainer invokes an installed phase skill. | Skills resolve the selected design/module architecture and stable-ID control paths; the agent reads/writes the declared attempt/code paths; Scripts perform deterministic checks; evidence is recorded before task completion. | Architecture, feature design, code, tests, and project-control attempt remain reconciled at the phase boundary. | `contract.concorde.workflow` |
| `interaction.concorde.install` | Maintainer asks Spec Kit to install the Concorde bundle. | Distribution resolves the pinned preset/extension; Spec Kit previews ownership and compatibility; accepted components and agent projections are materialized and verified. | A repeatable installed workflow or an unchanged project with actionable failure diagnostics. | `contract.concorde.spec-kit-installation`, `contract.concorde.spec-kit-platform` |
| `interaction.concorde.publish` | Maintainer or CI requests documentation. | Auto-Docs loads validated architecture/design/docs sources, invokes Archify for declared views, creates Manifest 10, builds a candidate site, and atomically promotes it. | A searchable read model whose pages retain canonical source provenance. | `contract.auto-docs.architecture-site` |
| `interaction.concorde.deliver` | Maintainer invokes delivery for a complete selected attempt. | Scripts verify task/checklist completion, validation and digest freshness, then atomically remove exactly that attempt. | Code and durable architecture/design remain authoritative with no active attempt and no implementation narrative. | `contract.concorde.workflow` |

## Modules

| Module | Responsibility | Boundary interaction |
|---|---|---|
| `module.concorde.skills` | Compose user/agent instructions and templates. | Calls Scripts and names Workspace Files. |
| `module.concorde.scripts` | Provide deterministic, safe operations and routing. | Reads/validates Workspace Files and returns structured results. |
| `module.concorde.workspace-files` | Define source paths, authority, lifecycle, and selection. | Supplies maintained/temporal input to Skills, Scripts, and Auto-Docs. |
| `module.concorde.distribution` | Package, catalog, install, update, remove, and release Concorde. | Supplies preset/extension/bundle components to Spec Kit. |
| `module.concorde.auto-docs` | Generate a validated read-only site. | Consumes Workspace Files and Archify; serves maintainers. |

## Features

| Feature | Outcome |
|---|---|
| `feature.concorde.workflow` | Direct feature change from design through plan, tasks, code/test reconciliation, and cleanup delivery. |
| `feature.concorde.publish-project-docsite` | Publish validated architecture, feature, and project sources as a searchable site. |
| `feature.concorde.install-with-spec-kit` | Inspect and materialize the supported bundle through Spec Kit. |
| `feature.concorde.self-host-framework` | Prove this checkout installs and composes through the public path. |
| `feature.concorde.record-workflow-reflections` | Preserve unsolved choices/problems, allocate never-used IDs, and remove validated merged-small entries automatically. |
| `feature.concorde.explore-alignment` | Browse evidence-qualified relationships between specification and executable reality. |
| `feature.concorde.define-project-ontology` | Define and validate recursive module architecture, typed entities/relations, and design-only feature interfaces. |
| `feature.concorde.workflow.initialize-architecture` | Propose a minimal reviewed root architecture. |
| `feature.concorde.workflow.retrieve-bounded-context` | Retrieve exactly one module/feature altitude. |
| `feature.concorde.workflow.answer-workflow-questions` | Answer read-only framework questions from bounded sources. |
| `feature.concorde.workflow.manage-feature-workspaces` | Resolve design-only feature phase paths and attempt state. |
| `feature.concorde.workflow.specify-behavior` | Author one feature's outcome, interfaces, usage, requirements, and architecture zoom. |
| `feature.concorde.workflow.plan-delivery` | Turn durable design, bounded architecture, and code/tests into one attempt plan/tasks. |
| `feature.concorde.workflow.execute-and-reconcile` | Execute traced tasks with evidence and reconcile every affected authority. |
| `feature.concorde.workflow.validate-architecture` | Deterministically diagnose layout, entity, relation, interface, evidence, and freshness state. |
| `feature.concorde.workflow.accept-milestone` | Validate and remove a completed temporal attempt without generating implementation prose. |
| `feature.concorde.workflow.fast-loop` | Reconcile one eligible small established change without an attempt. |
| `feature.concorde.install-with-spec-kit.publish-release` | Publish reproducible tagged component archives/catalogs. |
| `feature.concorde.install-with-spec-kit.one-command-install` | Install the supported bundle into a target with one command. |

## Decisions

- Stable architecture IDs are independent of mutable file/symbol locators.
- Module containment is the only specification hierarchy; related features are a graph, not nested packages.
- Architecture includes significant implementation entities but intentionally omits private helper inventory.
- Feature interfaces retain existing `contract.*` IDs during the prototype while ownership moves into designs.
- Canonical preset/extension sources precede installed projections; self-hosting verifies the generated copies.
- Code and tests are implementation/evidence. Git history plus maintained architecture/design and the tracked `.concorde/reflections/log.md` hold durable rationale.
