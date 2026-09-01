---
id: module.concorde.auto-docs
kind: module
parent: module.concorde
modules: []
features:
  - feature.auto-docs.publish-project-docsite
diagrams: []
---

# Architecture: Auto-Docs

## Responsibility

Publish validated Profile 7 module architectures, feature designs, project documents, and declared
architecture diagrams as a hierarchical, searchable, accessible, provenance-preserving read model.

## Boundary

Auto-Docs owns content discovery/classification, semantic routes, strict link mapping, diagram
orchestration, Build Manifest 10, Docusaurus materialization, publication validation, and atomic site
promotion. It does not own maintained source intent, `.concorde` project-control state, Concorde
validator semantics, Archify rendering, Docusaurus internals, or user-authored source files.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.auto-docs.project` | directory | Private TypeScript/Docusaurus implementation and generated build workspace. | `docsite` |
| `entity.auto-docs.registry` | program | Discovers root README, module architecture, feature design, docs, and declared diagrams into one normalized content model. | `docsite/plugins/concorde-content/registry.ts` |
| `entity.auto-docs.types` | type | Build Manifest 10 collections, page kinds, relations, routes, and provenance records. | `docsite/plugins/concorde-content/types.ts` |
| `entity.auto-docs.routes` | program | Assigns `/architecture/<module-id>`, `/features/<feature-id>`, and documentation routes from semantic identity. | `docsite/plugins/concorde-content/routes.ts` |
| `entity.auto-docs.links` | program | Resolves maintained Markdown links to included semantic routes and rejects missing sources. | `docsite/plugins/concorde-content/links.ts` |
| `entity.auto-docs.diagrams` | program | Discovers only architecture-owned diagram declarations and validates source/output mappings. | `docsite/plugins/concorde-content/diagrams.ts` |
| `entity.auto-docs.manifest` | schema | Deterministic Build Manifest 10 inventory of sources, routes, relations, diagrams, and provenance. | `docsite/plugins/concorde-content/manifest.ts` |
| `entity.auto-docs.validation` | program | Publication gate for identity, hierarchy, source, route, link, diagram, and manifest integrity. | `docsite/plugins/concorde-content/validation.ts` |
| `entity.auto-docs.materializer` | program | Creates ignored Docusaurus content projections without changing maintained sources. | `docsite/scripts/materialize-content.ts` |
| `entity.auto-docs.diagram-renderer` | program | Invokes installed Archify, validates deliveries, and promotes a complete generated diagram set. | `docsite/scripts/render-diagrams.ts` |
| `entity.auto-docs.publisher` | program | Orders preparation/build and atomically promotes a valid production candidate. | `docsite/scripts/build.ts` |
| `entity.auto-docs.tests` | test | TypeScript contract/unit/integration evidence for content, accessibility, atomicity, performance, and source immutability. | `docsite/tests` |
| `entity.auto-docs.archify` | external-system | Maintained-JSON to self-contained-HTML diagram renderer. | `external:archify` |
| `entity.auto-docs.docusaurus` | external-system | Static documentation application framework. | `external:@docusaurus/core@3.10.2` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.auto-docs.registry` | `reads_from` | `module.concorde.workspace-files` | Includes only durable module architectures, feature designs, docs, and declared diagrams; `.concorde/**` is never a content collection. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.routes` | Assigns stable routes from semantic identities. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.links` | Validates and maps source links without rewriting authorities. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.diagrams` | Adds architecture-owned maintained/delivered diagram records. |
| `entity.auto-docs.manifest` | `documents` | `entity.auto-docs.registry` | Serializes deterministic included-source/route/provenance state. |
| `entity.auto-docs.validation` | `validates` | `entity.auto-docs.manifest` | Prevents invalid or incomplete candidates from publication. |
| `entity.auto-docs.diagram-renderer` | `calls` | `entity.auto-docs.archify` | Produces disposable standalone diagram deliveries. |
| `entity.auto-docs.materializer` | `transforms` | `entity.auto-docs.registry` | Creates ignored Docusaurus source projections. |
| `entity.auto-docs.publisher` | `calls` | `entity.auto-docs.materializer` | Prepares content before build. |
| `entity.auto-docs.publisher` | `calls` | `entity.auto-docs.docusaurus` | Builds the static site candidate. |
| `entity.auto-docs.publisher` | `tested_by` | `entity.auto-docs.tests` | End-to-end tests exercise candidate validation and atomic promotion. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.auto-docs.publish` | Maintainer or CI invokes preview/validate/build. | Discover four collections; validate identity/hierarchy/links; render declared architecture views; emit Manifest 10; materialize content; build candidate; atomically promote. | Searchable site or preserved prior output with actionable diagnostics. | `contract.auto-docs.build-interface`, `contract.workspace-files.records`, `contract.auto-docs.archify-renderer`, `contract.auto-docs.build-manifest`, `contract.auto-docs.architecture-site` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.auto-docs.publish-project-docsite` | Convert validated maintained content into a reproducible site with one architecture page per module and one design page per feature. |

## Decisions

- Build Manifest 10 collections are `home`, `architecture`, `docs`, and `features`.
- Page kinds are `module-architecture`, `project-document`, and `feature-design`; feature companion pages do not exist.
- Architecture and feature content may use ignored materialized copies only for Docusaurus isolation; provenance always names the maintained source.
- `.concorde/**` is project control state: it is neither published nor broadly enumerated as a
  Manifest exclusion, while links to it are classified as excluded-control references.
- The last successful site survives any registry, rendering, validation, or build failure.
