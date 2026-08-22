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
  - feature.concorde.install-starter-workflow
  - feature.concorde.publish-project-docsite
contracts:
  provided:
    - contract.concorde.starter-workflow
    - contract.documentation.architecture-site
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
| `feature.concorde.install-starter-workflow` | A maintainer installs and exercises a minimal Concorde workflow in a Spec Kit project. | `specs/concorde/features/001-concorde-starter-workflow/spec.md` |
| `feature.concorde.publish-project-docsite` | A maintainer browses architecture sources and views, project documentation, and Spec Kit feature specifications in one generated site. | `specs/concorde/features/002-create-project-docsite/spec.md` |

## Boundary Contracts

| Contract ID | Role | Flow | Counterparty | Canonical definition |
|---|---|---|---|---|
| `contract.concorde.starter-workflow` | provided | bidirectional | Maintainer and coding agent | `contracts/concorde-workflow/contract.md` |
| `contract.documentation.architecture-site` | provided through Documentation | output | Maintainer browser | `modules/documentation/contracts/architecture-site/contract.md` |
| `contract.concorde.spec-kit-platform` | required | bidirectional | Spec Kit | `contracts/spec-kit-platform/contract.md` |

## Immediate Submodules

| Module | Responsibility | Provided I/O at this level | Required I/O at this level |
|---|---|---|---|
| `module.concorde.distribution` | Package and manage the installable Concorde stack. | Bundle preview, install, update, and removal results. | Versioned preset and extension component packages. |
| `module.concorde.spec-kit-integration` | Compose Concorde into Spec Kit and expose portable agent commands. | Architecture-aware artifacts and registered agent skills. | Spec Kit extension points and Architecture Core services. |
| `module.concorde.architecture-core` | Define, retrieve, and validate bounded Concorde architecture sources. | Architecture initialization, context, and validation results. | Explicit empty set for the starter slice. |
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
| `concorde-core` preset | Appends architecture-aware guidance to Spec Kit's existing spec, plan, and task artifacts. |
| `concorde` extension | Registers portable agent commands that call deterministic Architecture Core services. |
| Coding-agent integration | Presents the installed extension commands in its native skill or slash-command syntax. |
| Concorde Architecture Core | Maintains bounded hierarchy, context, and validation under the shared `specs/` tree. |

The detailed <a href="/architecture/concorde-spec-kit-component-model.html">component model</a> and
<a href="/architecture/concorde-starter-installation-flow.html">installation flow</a> are
supplemental explanatory views. Their maintained sources are
`features/001-concorde-starter-workflow/spec-kit-component-model.json` and
`features/001-concorde-starter-workflow/starter-installation-flow.json`. `architecture.json` remains
the canonical one-level root module view.

## Scenario Trace

The primary scenarios `install-starter-workflow` and `publish-architecture` are maintained in their
feature specifications and traced in `architecture.json`. They show only this module's immediate
children and permitted external actors.

## Evidence Status

The root and Documentation views pass all 9 Archify showcase checks with zero errors or warnings.
The two supplemental Feature 001 component and installation views also pass all 9 showcase checks,
desktop containment at four target viewports, and perceptual light/dark review.
The Documentation publication feature is implemented and verified by the feature's unit, contract,
integration, production-build, repeatability, and source-immutability evidence in
`specs/concorde/features/002-create-project-docsite/validation.md`. Both maintained architecture hierarchies and their
delivered views are published as a distinct Architecture collection. Chromium containment checks and
perceptual light/dark review pass for both diagrams at the required desktop viewport extremes.
The starter workflow is implemented and verified across native Spec Kit 0.16.4 lifecycle,
cross-integration command registration, deterministic Architecture Core behavior, and self-validation.
Its evidence remains `partial` only because the timed first-use and comprehension participant pilots
for SC-001, SC-009, and SC-011 have not yet been conducted.
