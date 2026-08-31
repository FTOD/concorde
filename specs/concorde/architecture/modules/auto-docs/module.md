---
id: module.concorde.auto-docs
kind: module
parent: module.concorde
children: []
features:
  - feature.auto-docs.publish-project-docsite
contracts:
  provided:
    - contract.auto-docs.architecture-site
    - contract.auto-docs.build-interface
    - contract.auto-docs.build-manifest
  required:
    - contract.auto-docs.project-content
    - contract.auto-docs.archify-renderer
---

# Auto-Docs

## Responsibility

Publish validated Concorde sources as a hierarchical, searchable, accessible, and browsable read model.

## Boundary

Auto-Docs owns generated navigation, pages, provenance, textual summaries, and embedded diagrams.
It does not own maintained architecture intent, validation semantics, Archify rendering, or user-authored
sources.

## Structure

The maintained level view is
[level-view.json](architecture/diagrams/level-view.json), the one diagram under this module's
`architecture/diagrams/`, delivered as
`generated/architecture/auto-docs.html`. It shows Auto-Docs (the validated read model) inside
its module boundary, its external providers Project Content (root `README.md` plus `docs/**/*.md`),
Project Specifications (`specs/**`), and Archify (validated HTML views), and the Maintainer who builds and browses. The
Feature 002 supplemental
<a href="/architecture/project-docsite-publication-flow.html">publication flow</a> (maintained source
`specs/concorde/features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json`)
explains the build sequence without redefining this structure.

## Features

| Feature ID | Outcome | Refines | Specification |
|---|---|---|---|
| `feature.auto-docs.publish-project-docsite` | Root `README.md`, architecture sources, project docs, feature specifications, and accepted realizations from `docs/` and the unified `specs/` hierarchy become one searchable, traceable, read-only website, with each declared delivered Archify view embedded beside its textual source. | `feature.concorde.publish-project-docsite` | [design.md](features/001-publish-project-docsite/design.md) |

## Contracts

| Contract ID | Role | Flow | Counterparty | Definition |
|---|---|---|---|---|
| `contract.auto-docs.architecture-site` | provided | output | Maintainer browser | [contract.md](architecture/contracts/architecture-site/contract.md) |
| `contract.auto-docs.build-interface` | provided | bidirectional | Maintainer and CI | [contract.md](architecture/contracts/build-interface/contract.md) |
| `contract.auto-docs.build-manifest` | provided | output | Maintainer and freshness checks | [contract.md](architecture/contracts/build-manifest/contract.md) |
| `contract.auto-docs.project-content` | required | input | Workspace Files, maintainers, and Spec Kit | [contract.md](architecture/contracts/project-content/contract.md) |
| `contract.auto-docs.archify-renderer` | required | bidirectional | Archify | [contract.md](architecture/contracts/archify-renderer/contract.md) |

## Submodules

None.

## Representative Scenario

`publish-project-docsite` is maintained in `architecture/diagrams/level-view.json` and uses only this module, its declared
external providers and consumer, and the governing boundary contracts. A maintainer invokes the
documented build interface across `contract.auto-docs.build-interface`. Auto-Docs consumes
the root `README.md`, project Markdown from `docs/`, and architecture, contract, and canonical feature sources from `specs/`
through `contract.auto-docs.project-content`, hands every diagram beneath each module's
`architecture/diagrams/` and every declared feature diagram to Archify
through `contract.auto-docs.archify-renderer` and receives rendered views, then validates
identities, links, and routes. It emits the deterministic `contract.auto-docs.build-manifest` and
provides the finished HTML site through `contract.auto-docs.architecture-site`; when any step
fails, the last successful site is preserved.

## Design Rationale

Auto-Docs is a projection, never an authority: root `README.md` owns the project introduction,
`docs/` owns project documentation, `specs/` owns architecture and feature intent, and generated pages link canonical sources instead of copying them.
Publication is gated so the site can never silently disagree with validated sources: every declared
view must be deliverable, links map strictly, provenance and the manifest are deterministic, and
promotion is atomic. Realization detail and recorded decisions are in the
[design reference](design.md).

## Evidence Status

The publication feature is implemented with executable evidence in `docsite/tests/` and
`specs/concorde/features/002-create-project-docsite/design.md`; details are in the
[design reference](design.md#evidence-status).
