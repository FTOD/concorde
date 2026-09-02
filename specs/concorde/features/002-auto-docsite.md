---
id: feature.concorde.publish-project-docsite
kind: feature
module: module.concorde
related_features:
  - feature.auto-docs.publish-project-docsite
interfaces:
  provided:
    - interface.concorde.publish-docsite
  required:
    - contract.auto-docs.architecture-site
evidence_status: verified
---

# Feature Design: Create Unified Project Docsite

## Outcome and Scope

A maintainer can publish the root README, project documents, module architectures, feature designs,
and architecture-owned diagrams as one searchable, accessible site with exact source provenance.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `module.concorde.auto-docs` | Implements discovery, validation, rendering, materialization, and atomic publication. |
| `entity.concorde.specification` | Supplies maintained module and feature sources. |
| `entity.concorde.archify` | Produces disposable standalone diagram deliveries. |

## Interfaces

### `interface.concorde.publish-docsite` — Publish the project read model

- **Consumer**: Maintainer, contributor, and CI.
- **Direction**: Maintained content/build request to static site and Manifest 10 result.
- **Entry points**: `npm run start`, `npm run validate`, `npm run build`, and `npm run check` in `docsite`.
- **Inputs**: Root README, `docs/**/*.md`, recursive module `architecture.md`, direct `features/*.md`, and declared module diagrams; native `.concorde/**` control/framework state is excluded.
- **Outputs**: Searchable site, semantic routes, source provenance, delivered diagrams, and Build Manifest 10.
- **Obligations**: Validate identities/links/routes/freshness, never discover `.concorde/**` as pages,
  diagnose legacy specification-local control sources, and atomically preserve the last successful site on failure.
- **Failures**: Invalid sources, missing links, route collision, diagram failure, manifest disagreement, or build failure blocks promotion.
- **Compatibility**: Collections are home/architecture/docs/features; feature pages have no abstract/implementation companions.
- **Implementing entities**: `module.concorde.auto-docs`, `entity.concorde.specification`, `entity.concorde.archify`.

## Usage Scenarios

1. Preview or validate the current source registry and semantic routes without changing sources.
2. Deliver every declared module diagram, materialize ignored Docusaurus inputs, and build a candidate.
3. Promote only a candidate whose links, provenance, Manifest 10, accessibility, and source digests pass.

## Requirements

- **FR-001**: Each module `architecture.md`, direct feature file, project document, and declared architecture diagram MUST appear exactly once in the normalized registry.
- **FR-002**: Routes MUST derive from stable semantic IDs and remain independent of legacy filenames or storage depth.
- **FR-003**: Build Manifest 10 MUST inventory all included sources, module/feature relations, routes, diagram deliveries, provenance, and generator version deterministically.
- **FR-004**: `.concorde` configuration/selection/constitution/attempt/reflection/framework/receipt state and executable/private source files MUST NOT become
  published pages or broad Manifest exclusions; legacy `specs/**/attempts/**` and specification-root
  reflection logs MUST fail the Profile 7 publication gate.
- **FR-005**: Any discovery, link, render, validation, or build failure MUST preserve maintained sources and the last successful site.

## Edge Cases

- A feature moves paths while retaining its stable ID and canonical route.
- Two Markdown links differ syntactically but normalize to the same missing or colliding route.
