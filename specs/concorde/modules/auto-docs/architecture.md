---
id: module.concorde.auto-docs
kind: module
parent: module.concorde
modules: []
features:
  - feature.auto-docs.publish-project-docsite
  - feature.auto-docs.create-project-docsite
  - feature.auto-docs.publish-feature-graph
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-auto-docs-system-overview.html
---

# Architecture: Auto-Docs

## Responsibility

Publish validated Profile 7 module architectures—including every capability module—direct feature
designs, and architecture-owned diagrams as a hierarchical, searchable, accessible,
provenance-preserving read model with exactly Architecture and Features navigation.

## Boundary

Auto-Docs owns content discovery/classification, semantic routes, maintained-link mapping, diagram
orchestration, Build Manifest 13, Docusaurus materialization, publication validation, and atomic site
promotion. It does not own maintained intent, `.concorde` project control/framework bytes, Concorde
validator semantics, Archify rendering, Docusaurus internals, or user-authored sources.

## Operation Contract Boundary

Auto-Docs publishes the root concept inventory, constrained relationships, runtime-realization
review, and architecture-owned diagrams. It must preserve the distinction between Operation
definition, invocation, data type, implemented contract, and the evidence limits around live agent
execution. Publication renders those maintained claims; it does not execute or independently prove
the JSON Operation ABI.

The root entity/component view explains structure; its dataflow explains typed producer/consumer
transfers, while the module collaboration view explains capability ownership. All are projections
of textual architecture and feature contracts, with separate declared outputs and normal freshness
checks. Diagram nodes do not create new entities or take ownership from a feature's data definition.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.auto-docs.project` | directory | TypeScript/Docusaurus adapter and generated build workspace. | `docsite` |
| `entity.auto-docs.docsite-scaffold` | program | Proposes and atomically applies Docsite Scaffold Proposal 1 with a project-owned site identity and no synthetic project prose. | `src/concorde/autodocs/docsite_scaffold.py` |
| `entity.auto-docs.docsite-template` | program | Enumerates the packaged docsite template inventory and digest shared by the installer and the scaffold Tool. | `src/concorde/autodocs/docsite_template.py` |
| `entity.auto-docs.registry` | program | Discovers module architecture, direct features, and declared diagrams into two specification collections while rejecting a root docs tree. | `docsite/plugins/concorde-content/registry.ts` |
| `entity.auto-docs.types` | type | Build Manifest 13 page collections, relations, routes, and provenance records. | `docsite/plugins/concorde-content/types.ts` |
| `entity.auto-docs.routes` | program | Assigns semantic architecture/feature routes and supports the root architecture entry. | `docsite/plugins/concorde-content/routes.ts` |
| `entity.auto-docs.links` | program | Resolves maintained Markdown links to included routes and rejects broken sources. | `docsite/plugins/concorde-content/links.ts` |
| `entity.auto-docs.diagrams` | program | Discovers architecture-owned diagram declarations and validates source/output mappings. | `docsite/plugins/concorde-content/diagrams.ts` |
| `entity.auto-docs.manifest` | schema | Deterministic included-source, route, relation, diagram, and provenance inventory. | `docsite/plugins/concorde-content/manifest.ts` |
| `entity.auto-docs.validation` | program | Publication gate for identity, hierarchy, source, route, link, diagram, and manifest integrity. | `docsite/plugins/concorde-content/validation.ts` |
| `entity.auto-docs.materializer` | program | Creates ignored Docusaurus content projections without changing maintained sources. | `docsite/scripts/materialize-content.ts` |
| `entity.auto-docs.diagram-renderer` | program | Invokes Archify, validates deliveries, and promotes a complete generated diagram set. | `docsite/scripts/render-diagrams.ts` |
| `entity.auto-docs.publisher` | program | Orders preparation/build and atomically promotes a valid candidate. | `docsite/scripts/build.ts` |
| `entity.auto-docs.site-identity` | configuration | Project-owned site identity schema 1 (title, URL, base path, organization/project names, optional repository) that parameterizes the otherwise byte-identical adapter. | `docsite/site.json` |
| `entity.auto-docs.graph` | program | Derives Feature Graph 2 from the validated registry: feature nodes, module groups, typed related-feature edges with inverse normalization and reciprocal merging, interface-derived `requires` edges, and per-family acyclicity. | `docsite/plugins/concorde-content/graph.ts` |
| `entity.auto-docs.feature-graph` | schema | Feature Graph 2: versioned, sorted JSON of feature nodes, module groups, typed edges, counts, and generator/source provenance published as `feature-graph.json`. | `docsite/tests/fixtures/interfaces/feature-graph.schema.json` |
| `entity.auto-docs.graph-page` | program | The `/graph` page: module-grouped interactive view with edge-kind and module filters, search, neighbor highlighting, legend, detail panel, and the textual edge table. | `docsite/src/pages/graph.tsx` |
| `entity.auto-docs.graph-view` | program | Client-only Cytoscape component drawing nodes, compound module groups, and typed edges; shared by the global page and neighborhood views. | `docsite/src/components/FeatureGraph.tsx` |
| `entity.auto-docs.neighborhood-view` | program | Depth-one neighborhood of one feature rendered on its page beside the relation-labeled related-feature list. | `docsite/src/components/FeatureNeighborhood.tsx` |
| `entity.auto-docs.cytoscape` | external-system | Browser graph rendering and fcose layout library loaded only on the client. | `external:cytoscape/cytoscape.js@3` |
| `entity.auto-docs.pages-workflow-template` | resource | Generic GitHub Pages deployment workflow the scaffold copies on request. | `docsite/scaffold/deploy-docsite.yml` |
| `entity.auto-docs.tests` | test | Contract/unit/integration evidence for content, accessibility, atomicity, performance, and immutability. | `docsite/tests` |
| `entity.auto-docs.archify` | external-system | Maintained-JSON to standalone-HTML diagram renderer. | `external:archify` |
| `entity.auto-docs.docusaurus` | external-system | Static documentation application framework. | `external:@docusaurus/core@3.10.2` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.auto-docs.registry` | `reads_from` | `entity.concorde.specification` | Includes maintained architecture/features/declared diagrams, rejects root docs, and excludes README plus all `.concorde/**` control/framework state. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.routes` | Assigns stable routes from semantic identity. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.links` | Validates and maps source links without rewriting authorities. |
| `entity.auto-docs.registry` | `calls` | `entity.auto-docs.diagrams` | Adds architecture-owned source/delivery records. |
| `entity.auto-docs.manifest` | `documents` | `entity.auto-docs.registry` | Serializes deterministic included content and provenance. |
| `entity.auto-docs.validation` | `validates` | `entity.auto-docs.manifest` | Prevents invalid/incomplete candidates from publication. |
| `entity.auto-docs.diagram-renderer` | `calls` | `entity.auto-docs.archify` | Produces disposable standalone diagram deliveries. |
| `entity.auto-docs.materializer` | `transforms` | `entity.auto-docs.registry` | Creates isolated Docusaurus source projections. |
| `entity.auto-docs.publisher` | `calls` | `entity.auto-docs.materializer` | Prepares content before the site build. |
| `entity.auto-docs.publisher` | `calls` | `entity.auto-docs.docusaurus` | Builds the production candidate. |
| `entity.auto-docs.publisher` | `reads_from` | `entity.auto-docs.site-identity` | Takes title, URLs, organization/project names, and repository link only from the project-owned identity file. |
| `entity.auto-docs.publisher` | `tested_by` | `entity.auto-docs.tests` | End-to-end tests exercise validation and atomic promotion. |
| `entity.auto-docs.graph` | `reads_from` | `entity.auto-docs.registry` | Derives the graph only from validated feature front matter and interface ownership. |
| `entity.auto-docs.graph` | `generates` | `entity.auto-docs.feature-graph` | Produces the deterministic Feature Graph 2 document. |
| `entity.auto-docs.validation` | `validates` | `entity.auto-docs.feature-graph` | Rejects unknown relations, unresolved endpoints, duplicate providers, and directional cycles before promotion. |
| `entity.auto-docs.manifest` | `documents` | `entity.auto-docs.feature-graph` | Build Manifest 13 registers the published graph path beside pages and diagrams. |
| `entity.auto-docs.publisher` | `generates` | `entity.auto-docs.feature-graph` | Writes `feature-graph.json` into the candidate and promotes it with the site. |
| `entity.auto-docs.graph-page` | `reads_from` | `entity.auto-docs.feature-graph` | Renders the global view and the textual edge table from plugin global data. |
| `entity.auto-docs.graph-page` | `calls` | `entity.auto-docs.graph-view` | Mounts the client-only interactive canvas. |
| `entity.auto-docs.neighborhood-view` | `calls` | `entity.auto-docs.graph-view` | Draws one feature's depth-one neighborhood with the same renderer. |
| `entity.auto-docs.graph-view` | `calls` | `entity.auto-docs.cytoscape` | Lays out and draws compound module groups and typed edges in the browser. |
| `entity.auto-docs.graph` | `tested_by` | `entity.auto-docs.tests` | Derivation, normalization, cycle, provider, determinism, and schema tests establish graph evidence. |
| `entity.auto-docs.docsite-scaffold` | `reads_from` | `entity.auto-docs.docsite-template` | Reuses the single packaged adapter file inventory and digest rule. |
| `entity.auto-docs.docsite-scaffold` | `generates` | `entity.auto-docs.project` | Applies the accepted Docsite Scaffold Proposal 1 as the project's `docsite/` adapter and site identity. |
| `module.concorde.distribution` | `reads_from` | `entity.auto-docs.docsite-template` | Packages the same template root into the installed framework projection. |
| `module.concorde.capabilities` | `calls` | `entity.auto-docs.docsite-scaffold` | Dispatches the CLI `docsite` Tool for propose/apply scaffold actions. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.auto-docs.publish` | Maintainer or CI invokes validate/build. | Reject root docs; discover Architecture and Features, including every declared module; validate identity/hierarchy/links; render declared architecture views; emit Build Manifest 13; materialize content; build candidate plus root-architecture entry; atomically promote. | Searchable two-collection site or preserved prior output with actionable diagnostics. | `contract.auto-docs.build-interface`, `contract.understanding.records`, `contract.auto-docs.archify-renderer`, `contract.auto-docs.build-manifest`, `contract.auto-docs.architecture-site` |
| `interaction.auto-docs.scaffold` | Maintainer requests a project docsite after initialization. | Verify the configured root architecture; read the packaged docsite template and derive site identity; emit a digest-bound Docsite Scaffold Proposal 1; after explicit acceptance, atomically promote exactly its files. | A project-owned docsite adapter and identity file ready for publication, or exact conflict diagnostics. | `interface.concorde.scaffold-docsite`, `contract.capabilities.tools` |

| `interaction.auto-docs.graph` | A reader opens `/graph` or a feature page after publication. | `entity.auto-docs.graph` derived Feature Graph 2 from `entity.auto-docs.registry` during the build; `entity.auto-docs.validation` rejected unknown relations, unresolved endpoints, duplicate providers, and directional cycles; `entity.auto-docs.publisher` wrote `feature-graph.json` and `entity.auto-docs.manifest` registered it; `entity.auto-docs.graph-page` or `entity.auto-docs.neighborhood-view` renders the typed edges through `entity.auto-docs.graph-view` and the textual table. | The reader sees how features compose, refine, depend on, and require one another, grouped by module, with links to each feature page. | `interface.auto-docs.feature-graph` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.auto-docs.publish-project-docsite` | Convert validated maintained content into a reproducible site with one architecture page per module and one design page per feature. |
| `feature.auto-docs.publish-feature-graph` | Publish one deterministic typed feature relationship graph as a JSON document, an interactive module-grouped page, and per-feature neighborhood views. |
| `feature.auto-docs.create-project-docsite` | Scaffold the project docsite from the packaged template through one reviewed proposal/apply cycle, then expose the entry points that publish it. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Build Manifest 13 collections are exactly `architecture` and `features`; page kinds are exactly
  module architecture and feature design.
- `.concorde/**` is excluded control/framework state, never a published content collection.
- README remains repository orientation rather than content; a root `docs/` tree fails validation as
  a parallel authority; `/` is a source-free projection to the root architecture route.
- Materialized Docusaurus files and diagram deliveries are disposable and retain canonical provenance.
- The last successful site survives any registry, render, validation, or build failure.
- The adapter is the docsite template Concorde packages for every project: project identity lives
  only in `docsite/site.json`, Features configures only when a direct feature is registered, and
  Concorde-repository evidence stays under `docsite/tests/repository/` outside the template.
- Feature Graph 2 is a derived projection, never a maintained diagram: it is regenerated from feature
  front matter on every build, validated before promotion, and rendered client-side with a textual
  counterpart; Archify remains the renderer for curated architecture-owned views only.
