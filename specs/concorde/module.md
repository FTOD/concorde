---
id: module.concorde
kind: module
parent: null
children:
  - module.concorde.distribution
  - module.concorde.spec-kit-integration
  - module.concorde.architecture-core
  - module.concorde.documentation
features:
  - feature.concorde.workflow
  - feature.concorde.publish-project-docsite
  - feature.concorde.install-with-spec-kit
  - feature.concorde.self-host-framework
  - feature.concorde.record-workflow-reflections
contracts:
  provided:
    - contract.concorde.workflow
    - contract.documentation.architecture-site
    - contract.concorde.spec-kit-installation
  required:
    - contract.concorde.spec-kit-platform
---

# Concorde

## Responsibility

Provide a Spec Kit-native workflow that lets maintainers direct AI-developed software through aligned,
zoomable module and feature hierarchies, explicit boundary contracts, and reviewable evidence.

## Boundary

Concorde owns its distributable bundle, architecture-aware Spec Kit integration, architecture source
model, bounded context, deterministic validation, and generated documentation workflow. It does not
own Spec Kit's core feature lifecycle, the coding agent runtime, Archify rendering semantics, or
Docusaurus itself.

## Structure

This level is composed under `architecture/`: its diagrams (`architecture/diagrams/`), its boundary
contracts (`architecture/contracts/`), and its four immediate modules (`architecture/modules/`),
beside the root features under `features/`. The maintained root level view is
[level-view.json](architecture/diagrams/level-view.json), delivered as
`generated/architecture/concorde-root.html`. It shows three permitted external actors (Maintainer,
Spec Kit, Coding Agent), the five root features (Install with Spec Kit, Self-Host Concorde, Concorde
Workflow, Record Workflow Reflections, Publish Project Docsite), and the four immediate modules
(Distribution, Spec Kit Integration, Architecture Core, Documentation) joined by the boundary
contracts inventoried below. The root view intentionally stops at one level; zooming into a module
reveals that module's own features, contracts, and submodules. Any further diagram of this level
lives beside the level view under `architecture/diagrams/` and is linked from this summary or the
design reference; today the level view is the only module-owned diagram.

Feature-owned explanatory views supplement the root view; they do not expand or replace it:

| View | Owner | Maintained source |
|---|---|---|
| <a href="/architecture/concorde-workflow-components.html">Workflow components</a> | Feature 001 (core) | `features/001-concorde-workflow/diagrams/concorde-workflow-components.json` |
| <a href="/architecture/project-docsite-publication-flow.html">Docsite publication flow</a> | Feature 002 | `features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json` |
| <a href="/architecture/concorde-spec-kit-component-model.html">Spec Kit component model</a> | Feature 003 | `features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json` |
| <a href="/architecture/concorde-bundle-installation-flow.html">Bundle installation flow</a> | Feature 003 | `features/003-install-concorde-speckit/diagrams/bundle-installation-flow.json` |
| <a href="/architecture/concorde-self-hosting-components.html">Self-hosting components</a> | Feature 004 (core) | `features/004-self-host-concorde/diagrams/concorde-self-hosting-components.json` |
| <a href="/architecture/workflow-reflection-components.html">Workflow reflection components</a> | Feature 005 (core) | `features/005-record-workflow-reflections/diagrams/workflow-reflection-components.json` |

## Features

| Feature ID | Outcome | Specification |
|---|---|---|
| `feature.concorde.workflow` | A maintainer directs feature development through a recursive specification hierarchy, architecture review gates, bounded context, and deterministic validation. | [design.md](features/001-concorde-workflow/design.md) |
| `feature.concorde.publish-project-docsite` | A maintainer browses architecture sources and views, project documentation, and Spec Kit feature specifications in one generated site. | [design.md](features/002-create-project-docsite/design.md) |
| `feature.concorde.install-with-spec-kit` | A maintainer inspects, installs, verifies, updates, and removes Concorde through the native Spec Kit ecosystem. | [design.md](features/003-install-concorde-speckit/design.md) |
| `feature.concorde.self-host-framework` | A maintainer installs, refreshes, and verifies the current Concorde framework sources in this same checkout so framework improvements are used during Concorde's own development. | [design.md](features/004-self-host-concorde/design.md) |
| `feature.concorde.record-workflow-reflections` | A coding agent records every difficulty or problem it meets while planning or implementing — about this feature, another feature's existing implementation, a module, the guidance, or a tool — in the project's one reflection log, through the existing phases and no new command; the maintainer reviews it and acceptance cites the feature's entries. | [design.md](features/005-record-workflow-reflections/design.md) |

The feature nodes in the root view are observable capabilities, not runtime services. Each is
reached from user intent through the immediate modules that provide the behavior:

| Entry path | Root feature invoked | Immediate modules involved |
|---|---|---|
| Spec Kit's bundle inspect, install, update, or removal operations | `feature.concorde.install-with-spec-kit` | Distribution owns the bundle lifecycle; Spec Kit Integration supplies and activates the preset and command extension. |
| Install, refresh, or verify the current framework sources in this checkout | `feature.concorde.self-host-framework` | Distribution identifies the authoritative local component set; Spec Kit Integration materializes it through the active integration; Architecture Core contributes deterministic freshness findings. |
| Normal Spec Kit phases, one of four runtime-backed Concorde operations (`init`, `feature.accept`, `context`, `validate`), or a read-only workflow question through `ask` | `feature.concorde.workflow` | Spec Kit Integration resolves the standard Spec Kit selection to the nested workspace, composes phase guidance, and presents all five Concorde surfaces; Architecture Core executes the four deterministic operations; the coding agent answers `ask` directly from cited installed guidance and bounded project sources. |
| Validate, build, serve, or browse the generated project site | `feature.concorde.publish-project-docsite` | Documentation builds the read model from validated Architecture Core sources and canonical Spec Kit feature specifications. |
| A plan, tasks, implement, analyze, or converge phase meets a difficulty or problem | `feature.concorde.record-workflow-reflections` | Spec Kit Integration's phase guidance and log template carry the recording obligation into the project reflection log (`reflections.md` at the specification root); Architecture Core validates the log's shape, exposes it in bounded context, and requires acceptance to cite the feature's open entries. |

## Contracts

| Contract ID | Role | Flow | Counterparty | Definition |
|---|---|---|---|---|
| `contract.concorde.workflow` | provided | bidirectional | Maintainer and coding agent | [contract.md](architecture/contracts/concorde-workflow/contract.md) |
| `contract.documentation.architecture-site` | provided through Documentation | output | Maintainer browser | [contract.md](architecture/modules/documentation/architecture/contracts/architecture-site/contract.md) |
| `contract.concorde.spec-kit-installation` | provided | bidirectional | Maintainer and Spec Kit | [contract.md](architecture/contracts/spec-kit-installation/contract.md) |
| `contract.concorde.spec-kit-platform` | required | bidirectional | Spec Kit | [contract.md](architecture/contracts/spec-kit-platform/contract.md) |

## Submodules

| Module | Responsibility | Provided I/O | Required I/O |
|---|---|---|---|
| `module.concorde.distribution` | Package and manage the installable Concorde stack. | Bundle preview, install, update, and removal results. | Versioned preset and extension component packages. |
| `module.concorde.spec-kit-integration` | Compose architecture-aware guidance into Spec Kit, select nested feature workspaces, and expose portable agent commands. | Architecture-aware lifecycle artifacts, active workspace selection, and registered agent commands. | Spec Kit extension points and Architecture Core services. |
| `module.concorde.architecture-core` | Define, retrieve, and validate bounded Concorde architecture sources. | Architecture initialization, feature placement support, bounded context, and validation results. | Explicit empty set for the current slice. |
| `module.concorde.documentation` | Publish validated sources as a browsable architecture read model. | Generated architecture site. | Validated architecture sources and Archify rendering. |

## Organization Rules

- Distribution MAY depend on the public packaging contracts of Spec Kit Integration but MUST NOT know
  Architecture Core internals.
- Spec Kit Integration MAY invoke Architecture Core only through its documented service contract.
- Documentation MAY consume validated Architecture Core outputs but MUST NOT mutate maintained sources.
- Architecture Core MUST remain independent of agent-specific command syntax and publication tooling.
- External consumers MUST depend on root or child boundary contracts, never child implementation
  details.

## Spec Kit Ecosystem Placement

Concorde is installed through Spec Kit rather than alongside it as a second orchestrator:

| Package or host | Responsibility at this boundary |
|---|---|
| Spec Kit | Owns component resolution and provenance plus the normal feature-development lifecycle. |
| Component catalogs | Advertise the independently packaged bundle, preset, and extension archives with location, compatibility, digest, and trust metadata. |
| `concorde-bundle` bundle | Pins and groups the accepted Concorde components as one inspectable installation recipe. |
| `concorde-core` preset | Composes architecture-aware templates and selected-workspace routing into nine existing Spec Kit lifecycle commands. |
| `concorde` extension | Supplies five Concorde-specific command surfaces: four portable runtime-backed operations plus the read-only, agent-followed `ask` procedure; also ships the workspace adapter and the deterministic Architecture Core runtime. |
| Coding-agent integration | Materializes resolved normal-command overrides and Concorde-specific commands in its native skill or slash-command syntax. |
| Concorde Architecture Core | Maintains the bounded hierarchy, context, and validation under the shared `specs/` tree. |

## Representative Scenario

`scenario-concorde-establish-and-place-feature` is maintained in `architecture/diagrams/level-view.json` and involves the
Maintainer, Spec Kit, the Coding Agent, the Concorde Workflow feature, Spec Kit Integration, and
Architecture Core. A maintainer starts a feature through Spec Kit's normal specify phase, or the
coding agent invokes one Concorde surface, and both paths meet at the Concorde Workflow feature across
`contract.concorde.workflow`. The feature hands the standard Spec Kit selection to Spec Kit
Integration, which resolves the nested feature workspace beneath its providing module and routes the
phase's durable and temporal paths across `contract.integration.feature-workspace`. It then requests
exactly one bounded architectural level from Architecture Core across
`contract.core.architecture-services`, so the maintainer reviews the feature's placement, contracts,
and refinements without reading deeper levels. Distribution and Documentation do not participate; the
companion scenario `scenario-concorde-review-implement-and-reconcile` continues with implementation,
validation, and publication.

## Design Rationale

Concorde is hosted by Spec Kit instead of standing beside it as a second orchestrator: a passive
bundle installs a tested preset and extension pair, and Spec Kit keeps ownership of the feature
lifecycle. Every level of the specification hierarchy separates a summary that is read (`module.md`,
the level view, and the contracts) from a reference that is consulted (`design.md`), so a reader can
stop at one level. Maintained sources remain the only authorities: deterministic validation reports
every breach as a finding, acceptance changes durable documents only under explicit approval, and
generated views and sites are disposable read models. The ideas, alternatives, and decisions behind
this level are recorded in the [design reference](design.md).

## Evidence Status

All maintained and feature-owned views pass Archify showcase checks; the workflow, publication, and
self-hosting features are verified while installation remains `partial`; pending items are listed in
the [design reference](design.md#evidence-status).
