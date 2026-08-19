---
id: module.concorde
kind: module
parent: null
view: architecture/concorde/architecture.json
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
| `feature.concorde.install-starter-workflow` | A maintainer installs and exercises a minimal Concorde workflow in a Spec Kit project. | `specs/001-concorde-starter-workflow/spec.md` |
| `feature.concorde.publish-project-docsite` | A maintainer browses architecture sources and views, project documentation, and Spec Kit feature specifications in one generated site. | `specs/002-create-project-docsite/spec.md` |

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

## Scenario Trace

The primary scenarios `install-starter-workflow` and `publish-architecture` are maintained in their
feature specifications and traced in `architecture.json`. They show only this module's immediate
children and permitted external actors.

## Evidence Status

The root and Documentation views pass all 9 Archify showcase checks with zero errors or warnings.
The Documentation publication feature is implemented and verified by the feature's unit, contract,
integration, production-build, repeatability, and source-immutability evidence in
`specs/002-create-project-docsite/validation.md`. Both maintained architecture hierarchies and their
delivered views are published as a distinct Architecture collection. Browser-based diagram visual
review remains pending because Chrome or Chromium was unavailable to Archify's visual-check command.
