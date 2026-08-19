---
id: feature.documentation.publish-project-docsite
kind: feature
module: module.concorde.documentation
refines:
  - feature.concorde.publish-project-docsite
scenarios:
  - publish-project-docsite
contracts:
  provided:
    - contract.documentation.architecture-site
    - contract.documentation.build-interface
    - contract.documentation.build-manifest
  required:
    - contract.documentation.project-content
    - contract.documentation.archify-renderer
architecture_view: architecture/concorde/modules/documentation/architecture.json
evidence_status: verified
canonical_spec: specs/002-create-project-docsite/spec.md
---

# Publish the project docsite

## Outcome

The Documentation module projects canonical Concorde architecture Markdown, project Markdown, and
Spec Kit feature specifications into one searchable, traceable, read-only website, embedding each
declared delivered Archify view beside its textual architecture source.

## Structural refinement

This feature realizes `feature.concorde.publish-project-docsite` inside the Documentation boundary. Its
behavioral requirements remain canonical in `specs/002-create-project-docsite/spec.md`; this document
owns only module placement, boundary contracts, scenario identity, and evidence links.

## Representative scenario

**ID**: `publish-project-docsite`

A maintainer invokes the documented build interface. Documentation consumes architecture Markdown,
project Markdown, and canonical `spec.md` files through `contract.documentation.project-content`,
associates declared Archify JSON with delivered HTML, validates and renders the read model, emits
`contract.documentation.build-manifest`, and provides
`contract.documentation.architecture-site` to the maintainer's browser. The ordered structural trace
is maintained in the Documentation module's `architecture.json`.

## Expected evidence

- Source discovery, validation, route, provenance, search, and manifest tests under `docsite/tests/`.
- Reproducible production output from `docsite/`.
- Requirement-to-evidence mapping in `specs/002-create-project-docsite/validation.md`.
