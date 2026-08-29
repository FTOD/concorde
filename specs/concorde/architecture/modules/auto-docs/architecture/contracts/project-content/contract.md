---
id: contract.auto-docs.project-content
kind: contract
module: module.concorde.auto-docs
role: required
flow: input
representation:
  kind: standard
  format: CommonMark with YAML front matter
  version: CommonMark 0.31.2 / YAML 1.2.2
  definition: https://spec.commonmark.org/0.31.2/
counterparties:
  - module.concorde.workspace-files
  - external.project-maintainer
  - external.spec-kit
providers:
  - module.concorde.workspace-files
  - external.project-maintainer
  - external.spec-kit
features:
  - feature.auto-docs.publish-project-docsite
version: 8
evidence:
  tests:
    - docsite/tests/contract/content-sources.test.ts
evidence_status: verified
---

# Project content contract

## Purpose

Provide UTF-8 architecture sources and canonical feature specifications and accepted implementations
from the unified `specs/` hierarchy, plus project documentation from `docs/**/*.md` and its declared
supplemental Archify JSON beneath adjacent `diagrams/` directories, without
relocating or modifying any authority. Architecture publication selects `**/module.md`,
`**/contracts/**/contract.md`, and every module-level `design.md` beside a `module.md` (the module
design reference); feature publication selects feature-root `abstract.md`, `design.md`, and
`implementation.md`, while excluding `attempt/**`. Markdown follows
[CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/); optional front matter follows
[YAML 1.2.2](https://yaml.org/spec/1.2.2/). Complete field, inclusion, link, failure, and compatibility
semantics are defined once in `specs/concorde/features/002-create-project-docsite/contracts/content-sources.md`.

## Information

The boundary carries UTF-8 Markdown and YAML metadata from two maintained roots, project-relative
links, stable feature and architecture identity, and declared Archify JSON view references owned by
modules, features, or custom documentation pages.

## Obligations

- Every eligible valid source is included exactly once and retains its authored meaning.
- Concorde's self-hosting input retains its eight-page framework-guide baseline as ordinary project
  documentation: one landing page, six progressive learning guides, and one nested docsite
  contributor guide.
- The Documentation landing page links to all six learning guides, and every guide that summarizes
  normative architecture, feature, or command behavior links to its included canonical authority.
- Feature IDs are unique; feature kind, module, title, and lifecycle status are present, and every
  feature's accepted implementation and module design reference is published with source provenance.
- Architecture IDs and kinds are explicit; declared JSON views are discovered without generated
  prerequisites and resolve to build-delivered Archify HTML before publication.
- A documentation page may declare only supplemental diagrams directly beneath its adjacent
  `diagrams/` directory; each is embedded on that page with source provenance and a standalone link.
- Project-relative links resolve within or across the two accepted source roots and three published views.
- Temporal plans, tasks, and supporting implementation files are observable exclusions, not
  permanent feature documentation.
- Reads do not change source bytes, metadata, or timestamps.

## Failure Semantics

Unreadable, escaping, ambiguous, malformed, missing-identity, broken-link, unpublishable-view, or
route-colliding sources stop publication with rule, source, reason, and remediation.

## Compatibility

Version 8 adds docs-owned supplemental Archify declarations beneath each declaring page's adjacent
`diagrams/` directory without changing Documentation routes or Markdown authority. Version 7 adopts
feature `abstract.md`, `design.md`, and `implementation.md` inputs and temporal
`attempt/**` exclusion. Module `design.md` remains an architecture input. Version 4 introduced
permanent feature publication and build-owned delivery of declared diagrams. The self-hosting guide baseline adds
required document instances without changing the CommonMark/YAML representation, source roots,
inclusion globs, content kinds, or path semantics. Further changes to those structural contract
elements require a new major contract version.

## Evidence

Valid and invalid source fixtures, source-immutability checks, architecture discovery, and production
rendering are exercised under `docsite/tests/`.
