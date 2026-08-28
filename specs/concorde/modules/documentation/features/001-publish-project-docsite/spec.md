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
architecture_view: specs/concorde/modules/documentation/architecture.json
evidence_status: verified
canonical_spec: specs/concorde/modules/documentation/features/001-publish-project-docsite/spec.md
---

# Feature Specification: Publish the Project Docsite

**Feature Branch**: Not created; this is a Documentation-module refinement

**Created**: 2026-08-20

**Status**: Implemented

## Outcome

The Documentation module projects architecture plus permanent feature specifications and designs from the unified `specs/`
hierarchy plus project Markdown from `docs/` into one searchable, traceable, read-only website, embedding each
declared delivered Archify view beside its textual architecture source.

## Structural Refinement

This feature realizes `feature.concorde.publish-project-docsite` inside the Documentation boundary.
The parent specification owns the project-wide outcome; this specification owns the Documentation
module's narrower behavior, contracts, scenario examples, and evidence links.

## User Scenarios & Testing

### User Story 1 - Publish the Maintained Project Model (Priority: P1)

As a maintainer, I can build one site from the project's maintained specifications and documentation
so that I can inspect architecture and feature intent without treating generated pages as authority.

**Independent Test**: Build from a fixture containing a module, a contract, a nested feature spec/design pair,
and project documentation; verify three distinct views, canonical provenance, and no source mutation.

**Acceptance Scenarios**:

1. **Given** module, contract, and permanent feature specifications/designs under `specs/`, **When** the site is built,
   **Then** Architecture and Features are separate views of that same hierarchy.
2. **Given** project Markdown under `docs/`, **When** the site is built, **Then** Documentation is a
   third view and every page points back to its canonical source.
3. **Given** unchanged canonical inputs, **When** the site is built twice, **Then** its manifest and
   source-to-route mappings are identical.

## Representative Scenario Example

**ID**: `publish-project-docsite`

A maintainer invokes the documented build interface. Documentation consumes module and contract
specifications, project Markdown, and canonical feature `spec.md`/`implementation.md` pairs through
`contract.documentation.project-content`,
associates declared Archify JSON with delivered HTML, validates and renders the read model, emits
`contract.documentation.build-manifest`, and provides
`contract.documentation.architecture-site` to the maintainer's browser. The ordered structural trace
is maintained in the Documentation module's `architecture.json`.

This scenario illustrates one normal interaction; it does not replace the feature's textual outcome
and requirements.

## Diagram Decision

The parent feature's `diagrams/project-docsite-publication-flow.json` sequence explains invocation from the
build command through registry, Archify, materialization, Docusaurus, validation, and publication.
The Documentation module's `architecture.json` remains the canonical bounded structural trace. A
second child sequence would duplicate those two complementary views.

## Requirements

- **FR-DOC-001**: The module MUST classify `specs/**/module.md` and
  `specs/**/contracts/**/contract.md` as the
  Architecture view without moving their authority or treating a renderer projection as maintained content.
- **FR-DOC-002**: The module MUST classify `specs/**/spec.md` and `specs/**/implementation.md` as the Features
  view and exclude temporal implementation artifacts from that view.
- **FR-DOC-003**: Both views MUST preserve the same module/feature hierarchy expressed by their source paths and IDs.
- **FR-DOC-004**: The module MUST expose project documentation from `docs/` as a third view while maintaining only
  two canonical source roots: `specs/` and `docs/`.
- **FR-DOC-005**: Any renderer-specific staging MUST be disposable, ignored, regenerated from the
  canonical registry, and invisible in published provenance.

## Success Criteria

- **SC-DOC-001**: Every eligible module, boundary contract, feature specification, feature design, and project document
  appears exactly once in the build manifest.
- **SC-DOC-002**: Two builds from identical inputs produce identical manifests.
- **SC-DOC-003**: Validation and build operations produce zero changes under `specs/` and `docs/`.

## Expected evidence

- Source discovery, validation, route, provenance, search, and manifest tests under `docsite/tests/`.
- Reproducible production output from `docsite/`.
- Requirement-to-evidence mapping in `specs/concorde/features/002-create-project-docsite/implementation.md`.
