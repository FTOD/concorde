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

Validated project specifications become one deterministic, searchable, accessible, provenance-rich
site with one architecture page per module and one design page per direct feature. Architecture and
Features are the only content collections; README is not a page and root `docs/` is rejected as a
parallel prose authority.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.auto-docs.registry` | Discovers/classifies the Architecture and Features collections and rejects parallel docs. |
| `entity.auto-docs.routes` | Assigns semantic module/feature routes and resolves `/` to root architecture. |
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
- **Compatibility**: Navigation exposes exactly Architecture and Features; `/` resolves to the root
  architecture route, module routes are `/architecture/<module-id>`, and feature routes are
  `/features/<feature-id>` with no companion or `/docs` pages.
- **Implementing entities**: `entity.auto-docs.publisher`, `entity.auto-docs.docusaurus`.

### `contract.auto-docs.build-interface` — Build, preview, and validation scripts

- **Consumer**: Maintainer and CI.
- **Direction**: Script/config/source input to status, manifest, candidate, or diagnostics.
- **Entry points**: npm `start`, `inspect`, `validate`, `render-diagrams`, `build`, and `check` scripts.
- **Inputs**: Repository/docsite roots, site identity from `docsite/site.json`, recursive
  `specs/**/architecture.md`, direct `specs/**/features/*.md`, declared module diagrams, locked
  dependencies, and optional renderer environment configuration.
- **Outputs**: Deterministic diagnostics, Manifest 10, preview, or atomically promoted build.
- **Obligations**: Preparation order is render → registry validation → materialization →
  build/manifest validation → atomic promotion; never discover README as content and fail with
  migration remediation when root `docs/` exists.
- **Failures**: Any step stops and preserves maintained sources and last successful output.
- **Compatibility**: Node 20+, locked package dependencies, and site identity schema 1.
- **Implementing entities**: `entity.auto-docs.publisher`, `entity.auto-docs.validation`, `entity.auto-docs.materializer`.

### `contract.auto-docs.build-manifest` — Build Manifest 10

- **Consumer**: Maintainer, CI, freshness checks, and publication tests.
- **Direction**: Normalized registry/diagram state to deterministic JSON record.
- **Entry points**: Registry inspection/validation/build preparation.
- **Inputs**: `architecture` and `features` collection records plus diagram deliveries.
- **Outputs**: `schemaVersion: 10`; pages of kind `module-architecture` or `feature-design`;
  routes/provenance/relations/diagram records.
- **Obligations**: Module pages include `moduleId`, `parentId`, `architectureDiagrams`; feature pages include `featureId`, `moduleId`, `moduleRoute`, `status`, `relatedFeatures`.
- **Failures**: Missing fields, duplicate source/route/ID, unknown relation, or stale diagram invalidates publication.
- **Compatibility**: Removes abstract/design/implementation companion and feature-diagram fields from Manifest 9.
- **Implementing entities**: `entity.auto-docs.manifest`, `entity.auto-docs.registry`, `entity.auto-docs.diagrams`.
- **Example**: A feature page record maps direct source `specs/example/features/001-change.md` to `/features/feature.example.change` and its providing module route.

### `contract.auto-docs.archify-renderer` — Required architecture diagram renderer

- **Provider**: `external:archify`.
- **Consumer**: Auto-Docs diagram delivery orchestrator.
- **Direction**: Maintained module diagram JSON to validated self-contained HTML/receipts.
- **Entry points**: Project-local Archify Skill/CLI validation, delivery, and optional visual-check actions.
- **Inputs**: Declared architecture-owned JSON source, output path, hidden generic legend policy, and generator environment.
- **Outputs**: Showcase validation result, standalone HTML, source/output digests, and truthful visual-review status.
- **Obligations**: Preserve source authority/provenance, write only generated output, and reject stale/invalid/escaping deliveries.
- **Failures**: Schema/composition/output/freshness/browser failures stop affected publication; missing browser is reported as unreviewed.
- **Compatibility**: Profile 7 requires one module-owned Archify architecture system overview, never
  discovers feature-owned diagram sources, and treats `.concorde/**` as non-public project control
  state rather than a content collection.
- **Implementing entities**: `entity.auto-docs.diagram-renderer`, `entity.auto-docs.archify`.
- **Example**: A module system overview is showcase-validated and rendered before its architecture page
  is admitted to the publication candidate.

## Usage Scenarios

### Configure identity

`docsite/site.json` is the only project-specific adapter file. Schema 1 requires a non-empty `title`,
absolute HTTP(S) `url` without a path, slash-bounded `baseUrl`, and non-empty `organizationName` and
`projectName`; optional `repository` is an absolute URL and optional `tagline` overrides the default.
A missing or invalid field fails with a diagnostic naming `docsite/site.json` and the violated rule.

### Author and publish

Write maintained prose only in the owning module `architecture.md` or direct feature file. Keep a
module diagram JSON under that module's `diagrams/`, declare and textually explain it in
`architecture.md`, use a hidden legend and unique generated HTML target, and never place a diagram
source in a feature. Correct maintained sources rather than editing `generated/`,
`docsite/.generated/`, or `docsite/build/`.

From `docsite/`, use `npm run inspect` for normalized mappings, `npm run validate` for source gates,
`npm run render-diagrams` for declared views, `npm run start` for preview, `npm run build` for an
atomic candidate, and `npm run check` for typechecking, tests, source/diagram validation, and the
production build. Repeated builds over identical inputs produce the same manifest and route
inventory without an LLM call. Browser visual review is an explicit Archify check; structural
delivery remains truthful when no browser is available.

The build discovers the two collections, validates identities/hierarchy/links/routes, delivers
declared module diagrams, materializes ignored Architecture/Feature renderer inputs, builds a
Docusaurus candidate, validates Build Manifest 10 and provenance/freshness, then promotes only that
complete candidate. Any failure leaves maintained sources and the previous successful build intact.

## Requirements

- **FR-001**: Registry MUST include each maintained source exactly once with canonical provenance.
- **FR-002**: Manifest/page routes MUST derive from stable semantic identity, not legacy filenames.
- **FR-003**: Diagram delivery/build failures MUST preserve the last successful site.
- **FR-004**: The adapter MUST read project identity only from `docsite/site.json` and MUST publish
  exactly the Architecture and Features collections, with Features conditionally configured only
  when at least one direct feature is registered.
- **FR-005**: Registry and deterministic project validation MUST reject any root `docs/` tree with
  remediation to merge unique intent into an owning module architecture or direct feature before
  removal; README MUST remain outside content and provenance records.
- **FR-006**: Navigation, sidebars, materialized inputs, search records, manifest pages, and routes
  MUST contain no Home/Documentation collection, `project-document` kind, or `/docs` family.
- **FR-007**: Root `/` MUST resolve to the configured root module architecture without creating a
  second source-backed page record.

## Edge Cases

- Two physical paths claim one stable ID or route.
- A source link resolves outside the included content set.
