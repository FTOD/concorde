# Feature Implementation: Publish Project Docsite

**Realization status**: Accepted realization of the unified project read model, including the README-backed project homepage, independent Architecture and Features projections, and build-owned Archify delivery.

## Realization Overview

Feature 002 is realized by the private TypeScript Docusaurus project under `docsite/`. It publishes one read-only project model from root `README.md` plus the maintained `docs/` and `specs/` trees. The README is the single project introduction for both repository readers and the generated `/` homepage: it leads with Concorde's purpose, key features, all five Concorde-specific commands, and links into Architecture, Documentation, and Features before status and detailed setup material.

A shared registry classifies the dedicated `home` collection, Architecture, Documentation, Feature Abstracts, Feature Designs, and Feature Implementations. Root `README.md` maps uniquely to `/`; repository-relative Markdown links are resolved through the same canonical route map used by every other source. The generated homepage is searchable, carries `README.md` provenance, and appears exactly once in Build Manifest schema v9. No site-only React page duplicates its narrative.

Architecture and Features remain independent semantic projections even though their canonical Markdown shares recursive `specs/` packages. Architecture pages follow module containment. The Features sidebar is generated from the same declared module tree and each module's ordered feature registration, with explicit sub-features beneath their parent feature. Routes remain stable and identity-derived: a top-level feature opens at `/features/<feature-id>`, an immediate child opens below its declared parent route, and design and implementation companions append `/design` and `/implementation`. Adjacent-level refinement remains provenance, metadata, and cross-links rather than containment, so a feature that refines several project outcomes still appears once beneath its owning module.

Diagram publication remains part of preview and production. The build discovers every module-owned and feature-owned Archify source, verifies the project-local Archify 2.16 package, validates each maintained JSON source at showcase quality, and delivers one complete disposable diagram set before Docusaurus consumes it. Generated diagrams, staged Markdown, renderer caches, search indexes, manifests, and site output remain ignored read models.

## Module and Feature Collaboration

The project-level feature `feature.concorde.publish-project-docsite` owns the project-wide publication outcome. Its Auto-Docs refinement, `feature.auto-docs.publish-project-docsite`, realizes that outcome behind `module.concorde.auto-docs`. The project interaction and Auto-Docs level views remain authoritative at `specs/concorde/architecture/diagrams/level-view.json` and `specs/concorde/architecture/modules/auto-docs/architecture/diagrams/level-view.json`; this realization references those views rather than redefining module responsibility, boundary, contracts, or organization.

Scripts, Spec Kit, and project maintainers provide maintained inputs through `contract.auto-docs.project-content`. Maintainers additionally own root `README.md` as the one project introduction. Auto-Docs exposes preview and build behavior through `contract.auto-docs.build-interface`, invokes Archify through `contract.auto-docs.archify-renderer`, emits deterministic inventory through `contract.auto-docs.build-manifest`, and provides the finished site through `contract.auto-docs.architecture-site`. Archify retains rendering semantics; Docusaurus retains generated-site rendering; Auto-Docs owns orchestration, projection, navigation, provenance, and publication gates.

Within Auto-Docs, `docsite/plugins/concorde-content/registry.ts` owns discovery, classification, stable identities, source hashes, module and feature relationships, semantic routes, and staged paths. `links.ts` maps maintained Markdown targets through finalized routes. `manifest.ts` projects schema-v9 page and collection metadata. `materialize-content.ts` writes the disposable Home, Architecture, and Features trees: the Home projection preserves the README body while adding only Docusaurus route metadata, and feature projections retain stable-ID paths and generated category metadata. The shared DocItem wrapper supplies provenance on `/` and all other source-derived pages.

## Scenario Realization

For `publish-architecture`, `render-diagrams.ts` discovers and delivers every declared diagram into a private candidate. It verifies schema-v1 receipts, declared kind and output, maintained-source and artifact digests, all nine showcase checks, composition pass, and zero errors or warnings. A complete verified set atomically replaces the disposable `generated/` tree; a failed set preserves the prior complete delivery and stops publication.

The registry requires and parses root `README.md`, reads `docs/` directly, and recursively classifies `specs/`. It assigns `/` to the single `home` document, resolves module routes before feature pages, assigns stable-ID routes to every feature, and only then derives containment and refinement summaries. Missing or unreadable README content, unresolved supported links, invalid metadata, and route collisions become actionable validation findings.

The materializer stages the README beneath `docsite/.generated/content/home/` with build-only slug metadata and leaves the maintained file byte-unchanged. It also stages Architecture and each feature trio at their semantic paths. The Docusaurus configuration mounts the staged README docs instance at `/`, uses the normal DocItem presentation and provenance path, includes it in local search, and has no competing `src/pages/index.tsx`. Shared preparation clears Docusaurus metadata and bundler caches so route or link changes cannot reuse stale compiled content.

Docusaurus renders a fresh candidate with the README homepage, all three navigation families, local search, and Build Manifest schema v9. The manifest carries the six collection definitions, source provenance, stable feature identity, providing-module routes, containment and refinement summaries, and exactly one `README.md` page at `/`. Candidate routes, links, source freshness, diagram freshness, and schema conformance are verified before atomic promotion to `docsite/build/`; any failure preserves the last successful site.

## Durable Implementation Decisions

- Root `README.md` is the single maintained project introduction. `docs/` owns deeper project guides and `specs/` owns architecture and feature intent; generated pages never become sources.
- README remains ordinary GitHub-flavored Markdown. A disposable staged wrapper adds the `/` slug, while canonical link rewriting preserves repository and site navigation without site-only imports in the maintained file.
- The registry is the single inclusion and route authority shared by validation, link rewriting, staging, search, presentation metadata, manifests, and tests.
- The dedicated `home` collection has source base `.`, include pattern `README.md`, route base `/`, content kind `project-document`, and exactly one page.
- The previous custom React homepage and `ProjectSummary` component are removed so no second hand-authored narrative can drift from README.
- Architecture routes follow module containment. Features routes derive only from globally unique stable feature IDs and explicit parent/sub-feature containment. Adjacent-level refinements and providing modules remain cross-links rather than navigation parents.
- Feature abstracts, behavioral designs, and accepted implementations remain distinct permanent collections; every `attempt/` Markdown file is excluded from publication.
- Generated feature category metadata keeps readable titles while stable IDs provide collision-free disposable paths. All feature routes are assigned before relationship edges are projected.
- Preview and production clear both `.docusaurus` and `node_modules/.cache` after materializing current projections; renderer caches are part of the freshness boundary.
- Content Sources Contract v9 adds the required README homepage. Build Manifest Contract v5 and schema/example v9 add the sixth collection and root source-path shape. Published Project Site Contract v5 makes the existing `/` URL a source-backed README projection. Build Interface remains v1.
- Maintained Archify JSON and its textual counterpart own diagram meaning. Generated HTML and automated receipts never constitute intent or perceptual review. Diagram-set promotion and site-candidate promotion remain separate atomic boundaries.
- The root Architecture view remains the sufficient core component view for Feature 002. `diagrams/project-docsite-publication-flow.json` remains a supplemental sequence for invocation order; adding README changes source content, not participants or ordering.
- The build remains pinned to Node.js 20+, Docusaurus 3.10.2, TypeScript 5.9, React 19, Ajv 8, Vitest 4, Archify 2.16.0-dev.0, and the committed npm lockfile.

## Traceability and Evidence

Required behavior remains in `design.md`. Public source, route, command, manifest, and output guarantees are governed by `contracts/content-sources.md`, `contracts/build-interface.md`, `contracts/build-manifest-contract.md`, `contracts/build-manifest.schema.json`, `contracts/build-manifest.example.json`, and `contracts/published-site.md`, together with the Auto-Docs module contracts under `specs/concorde/architecture/modules/auto-docs/architecture/contracts/`.

The homepage implementation is centered in `README.md`, `docsite/docusaurus.config.ts`, `docsite/plugins/concorde-content/types.ts`, `registry.ts`, `links.ts`, `manifest.ts`, `index.ts`, and `docsite/scripts/materialize-content.ts`. The existing `ContentProvenance` and DocItem wrapper display source identity. `docsite/README.md` and `docs/contributing/docsite.md` document homepage ownership and the six-collection publication model. The deleted `docsite/src/pages/index.tsx` and `ProjectSummary.tsx` are negative evidence that no second homepage remains.

Executable evidence covers required README discovery, root routing, source hashing and provenance, opening-section order, Concorde and related Spec Kit commands, links into all three generated views, missing and broken homepage inputs, duplicate routes, body-faithful staging, source immutability, manifest schema v9, module-grouped Features navigation, search, rendered provenance, retained feature routes, and repeatable production output. The generated sidebar contains every feature exactly once beneath its owning module, keeps explicit sub-features beneath their parent, and leaves stable feature routes free of architecture or module-storage wrappers.

All eight declared diagrams pass the Archify 2.16 delivery gate with 9/9 showcase checks, composition pass, and zero errors or warnings. Feature 002's supplemental publication sequence is freshly delivered and embedded with standalone route and provenance. Browser visual-check was not run, so no new perceptual-review claim is made.

## Known Limitations

- The Auto-Docs refinement still contains earlier hierarchy and two-source-root requirements. Its FR-DOC-003, FR-DOC-004, and module-level project-content contract require their own lifecycle update; this acceptance does not edit adjacent durable sources (R-008).
- Cross-contract version references have executable alignment evidence at schema v9, but the maintainer-owned record of the earlier published-site drift remains open for review (R-009).
- Duplicate feature IDs intentionally emit identity findings plus companion route-collision findings. They are actionable but may be noisy until diagnostics are grouped (R-010).
- Publication clears `.docusaurus` and `node_modules/.cache` on every preview/build preparation. This favors route correctness over warm-cache reuse and must remain aligned with future Docusaurus cache locations (R-011).
- Cross-package validation commands must run from the repository root or use paths appropriate to their working directory; the earlier digest-path mistake remains recorded as an operational caution (R-012).
- Refinement summaries depend on the invariant that every feature route is assigned before any relationship edge is projected (R-013).
- Strict manifest schemas must change in the same milestone as shared page fields. Schema v9 now covers both refinements and the homepage collection, while the earlier omission remains open in the reflection log (R-014).
- Concorde validation accepts `--project-root` as a global option before the `validate` verb; generated quickstarts should retain that ordering (R-020).
- The deep feature-route migration has no redirects. The `/features` base remains stable, but older deep links must be updated.
- Browser containment captures and human light/dark perceptual review remain pending. Ordinary builds intentionally do not claim visual polish.
- Live preview prepares diagrams at startup; changing a maintained diagram while the server is running requires redelivery or preview restart.
- Diagram delivery and site publication have separate atomic boundaries. A later Docusaurus failure can leave a newer ignored diagram set while the last successfully published site remains intact.
- Complete diagram-set promotion currently owns the root `generated/` tree; another producer requires a coordinated namespace or narrower promotion boundary.
- Public hosting behavior for adopters, authentication, analytics, comments, in-site editing, versioned releases, redirects, API extraction, source reference generation, and test-report publication remain outside Feature 002.
- The pinned Docusaurus/local-search dependency graph retains the previously recorded non-critical transitive advisories.
