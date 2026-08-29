# Feature Implementation: Publish Project Docsite

**Realization status**: Accepted realization of the unified project read model with independent semantic Architecture and Features projections and build-owned Archify delivery.

## Realization Overview

Feature 002 is realized by the private TypeScript Docusaurus project under docsite/. It publishes one read-only project model from the two maintained roots specs/ and docs/. A shared registry classifies Architecture, Documentation, Feature Abstracts, Feature Designs, and Feature Implementations, then exposes them through three navigation families without making the generated site a second authority.

Architecture and Features are independent semantic projections even though their canonical Markdown shares the same recursive specs/ module packages. Architecture keeps the module hierarchy. Features uses stable feature identity and explicit parent/sub-feature containment: a top-level feature opens at /features/<feature-id>, an immediate child opens below its declared parent route, and design and implementation companions append /design and /implementation. Module placement and adjacent-level refinement remain provenance, metadata, and cross-links; architecture/, modules/, and module-local features/ storage wrappers never become Features categories or route parents.

Diagram publication remains part of the same preview and production workflow. The build discovers every module-owned and feature-owned Archify declaration, verifies the project-local Archify 2.16 package at .agents/skills/archify, validates every maintained JSON source at showcase quality, and delivers one complete disposable diagram set before Docusaurus consumes it. The generated/ tree, staged projections, renderer caches, search indexes, manifests, and site output are ignored read models.

## Module and Feature Collaboration

The root feature feature.concorde.publish-project-docsite owns the project-wide publication outcome. Its Documentation refinement, feature.documentation.publish-project-docsite, realizes that outcome behind module.concorde.documentation. The root and Documentation level views remain authoritative at specs/concorde/architecture/diagrams/level-view.json and specs/concorde/architecture/modules/documentation/architecture/diagrams/level-view.json; this realization references those views and does not redefine module responsibility, boundary, contracts, or one-level organization.

Architecture Core, Spec Kit, and maintainers provide maintained inputs through contract.documentation.project-content. Documentation exposes preview and build behavior through contract.documentation.build-interface, invokes Archify through contract.documentation.archify-renderer, emits deterministic inventory through contract.documentation.build-manifest, and provides the finished site through contract.documentation.architecture-site. Archify retains rendering semantics; Docusaurus retains generated-site rendering; Documentation owns orchestration, projection, navigation, provenance, and publication gates.

Within Documentation, docsite/plugins/concorde-content/registry.ts owns discovery, classification, stable identities, canonical hashes, feature/module relationships, semantic feature routes, and staged paths. routes.ts owns the deterministic route helpers; manifest.ts projects the registry into published page metadata; links.ts maps canonical Markdown targets through finalized routes. materialize-content.ts writes independent disposable Architecture and Features trees and creates one human-readable _category_.json per feature. ContentProvenance links each feature to its providing Architecture module, and FeatureRelations presents explicit containment and refinement links without turning refinement into containment.

## Scenario Realization

For publish-architecture, render-diagrams.ts first discovers and delivers every declared diagram into a private candidate. It verifies schema-v1 receipts, declared kind and output, maintained-source and artifact digests, all nine showcase checks, composition pass, and zero errors or warnings. A complete verified set atomically replaces the disposable generated/ tree; a failed set preserves the prior complete delivery and stops publication.

The registry then reads docs/ directly and recursively classifies specs/. It resolves module routes before feature pages, assigns stable-ID routes to every feature in one pass, and only then derives refinement relationship summaries so all embedded targets use finalized routes. Parent/sub-feature registration controls the only Features nesting. Duplicate stable IDs produce both identity findings and paired-page route-collision findings, preserving actionable validation.

The materializer stages each feature trio at its semantic feature path and generates category metadata from the canonical feature title. Repository-relative links are rewritten from canonical source identity, so documentation, architecture, and feature pages all target the new routes without copying source content. Shared preparation removes both .docusaurus and node_modules/.cache after materialization, preventing compiled links from an older registry from surviving a route migration.

Docusaurus renders a fresh site candidate with search and Build Manifest v8. The manifest carries source provenance, stable feature identity, providing-module routes, containment relationships, and optional refinement summaries. The strict schema accepts refinements through the existing feature-relation shape. Candidate routes, links, freshness, and schema conformance are verified before atomic promotion to docsite/build/; any later failure preserves the last successful published site.

## Durable Implementation Decisions

- docs/ and specs/ remain the only maintained content roots. generated/, docsite/.generated/, docsite/.docusaurus/, docsite/node_modules/.cache/, and docsite/build/ are disposable projections or caches.
- The registry is the single inclusion and route authority shared by validation, link rewriting, staging, presentation metadata, manifests, and tests.
- Architecture routes continue to follow projected module containment. Features routes derive only from globally unique stable feature IDs and explicit parent/sub-feature containment.
- Adjacent-level refines relationships are cross-links, never navigation parents. Providing modules link back into Architecture without inserting module categories into Features.
- All feature routes are assigned before relationship edges are projected, ensuring parent, sibling, and refinement summaries use finalized targets.
- Generated _category_.json files provide feature titles and abstract landing links while keeping stable IDs as collision-free disposable directory identities.
- Preview and production clear both Docusaurus metadata and bundler caches after materializing current projections; stale compiled content is inside the publication freshness boundary.
- Content Sources Contract v8 and Published Project Site Contract v4 govern the breaking deep-route migration while the /features route base remains stable.
- Build Manifest schema v8 retains its version because refinements are an additive optional field using the established featureRelation representation; the contract, schema, example, and tests change together.
- Feature abstracts, designs, and implementations remain distinct permanent collections. Every attempt/ Markdown file is excluded from publication.
- Maintained Archify JSON and its textual counterpart own diagram meaning. Generated HTML and automated receipts never constitute intent or perceptual review.
- Diagram-set promotion and site-candidate promotion remain separate atomic boundaries. Partial output never replaces a complete set.
- The root Architecture view remains the sufficient core component view for Feature 002. diagrams/project-docsite-publication-flow.json remains a supplemental sequence for invocation order.
- The build remains pinned to Node.js 20+, Docusaurus 3.10.2, TypeScript 5.9, React 19, Ajv 8, Vitest 4, Archify 2.16.0-dev.0, and the committed npm lockfile.

## Traceability and Evidence

Required behavior remains in design.md. The public source, route, command, manifest, and output guarantees are governed by contracts/content-sources.md, contracts/build-interface.md, contracts/build-manifest-contract.md, contracts/build-manifest.schema.json, contracts/build-manifest.example.json, and contracts/published-site.md, together with the Documentation module contracts under specs/concorde/architecture/modules/documentation/architecture/contracts/.

The semantic hierarchy implementation is centered in docsite/plugins/concorde-content/routes.ts, registry.ts, types.ts, and manifest.ts; docsite/scripts/materialize-content.ts and prepare-publication.ts; and the ContentProvenance and FeatureRelations presentation components. Existing diagram discovery, delivery, candidate validation, and atomic publication remain in diagrams.ts, render-diagrams.ts, start.ts, and build.ts. docsite/README.md, docs/contributing/docsite.md, and docs/project-structure.md explain the resulting projection and route model.

Executable evidence covers stable-ID routing, explicit containment, module-level source independence, generated category metadata, canonical link rewriting, providing-module and refinement links, duplicate identity/collision diagnostics, strict manifest conformance, cache freshness, source immutability, diagram delivery, rendered sidebar structure, route inventory, and repeatability. The final gate passes 19 Vitest files with 73 tests, TypeScript typechecking, validation of 99 published pages with 32 deliberate exclusions and zero errors, two identical production manifests, and deterministic Concorde validation with zero findings. The published manifest contains 63 feature pages and zero feature routes with architecture or module-storage wrappers.

All eight declared diagrams pass the Archify 2.16 delivery gate with 9/9 showcase checks, composition pass, and zero errors or warnings. Feature 002's supplemental sequence is freshly delivered and embedded with standalone route and provenance. Browser visual-check was not run, so no new perceptual-review claim is made.

## Known Limitations

- The Documentation refinement still requires both views to preserve one source-path hierarchy. Its FR-DOC-003 must be revised through that feature's own specification lifecycle; this hardening does not edit the adjacent feature (R-008).
- The selected published-site contract's obsolete manifest-schema reference was corrected and now has cross-contract evidence, but the maintainer-owned reflection remains open until reviewed (R-009).
- Duplicate feature IDs intentionally emit two identity findings plus six abstract/design/implementation route findings. These are actionable but may be noisy if diagnostics are later grouped (R-010).
- Publication now clears .docusaurus and node_modules/.cache on every preview/build preparation. This favors route correctness over warm compiled-cache reuse and should remain aligned with future Docusaurus cache locations (R-011).
- Cross-package validation commands must use paths relative to their actual working directory; the corrected final digest check is recorded as an operational caution (R-012).
- Refinement summaries depend on the two-pass invariant that all feature routes are assigned before relationship edges are projected (R-013).
- Manifest consumers using strict local copies of schema v8 must accept the compatible optional refinements field added to the maintained schema and example (R-014).
- The deep feature-route migration has no redirects. The /features base remains stable, but previously retained deep links must be updated.
- The project-local Archify skill is an installed upstream snapshot. Updating it requires an explicit official reinstall plus coordinated lock, adapter, contract, diagram, and test review.
- Browser containment captures and human light/dark perceptual review remain pending. Ordinary builds intentionally do not run visual-check or claim visual polish.
- Live preview prepares diagrams at startup; a maintained diagram changed while the server is already running requires explicit redelivery or preview restart.
- Diagram delivery and site publication have separate atomic boundaries. A later Docusaurus failure can leave a newer ignored diagram set while the last successfully published site remains intact.
- Complete diagram-set promotion currently owns the root generated/ tree; another producer will require a coordinated namespace or narrower promotion boundary.
- Public hosting behavior for adopters, authentication, analytics, comments, in-site editing, versioned releases, redirects, API extraction, source reference generation, and test-report publication remain outside Feature 002.
- The pinned Docusaurus/local-search dependency graph retains the previously recorded non-critical transitive advisories.
