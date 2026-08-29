---
id: module.concorde.documentation
kind: module
parent: module.concorde
children: []
features:
  - feature.documentation.publish-project-docsite
contracts:
  provided:
    - contract.documentation.architecture-site
    - contract.documentation.build-interface
    - contract.documentation.build-manifest
  required:
    - contract.documentation.project-content
    - contract.documentation.archify-renderer
---

# Documentation

## Responsibility

Publish validated Concorde sources as a hierarchical, searchable, accessible, and browsable read model.

## Boundary

Documentation owns generated navigation, pages, provenance, textual summaries, and embedded diagrams.
It does not own maintained architecture intent, validation semantics, Archify rendering, or user-authored
sources.

## Structure

The maintained level view is
[level-view.json](architecture/diagrams/level-view.json), the one diagram under this module's
`architecture/diagrams/`, delivered as
`generated/architecture/documentation.html`. It shows Documentation (the validated read model) inside
its module boundary, its external providers Project Docs (`docs/**/*.md`), Project Specifications
(`specs/**`), and Archify (validated HTML views), and the Maintainer who builds and browses. The
Feature 002 supplemental
<a href="/architecture/project-docsite-publication-flow.html">publication flow</a> (maintained source
`specs/concorde/features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json`)
explains the build sequence without redefining this structure.

## Features

| Feature ID | Outcome | Refines | Specification |
|---|---|---|---|
| `feature.documentation.publish-project-docsite` | Architecture sources, project docs, feature specifications, and accepted realizations from the unified `specs/` hierarchy and `docs/` become one searchable, traceable, read-only website, with each declared delivered Archify view embedded beside its textual source. | `feature.concorde.publish-project-docsite` | [design.md](features/001-publish-project-docsite/design.md) |

## Contracts

| Contract ID | Role | Flow | Counterparty | Definition |
|---|---|---|---|---|
| `contract.documentation.architecture-site` | provided | output | Maintainer browser | [contract.md](architecture/contracts/architecture-site/contract.md) |
| `contract.documentation.build-interface` | provided | bidirectional | Maintainer and CI | [contract.md](architecture/contracts/build-interface/contract.md) |
| `contract.documentation.build-manifest` | provided | output | Maintainer and freshness checks | [contract.md](architecture/contracts/build-manifest/contract.md) |
| `contract.documentation.project-content` | required | input | Maintainers and Spec Kit | [contract.md](architecture/contracts/project-content/contract.md) |
| `contract.documentation.archify-renderer` | required | bidirectional | Archify | [contract.md](architecture/contracts/archify-renderer/contract.md) |

## Submodules

None.

## Representative Scenario

`publish-project-docsite` is maintained in `architecture/diagrams/level-view.json` and uses only this module, its declared
external providers and consumer, and the governing boundary contracts. A maintainer invokes the
documented build interface across `contract.documentation.build-interface`. Documentation consumes
project Markdown from `docs/` and architecture, contract, and canonical feature sources from `specs/`
through `contract.documentation.project-content`, hands every diagram beneath each module's
`architecture/diagrams/` and every declared feature diagram to Archify
through `contract.documentation.archify-renderer` and receives rendered views, then validates
identities, links, and routes. It emits the deterministic `contract.documentation.build-manifest` and
provides the finished HTML site through `contract.documentation.architecture-site`; when any step
fails, the last successful site is preserved.

## Design Rationale

Documentation is a projection, never an authority: `docs/` owns project documentation, `specs/` owns
architecture and feature intent, and generated pages link canonical sources instead of copying them.
Publication is gated so the site can never silently disagree with validated sources: every declared
view must be deliverable, links map strictly, provenance and the manifest are deterministic, and
promotion is atomic. Realization detail and recorded decisions are in the
[design reference](design.md).

## Evidence Status

The publication feature is implemented with executable evidence in `docsite/tests/` and
`specs/concorde/features/002-create-project-docsite/design.md`; details are in the
[design reference](design.md#evidence-status).
