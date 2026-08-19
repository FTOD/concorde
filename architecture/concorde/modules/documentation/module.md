---
id: module.concorde.documentation
kind: module
parent: module.concorde
children: []
view: architecture/concorde/modules/documentation/architecture.json
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

## Feature Set

| Feature ID | Outcome | Parent refinement | Structural definition |
|---|---|---|---|
| `feature.documentation.publish-project-docsite` | Architecture sources, project docs, and feature specs become one generated read model. | `feature.concorde.publish-project-docsite` | `features/publish-project-docsite.md` |

## Boundary Contracts

The feature's canonical contract definitions are split under `contracts/` so representations,
compatibility, and evidence can evolve together without duplicating them in this module summary.

| Contract ID | Role / flow | Counterparty | Canonical definition |
|---|---|---|---|
| `contract.documentation.architecture-site` | provided / output | Maintainer browser | `contracts/architecture-site/contract.md` |
| `contract.documentation.build-interface` | provided / bidirectional | Maintainer and CI | `contracts/build-interface/contract.md` |
| `contract.documentation.build-manifest` | provided / output | Maintainer and freshness checks | `contracts/build-manifest/contract.md` |
| `contract.documentation.project-content` | required / input | Maintainers and Spec Kit | `contracts/project-content/contract.md` |
| `contract.documentation.archify-renderer` | required / bidirectional | Archify | Inline bootstrap definition below |

## Bootstrap Contract Definitions

### `contract.documentation.archify-renderer`

- **Role / flow**: required, bidirectional.
- **Provider**: external Archify.
- **Representation**: commonly adopted Archify architecture JSON schema and generated HTML contract.
- **Guarantees required**: valid maintained JSON produces deterministic, self-contained diagram output.
- **Failure**: renderer diagnostics are preserved and publication stops for the affected view.
- **Evidence**: both maintained architecture views pass all 9 Archify showcase checks; deterministic
  delivery receipts and the publication test evidence are recorded under `generated/architecture/`
  and `specs/002-create-project-docsite/validation.md`. Browser visual review remains pending because
  Chrome or Chromium is unavailable in the implementation environment.

## Scenario Trace

`publish-project-docsite` is maintained in `architecture.json` and uses only this module, its declared
external providers/consumer, and the governing boundary contracts.

## Evidence Status

The publication feature is implemented. Its locked dependency installation, validation interface,
three-collection source discovery, strict link mapping, canonical-only feature projection, sandboxed
Archify embedding, local search, accessible presentation, schema-valid manifest, atomic promotion,
repeatability, and source immutability all
have executable evidence in `docsite/tests/` and `specs/002-create-project-docsite/validation.md`.
