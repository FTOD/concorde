---
id: contract.documentation.project-content
kind: contract
module: module.concorde.documentation
role: required
flow: input
representation:
  kind: standard
  format: CommonMark with YAML front matter
  version: CommonMark 0.31.2 / YAML 1.2.2
  definition: https://spec.commonmark.org/0.31.2/
counterparties:
  - module.concorde.architecture-core
  - external.project-maintainer
  - external.spec-kit
providers:
  - module.concorde.architecture-core
  - external.project-maintainer
  - external.spec-kit
features:
  - feature.documentation.publish-project-docsite
version: 2
evidence:
  tests:
    - docsite/tests/contract/content-sources.test.ts
evidence_status: verified
---

# Project content contract

## Purpose

Provide UTF-8 architecture sources from `architecture/**/*.md`, project documentation from
`docs/**/*.md`, and canonical feature specifications from `specs/**/spec.md` without relocating or
modifying any authority. Markdown follows
[CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/); optional front matter follows
[YAML 1.2.2](https://yaml.org/spec/1.2.2/). Complete field, inclusion, link, failure, and compatibility
semantics are defined once in `specs/002-create-project-docsite/contracts/content-sources.md`.

## Information

The boundary carries UTF-8 Markdown and YAML metadata from three maintained roots, project-relative
links, stable feature and architecture identity, and declared Archify JSON view references.

## Obligations

- Every eligible valid source is included exactly once and retains its authored meaning.
- Feature IDs are unique; feature kind, module, title, and lifecycle status are present.
- Architecture IDs and kinds are explicit; declared JSON views resolve to delivered Archify HTML.
- Project-relative links resolve within or across the three accepted source roots.
- Plans, tasks, and checklists are observable exclusions, not feature specifications.
- Reads do not change source bytes, metadata, or timestamps.

## Failure Semantics

Unreadable, escaping, ambiguous, malformed, missing-identity, broken-link, unpublishable-view, or
route-colliding sources stop publication with rule, source, reason, and remediation.

## Compatibility

Version 2 adds the Architecture route space and view metadata; further changes to roots, inclusion
globs, required fields, or path semantics require a new major contract version.

## Evidence

Valid and invalid source fixtures, source-immutability checks, architecture discovery, and production
rendering are exercised under `docsite/tests/`.
