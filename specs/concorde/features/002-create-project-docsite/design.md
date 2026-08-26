# Feature Design: Publish Project Docsite

**Design status**: Accepted realization of the unified project read model with build-owned Archify delivery.

## Realization Overview

Feature 002 is realized by the private TypeScript Docusaurus project under `docsite/`. It publishes a read-only project model from two maintained source roots without creating a second content authority: `specs/` supplies architecture sources plus durable feature specifications and designs, while `docs/` supplies project-authored guidance. A shared registry classifies those inputs into four source collections—Architecture, Documentation, Feature Specifications, and Feature Designs—and presents them through three navigation families: Architecture, Documentation, and Features.

Diagram publication is part of the same preview and production workflow. Before registry validation or Docusaurus rendering consumes diagram HTML, the build discovers every module-owned and feature-owned Archify declaration, verifies one explicitly configured Archify 2.14.0 package, validates each maintained JSON source at showcase quality, and delivers a complete disposable diagram set. The delivered `generated/` tree, Docusaurus projections, search indexes, manifests, and site output are ignored read models; maintained Markdown and Archify JSON remain the authorities.

The Documentation collection reads `docs/**/*.md` directly. Architecture and Features use ignored projections under `docsite/.generated/content/` because separate Docusaurus content-plugin instances cannot safely share the same physical `specs/` loader root. Production output is rendered into a fresh candidate and promoted to `docsite/build/` only after source, route, rendering, and manifest validation succeeds.

## Module and Feature Collaboration

The root feature `feature.concorde.publish-project-docsite` owns the project-wide publication outcome. Its Documentation-owned refinement, `feature.documentation.publish-project-docsite`, realizes that outcome behind the boundaries declared by `module.concorde.documentation`. The root and Documentation one-level structures remain authoritative in `specs/concorde/architecture.json` and `specs/concorde/modules/documentation/architecture.json`; this design references those views instead of redefining module responsibility or placement.

Architecture Core, Spec Kit, and maintainers provide maintained inputs through `contract.documentation.project-content`. The Documentation module exposes preview/build behavior through `contract.documentation.build-interface`, invokes the external renderer through `contract.documentation.archify-renderer`, emits deterministic inventory through `contract.documentation.build-manifest`, and provides the finished site through `contract.documentation.architecture-site`. Archify retains ownership of schema validation and standalone HTML rendering; Docusaurus retains ownership of the generated site.

Inside Documentation, `docsite/plugins/concorde-content/diagrams.ts` owns declaration discovery and safe normalized mappings without requiring delivered bytes. `registry.ts` owns content discovery, classification, canonical hashes, logical routes, and metadata extraction. `docsite/scripts/render-diagrams.ts` adapts the Archify package/CLI contract and atomically promotes complete delivery sets. `prepare-publication.ts` orders delivery before registry validation and materialization. The preview and production wrappers invoke that shared preparation boundary before Docusaurus.

## Scenario Realization

For the `publish-architecture` scenario, a maintainer sets `ARCHIFY_ROOT` to a package whose real `package.json` identifies `archify` version `2.14.0` and maps its CLI to `bin/archify.mjs`. The adapter rejects missing, incompatible, escaping, or incomplete packages and runs Archify doctor before touching the live delivery set. It never probes an agent home, global executable path, or checkout-local skill as an implicit authority.

Declaration discovery reads eligible module and contract front matter plus canonical feature `spec.md` diagram declarations. It resolves only regular non-symbolic JSON sources, checks feature placement, role and kind rules, `meta.output` agreement, showcase quality, project/generated containment, HTML suffixes, and unique source/output mappings. It returns declarations in stable source-path order without requiring generated HTML, so `inspect` and `validate` remain non-rendering source checks that work in a clean checkout.

Preview and production preparation run Archify `validate` and `deliver` sequentially for each declaration, with explicit source and candidate-output paths. Architecture diagrams receive repository context; dynamic diagrams use the supported type-specific interface. The adapter verifies schema-v1 receipts, the exact diagram kind, maintained-source SHA-256 and byte count, delivered artifact SHA-256 and byte count, all nine showcase checks, composition pass, and zero errors or warnings. Raw receipts are process-local because they contain absolute paths; only normalized project-relative identities and hashes survive in build results. Browser-dependent `visual-check` is deliberately separate from ordinary publication.

All outputs are rendered beneath a private candidate root. Only a fully verified set atomically replaces the ignored root `generated/` tree, which removes stale and undeclared deliveries. Any discovery, package, renderer, receipt, or mid-set failure removes the candidate and preserves the previous complete diagram set. The registry then validates current logical routes and content, the materializer recreates Architecture and Feature projections, and Docusaurus produces pages, local search, and manifest data. A schema-valid site candidate is atomically promoted; later site failure leaves the last successful `docsite/build/` untouched.

Ordinary documentation remains recursively discovered from `docs/`. Architecture and feature pages retain canonical source provenance, textual content outside sandboxed interactive views, and standalone diagram links. Repository-relative links are mapped against canonical sources before rendering, and implementation artifacts remain deliberate exclusions from the permanent Features collection.

## Durable Implementation Decisions

- `docs/` and `specs/` are the only maintained content roots; `generated/`, `docsite/.generated/`, and `docsite/build/` are ignored, reproducible projections.
- Maintained Archify JSON and its textual counterpart own diagram meaning. Generated HTML, visual receipts, captures, and contact sheets are not version-controlled sources.
- Diagram declaration discovery is independent of delivered-output existence. Publication delivery is a later mandatory gate, eliminating the prior clean-checkout cycle.
- `ARCHIFY_ROOT` is the explicit renderer boundary. The adapter requires Archify 2.14.0 package identity, bin containment, and doctor success instead of relying on `npx`, global PATH, or agent-specific directories.
- Each declaration is validated and delivered with explicit paths in deterministic order. Normalized receipts verify source and artifact digests plus 9/9 showcase acceptance without persisting absolute paths.
- Diagram-set promotion and site-candidate promotion are separate atomic boundaries. A partial diagram set is never consumed, and an incomplete site never replaces the last successful publication.
- The registry remains the single inclusion and route-mapping authority shared by validation, link rewriting, projections, presentation metadata, tests, and manifest generation. Logical diagram routes do not imply generated HTML is maintained input.
- Four source collections map to three public navigation families. Feature specifications and durable designs remain distinct permanent collections grouped beneath `/features`; every Markdown file under `implementation/` is excluded.
- Repository-relative Markdown is resolved against canonical sources before route rewriting. Missing, escaping, ambiguous, or temporally excluded targets fail validation.
- The build remains pinned to Node.js 20+, Docusaurus 3.10.2, TypeScript 5.9, React 19, Ajv 8, Vitest 4, and the committed npm lockfile.
- The root architecture view remains the sufficient Feature 002 core component model. `diagrams/project-docsite-publication-flow.json` remains one supplemental sequence view for publication order and is automatically delivered and embedded.
- Visual checking remains an explicit browser-backed evidence step. Automated delivery success is never presented as completed perceptual review.

## Traceability and Evidence

Behavior and outcomes remain in `spec.md`. Detailed source, renderer, command, manifest, and published-output guarantees are governed by `contracts/content-sources.md`, `specs/concorde/modules/documentation/contracts/archify-renderer/contract.md`, `contracts/build-interface.md`, `contracts/build-manifest-contract.md`, `contracts/build-manifest.schema.json`, and `contracts/published-site.md`. Module ownership and boundaries remain under `specs/concorde/modules/documentation/`.

Implementation is centered in `docsite/plugins/concorde-content/diagrams.ts`, `registry.ts`, and `types.ts`; `docsite/scripts/render-diagrams.ts`, `prepare-publication.ts`, `start.ts`, and `build.ts`; Docusaurus configuration and presentation components; and the maintained contributor guides. `.gitignore` excludes complete generated delivery sets and temporary candidates. README links now point to maintained JSON/specification sources instead of committed HTML.

Executable evidence covers declaration ordering and containment, role/kind/output agreement, duplicate outputs, explicit package compatibility, doctor and receipt gates, source/artifact digest agreement, stale-orphan removal, whole-set atomicity, rollback before and after backup movement, source immutability, clean-checkout production, all seven standalone diagram routes, automatic feature/module embedding, manifest repeatability, and failure preservation. The accepted milestone passed 17 Vitest files with 46 tests, 134 Concorde Python tests, source validation for 48 pages with 18 deliberate exclusions, a clean production Docusaurus build, and Concorde validation with zero errors, warnings, or infos. All seven diagrams passed 9/9 Archify showcase checks with zero errors and warnings. Feature 002's sequence source digest was `d483e6d7592dd378ba227bc7bf760cd88fb3e2c9e0f44d746827025806568116`; its delivered artifact digest was `c85d98ffce678d41c4dc3a7f75ba7102aa6c1e7b0753616c3dd7a9afa5d002a6`.

## Known Limitations

- Archify is currently a private external package rather than a locked npm dependency. CI and contributors must provision exactly version 2.14.0 and set `ARCHIFY_ROOT`; publishing or vendoring a stable package is separate work.
- Browser containment captures and human light/dark perceptual review remain pending. Ordinary builds intentionally do not run `visual-check` or claim visual polish.
- Live preview prepares diagrams at startup. A maintained diagram changed while the Docusaurus server is already running requires explicit redelivery or preview restart before its HTML changes.
- Diagram delivery and site publication have separate atomic boundaries. A later Docusaurus failure may leave a newer ignored diagram set on disk, while the last successfully published site remains intact.
- Complete-set promotion currently owns the entire root `generated/` tree. Another future generated-output producer will require a coordinated namespace or narrower promotion boundary.
- Public hosting, deployment, authentication, analytics, comments, in-site editing, versioned documentation releases, redirects, API extraction, source-code reference generation, and test-report publication remain outside Feature 002.
- Source renames can change derived routes because redirects are not yet a published contract. The pinned Docusaurus/local-search dependency graph also retains previously recorded non-critical transitive advisories.
