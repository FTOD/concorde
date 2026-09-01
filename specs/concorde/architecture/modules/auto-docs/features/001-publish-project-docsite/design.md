---
id: feature.auto-docs.publish-project-docsite
kind: feature
module: module.concorde.auto-docs
refines:
  - feature.concorde.publish-project-docsite
scenarios:
  - publish-project-docsite
contracts:
  provided:
    - contract.auto-docs.architecture-site
    - contract.auto-docs.build-interface
    - contract.auto-docs.build-manifest
  required:
    - contract.auto-docs.project-content
    - contract.auto-docs.archify-renderer
evidence_status: verified
canonical_design: specs/concorde/architecture/modules/auto-docs/features/001-publish-project-docsite/design.md
---

# Feature Design: Publish the Project Docsite

**Feature Branch**: Not created; this is an Auto-Docs-module refinement

**Created**: 2026-08-20

**Status**: Implemented

## Outcome

The Auto-Docs module projects the root `README.md` introduction, architecture plus permanent feature specifications and designs from the unified `specs/`
hierarchy, and project Markdown from `docs/` into one searchable, traceable, read-only website, embedding each
declared delivered Archify view beside its textual architecture source.

## Structural Refinement

This feature realizes `feature.concorde.publish-project-docsite` inside the Auto-Docs boundary.
The parent specification owns the project-wide outcome; this specification owns the Auto-Docs
module's narrower behavior, contracts, scenario examples, and evidence links.

## User Scenarios & Testing

### User Story 1 - Publish the Maintained Project Model (Priority: P1)

As a maintainer, I can build one site from the project's maintained specifications and documentation
so that I can inspect architecture and feature intent without treating generated pages as authority.

**Independent Test**: Build from a fixture containing a root README, a module, a contract, a nested feature spec/design pair,
and project documentation; verify the homepage plus three distinct views, canonical provenance, and no source mutation.

**Acceptance Scenarios**:

1. **Given** module, contract, and permanent feature specifications/designs under `specs/`, **When** the site is built,
   **Then** Architecture and Features are separate views of that same hierarchy.
2. **Given** root `README.md` and project Markdown under `docs/`, **When** the site is built, **Then**
   the README owns `/`, Documentation is a third view, and every page points back to its canonical source.
3. **Given** unchanged canonical inputs, **When** the site is built twice, **Then** its manifest and
   source-to-route mappings are identical.

## Representative Scenario Example

**ID**: `publish-project-docsite`

A maintainer invokes the documented build interface. Auto-Docs consumes root `README.md`, module and
contract specifications, project Markdown, and canonical feature `abstract.md`/`design.md`/`implementation.md` trios through
`contract.auto-docs.project-content`,
associates declared Archify JSON with delivered HTML, validates and renders the read model, emits
`contract.auto-docs.build-manifest`, and provides
`contract.auto-docs.architecture-site` to the maintainer's browser. The ordered structural trace
is maintained in the Auto-Docs module's `architecture/diagrams/level-view.json`.

This scenario illustrates one normal interaction; it does not replace the feature's textual outcome
and requirements.

## Diagram Decision

The parent feature's `diagrams/project-docsite-publication-flow.json` sequence explains invocation from the
build command through registry, Archify, materialization, Docusaurus, validation, and publication.
The Auto-Docs module's level view (`architecture/diagrams/level-view.json`) remains the canonical bounded structural trace. A
second child sequence would duplicate those two complementary views.

## Requirements

- **FR-DOC-001**: The module MUST classify `specs/**/module.md`, its sibling `design.md`,
  `specs/**/architecture/contracts/**/contract.md`, and every diagram beneath
  `specs/**/architecture/diagrams/` as the
  Architecture view without moving their authority or treating a renderer projection as maintained content.
- **FR-DOC-002**: The module MUST classify `specs/**/abstract.md`, `specs/**/design.md`, and the feature-root `specs/**/implementation.md` beside a `design.md` as the Features
  view and exclude temporal implementation artifacts from that view.
- **FR-DOC-003**: Architecture MUST preserve declared module containment; Features MUST group
  top-level features by that owning module hierarchy and preserve explicit parent/sub-feature
  containment inside each module group, without deriving navigation from raw storage segments.
- **FR-DOC-004**: The module MUST publish root `README.md` as the one-file homepage at `/` and expose
  project documentation from `docs/` as a third view, while `specs/` and `docs/` remain the two
  recursive canonical source trees.
- **FR-DOC-005**: Any renderer-specific staging MUST be disposable, ignored, regenerated from the
  canonical registry, and invisible in published provenance.

## Success Criteria

- **SC-DOC-001**: The root README and every eligible module, boundary contract, feature specification, feature design, and project document
  appears exactly once in the build manifest.
- **SC-DOC-002**: Two builds from identical inputs produce identical manifests.
- **SC-DOC-003**: Validation and build operations produce zero changes to `README.md` or under `specs/` and `docs/`.

## Expected evidence

- Source discovery, validation, route, provenance, search, and manifest tests under `docsite/tests/`.
- Reproducible production output from `docsite/`.
- Requirement-to-evidence mapping in `specs/concorde/features/002-auto-docsite/implementation.md`.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Published project model` | The read-only website projection of maintained architecture, feature, README, and documentation sources. | `contains` → `Architecture collection`; `contains` → `Features collection`; `contains` → `Documentation collection` |
| `Architecture collection` | Published module summaries, module design references, contracts, and level views organized by module containment. | `is part of` → `Published project model` |
| `Features collection` | Published durable feature abstracts, designs, and accepted implementations organized by module and feature containment. | `is part of` → `Published project model` |
| `Documentation collection` | Published root README and project-authored guides organized by documentation paths. | `is part of` → `Published project model` |
