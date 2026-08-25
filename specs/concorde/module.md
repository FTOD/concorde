---
id: module.concorde
kind: module
parent: null
view: specs/concorde/architecture.json
children:
  - module.concorde.distribution
  - module.concorde.spec-kit-integration
  - module.concorde.architecture-core
  - module.concorde.documentation
features:
  - feature.concorde.workflow
  - feature.concorde.publish-project-docsite
  - feature.concorde.install-with-spec-kit
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

## Current-Level Features

| Feature ID | Outcome | Canonical specification |
|---|---|---|
| `feature.concorde.workflow` | A maintainer directs feature development through a recursive specification hierarchy, architecture review gates, bounded context, and deterministic validation. | `specs/concorde/features/001-concorde-workflow/spec.md` |
| `feature.concorde.publish-project-docsite` | A maintainer browses architecture sources and views, project documentation, and Spec Kit feature specifications in one generated site. | `specs/concorde/features/002-create-project-docsite/spec.md` |
| `feature.concorde.install-with-spec-kit` | A maintainer inspects, installs, verifies, updates, and removes Concorde through the native Spec Kit ecosystem. | `specs/concorde/features/003-install-concorde-speckit/spec.md` |

## Invocation at the Root Level

The feature nodes in `architecture.json` are observable capabilities, not additional runtime
services. They make it possible to read the root view from user intent to the immediate modules that
provide the behavior:

| Entry path | Root feature invoked | Immediate modules involved |
|---|---|---|
| A maintainer uses Spec Kit's bundle inspect, install, update, or removal operations. | `feature.concorde.install-with-spec-kit` | Distribution owns the bundle lifecycle; Spec Kit Integration supplies and activates the preset and command extension. |
| A maintainer or coding agent runs normal Spec Kit phases, together with `speckit.concorde.init`, `feature.create`, `feature.select`, `feature.harden`, `context`, or `validate`. | `feature.concorde.workflow` | Spec Kit Integration selects the nested workspace and composes phase guidance; Architecture Core initializes, projects bounded context, validates architecture, and safely promotes completed milestones into durable feature design. |
| A maintainer validates, builds, serves, or browses the generated project site. | `feature.concorde.publish-project-docsite` | Documentation builds the read model from validated Architecture Core sources and canonical Spec Kit feature specifications. |

The root view intentionally stops here. Zooming into an immediate module reveals that module's own
features, contracts, and submodules without exposing them prematurely at the root level.

## Boundary Contracts

| Contract ID | Role | Flow | Counterparty | Canonical definition |
|---|---|---|---|---|
| `contract.concorde.workflow` | provided | bidirectional | Maintainer and coding agent | `contracts/concorde-workflow/contract.md` |
| `contract.documentation.architecture-site` | provided through Documentation | output | Maintainer browser | `modules/documentation/contracts/architecture-site/contract.md` |
| `contract.concorde.spec-kit-installation` | provided | bidirectional | Maintainer and Spec Kit | `contracts/spec-kit-installation/contract.md` |
| `contract.concorde.spec-kit-platform` | required | bidirectional | Spec Kit | `contracts/spec-kit-platform/contract.md` |

## Immediate Submodules

| Module | Responsibility | Provided I/O at this level | Required I/O at this level |
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

Concorde is installed through Spec Kit rather than alongside it as a second orchestrator. The package
types divide responsibility as follows:

| Package or host | Responsibility at this boundary |
|---|---|
| Spec Kit | Owns component resolution and provenance plus the normal feature-development lifecycle. |
| Component catalogs | Advertise independently packaged bundle, preset, and extension archives with location, compatibility, digest, and trust metadata. |
| `concorde-starter` bundle | Pins and groups the accepted Concorde components as one inspectable installation recipe. |
| `concorde-core` preset | Composes architecture-aware templates and selected-workspace routing into nine existing Spec Kit lifecycle commands. |
| `concorde` extension | Supplies six portable Concorde-specific commands, the workspace adapter, and deterministic Architecture Core runtime. |
| Coding-agent integration | Materializes resolved normal-command overrides and Concorde-specific commands in its native skill or slash-command syntax. |
| Concorde Architecture Core | Maintains bounded hierarchy, context, and validation under the shared `specs/` tree. |

The detailed <a href="/architecture/concorde-spec-kit-component-model.html">component model</a> and
<a href="/architecture/concorde-starter-installation-flow.html">installation flow</a> are
supplemental Feature 003 explanatory views. Their maintained sources are
`features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json` and
`features/003-install-concorde-speckit/diagrams/starter-installation-flow.json`. `architecture.json` remains
the canonical one-level root module view. Feature 001 owns the core
`features/001-concorde-workflow/diagrams/concorde-workflow-components.json` component-interaction model, and Feature
002 owns `features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json`. Feature-owned
views are encouraged explanations of scenario collaboration; they do not expand or replace the root
module view.

## Scenario Trace

The Concorde workflow, installation, and publication scenarios are maintained in their respective feature
specifications and traced in `architecture.json`. They show only this module's immediate children and
permitted external actors.

## Evidence Status

The root and Documentation views pass all 9 Archify showcase checks with zero errors or warnings.
The two supplemental Feature 003 component and installation views also pass all 9 showcase checks,
desktop containment at four target viewports, and perceptual light/dark review.
The Feature 001 core component view and Feature 002 supplemental publication sequence pass all 9 showcase
checks with zero errors or warnings and have fresh provenance-bearing deliveries. Their browser
containment and perceptual review remain pending because Chrome/Chromium is unavailable in the
current validation environment.
The Documentation publication feature is implemented and verified by the feature's unit, contract,
integration, production-build, repeatability, and source-immutability evidence in
`specs/concorde/features/002-create-project-docsite/implementation/validation.md`. Both maintained architecture hierarchies and their
delivered views are published as a distinct Architecture collection. Browser containment and
light/dark perceptual review of the current root and Documentation artifacts remain pending because
Chrome/Chromium is unavailable in the validation environment; structural checks are not treated as
perceptual evidence.
The Spec Kit bundle lifecycle and component registration are implemented, while the installation
feature remains `partial` until all nine normal command overrides and six Concorde-specific commands
execute from release-installed artifacts in clean skills and slash-command projects, preset
recomposition is verified, and the timed first-use and comprehension pilot is conducted. The Concorde workflow has verified
initialization, nested feature placement/selection, public preset command composition, bounded
active-feature context, architecture readiness, contract example conformance, evidence disagreement,
freshness normalization, and deterministic validation. Its human placement, mental-model, and final
review evidence remains pending.
