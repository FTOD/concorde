---
id: feature.auto-docs.publish-project-docsite
kind: feature
module: module.concorde.auto-docs
related_features:
  - feature.concorde.publish-project-docsite
interfaces:
  provided:
    - contract.auto-docs.architecture-site
    - contract.auto-docs.build-interface
    - contract.auto-docs.build-manifest
  required:
    - contract.workspace.records
    - contract.auto-docs.archify-renderer
evidence_status: verified
---

# Feature Design: Publish the Project Docsite

## Outcome and Scope

Validated project content becomes one deterministic, searchable, accessible, provenance-rich site
with one architecture page per module and one design page per feature.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.auto-docs.registry` | Discovers/classifies four maintained content collections. |
| `entity.auto-docs.routes` | Assigns semantic module/feature/document routes. |
| `entity.auto-docs.diagrams` | Resolves architecture-owned maintained/delivered views. |
| `entity.auto-docs.manifest` | Records Build Manifest 10 source/route/provenance state. |
| `entity.auto-docs.publisher` | Builds and atomically promotes only a valid complete candidate. |

## Interfaces

### `contract.auto-docs.architecture-site` — Published project site

- **Consumer**: Maintainer browser and static-site host.
- **Direction**: Validated build output to read-only HTML/search/assets.
- **Entry points**: Generated site root and semantic routes.
- **Inputs**: Build Manifest 10, materialized content, Docusaurus assets, and delivered architecture diagrams.
- **Outputs**: Accessible searchable pages with canonical source provenance and navigation.
- **Obligations**: No source mutation, no `.concorde` control/framework pages, unique stable routes, accessible text fallback, and last-good preservation.
- **Failures**: Invalid/incomplete candidate is never promoted.
- **Compatibility**: Feature route is `/features/<feature-id>` with no companion pages.
- **Implementing entities**: `entity.auto-docs.publisher`, `entity.auto-docs.docusaurus`.

### `contract.auto-docs.build-interface` — Build/preview/validate commands

- **Consumer**: Maintainer and CI.
- **Direction**: Command/config/source input to status, manifest, candidate, or diagnostics.
- **Entry points**: npm `start`, `inspect`, `validate`, `render-diagrams`, `build`, and `check` scripts.
- **Inputs**: Repository/docsite roots, canonical sources, dependencies, and optional environment configuration.
- **Outputs**: Deterministic diagnostics, Manifest 10, preview, or atomically promoted build.
- **Obligations**: Preparation order is render → registry validation → materialization → build/promotion.
- **Failures**: Any step stops and preserves maintained sources and last successful output.
- **Compatibility**: Node 20+ and locked package dependencies.
- **Implementing entities**: `entity.auto-docs.publisher`, `entity.auto-docs.validation`, `entity.auto-docs.materializer`.

### `contract.auto-docs.build-manifest` — Build Manifest 10

- **Consumer**: Maintainer, CI, freshness checks, and publication tests.
- **Direction**: Normalized registry/diagram state to deterministic JSON record.
- **Entry points**: Registry inspection/validation/build preparation.
- **Inputs**: `home`, `architecture`, `docs`, and `features` collection records plus diagram deliveries.
- **Outputs**: `schemaVersion: 10`; pages of kind `module-architecture`, `project-document`, or `feature-design`; routes/provenance/relations/diagram records.
- **Obligations**: Module pages include `moduleId`, `parentId`, `architectureDiagrams`; feature pages include `featureId`, `moduleId`, `moduleRoute`, `status`, `relatedFeatures`.
- **Failures**: Missing fields, duplicate source/route/ID, unknown relation, or stale diagram invalidates publication.
- **Compatibility**: Removes abstract/design/implementation companion and feature-diagram fields from Manifest 9.
- **Implementing entities**: `entity.auto-docs.manifest`, `entity.auto-docs.registry`, `entity.auto-docs.diagrams`.
- **Example**: A feature page record maps direct source `specs/example/features/001-change.md` to `/features/feature.example.change` and its providing module route.

### `contract.auto-docs.archify-renderer` — Required architecture diagram renderer

- **Provider**: `external:archify`.
- **Consumer**: Auto-Docs diagram delivery orchestrator.
- **Direction**: Maintained module diagram JSON to validated self-contained HTML/receipts.
- **Entry points**: Project-local Archify skill/CLI validation, delivery, and optional visual-check operations.
- **Inputs**: Declared architecture-owned JSON source, output path, hidden generic legend policy, and generator environment.
- **Outputs**: Showcase validation result, standalone HTML, source/output digests, and truthful visual-review status.
- **Obligations**: Preserve source authority/provenance, write only generated output, and reject stale/invalid/escaping deliveries.
- **Failures**: Schema/composition/output/freshness/browser failures stop affected publication; missing browser is reported as unreviewed.
- **Compatibility**: Profile 7 permits zero diagrams, never discovers feature-owned diagram sources,
  and treats `.concorde/**` as non-public project control state rather than a content collection.
- **Implementing entities**: `entity.auto-docs.diagram-renderer`, `entity.auto-docs.archify`.
- **Example**: A module with `diagrams: []` produces no renderer invocation or manifest diagram entries.

## Usage Scenarios

`npm run check` validates types/tests/sources, delivers declared module diagrams, emits a repeatable
manifest, materializes ignored content, builds Docusaurus, and promotes only the complete candidate.

## Requirements

- **FR-001**: Registry MUST include each maintained source exactly once with canonical provenance.
- **FR-002**: Manifest/page routes MUST derive from stable semantic identity, not legacy filenames.
- **FR-003**: Diagram delivery/build failures MUST preserve the last successful site.

## Edge Cases

- Two physical paths claim one stable ID or route.
- A source link resolves outside the included content set.
