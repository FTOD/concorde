---
id: module.concorde.auto-docs
kind: module
parent: module.concorde
modules: []
features:
  - feature.auto-docs.publish-project-docsite
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-auto-docs-system-overview.html
---

# Architecture: Auto-Docs

## Responsibility

Publish validated Profile 7 module architectures, direct feature designs, project documents, and
architecture-owned diagrams as a hierarchical, searchable, accessible, provenance-preserving read model.

## Boundary

Auto-Docs owns content discovery/classification, semantic routes, maintained-link mapping, diagram
orchestration, Build Manifest 10, Docusaurus materialization, publication validation, and atomic site
promotion. It does not own maintained intent, `.concorde` project control/framework bytes, Concorde
validator semantics, Archify rendering, Docusaurus internals, or user-authored sources.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.auto-docs.project` | directory | TypeScript/Docusaurus adapter and generated build workspace. | `docsite` |
| `entity.auto-docs.registry` | program | Discovers README, module architecture, direct features, docs, and declared diagrams into one content model. | `docsite/plugins/concorde-content/registry.ts` |
| `entity.auto-docs.types` | type | Build Manifest 10 page collections, relations, routes, and provenance records. | `docsite/plugins/concorde-content/types.ts` |
| `entity.auto-docs.routes` | program | Assigns semantic architecture, feature, and documentation routes. | `docsite/plugins/concorde-content/routes.ts` |
| `entity.auto-docs.links` | program | Resolves maintained Markdown links to included routes and rejects broken sources. | `docsite/plugins/concorde-content/links.ts` |
| `entity.auto-docs.diagrams` | program | Discovers architecture-owned diagram declarations and validates source/output mappings. | `docsite/plugins/concorde-content/diagrams.ts` |
| `entity.auto-docs.manifest` | schema | Deterministic included-source, route, relation, diagram, and provenance inventory. | `docsite/plugins/concorde-content/manifest.ts` |
| `entity.auto-docs.validation` | program | Publication gate for identity, hierarchy, source, route, link, diagram, and manifest integrity. | `docsite/plugins/concorde-content/validation.ts` |
| `entity.auto-docs.materializer` | program | Creates ignored Docusaurus content projections without changing maintained sources. | `docsite/scripts/materialize-content.ts` |
| `entity.auto-docs.diagram-renderer` | program | Invokes Archify, validates deliveries, and promotes a complete generated diagram set. | `docsite/scripts/render-diagrams.ts` |
| `entity.auto-docs.publisher` | program | Orders preparation/build and atomically promotes a valid candidate. | `docsite/scripts/build.ts` |
| `entity.auto-docs.tests` | test | Contract/unit/integration evidence for content, accessibility, atomicity, performance, and immutability. | `docsite/tests` |
| `entity.auto-docs.archify` | external-system | Maintained-JSON to standalone-HTML diagram renderer. | `external:archify` |
| `entity.auto-docs.docusaurus` | external-system | Static documentation application framework. | `external:@docusaurus/core@3.10.2` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.auto-docs.registry` | `reads_from` | `module.concorde.workspace` | Includes maintained specifications/docs/declared diagrams and excludes all `.concorde/**` control/framework state. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.routes` | Assigns stable routes from semantic identity. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.links` | Validates and maps source links without rewriting authorities. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.diagrams` | Adds architecture-owned source/delivery records. |
| `entity.auto-docs.manifest` | `documents` | `entity.auto-docs.registry` | Serializes deterministic included content and provenance. |
| `entity.auto-docs.validation` | `validates` | `entity.auto-docs.manifest` | Prevents invalid/incomplete candidates from publication. |
| `entity.auto-docs.diagram-renderer` | `calls` | `entity.auto-docs.archify` | Produces disposable standalone diagram deliveries. |
| `entity.auto-docs.materializer` | `transforms` | `entity.auto-docs.registry` | Creates isolated Docusaurus source projections. |
| `entity.auto-docs.publisher` | `calls` | `entity.auto-docs.materializer` | Prepares content before the site build. |
| `entity.auto-docs.publisher` | `calls` | `entity.auto-docs.docusaurus` | Builds the production candidate. |
| `entity.auto-docs.publisher` | `tested_by` | `entity.auto-docs.tests` | End-to-end tests exercise validation and atomic promotion. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.auto-docs.publish` | Maintainer or CI invokes validate/build. | Discover four maintained collections; validate identity/hierarchy/links; render declared architecture views; emit Manifest 10; materialize content; build candidate; atomically promote. | Searchable site or preserved prior output with actionable diagnostics. | `contract.auto-docs.build-interface`, `contract.workspace.records`, `contract.auto-docs.archify-renderer`, `contract.auto-docs.build-manifest`, `contract.auto-docs.architecture-site` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.auto-docs.publish-project-docsite` | Convert validated maintained content into a reproducible site with one architecture page per module and one design page per feature. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Build Manifest 10 collections remain `home`, `architecture`, `docs`, and `features`.
- `.concorde/**` is excluded control/framework state, never a published content collection.
- Materialized Docusaurus files and diagram deliveries are disposable and retain canonical provenance.
- The last successful site survives any registry, render, validation, or build failure.
