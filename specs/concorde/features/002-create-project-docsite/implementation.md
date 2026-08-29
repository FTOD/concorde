# Feature Implementation: Publish Project Docsite

**Realization status**: Accepted realization of the unified project read model with build-owned Archify delivery.

## Realization Overview

Feature 002 is realized by the private TypeScript Docusaurus project under `docsite/`. It publishes
a read-only project model from `specs/` and `docs/`. A shared registry classifies five collections:
Architecture, Documentation, Feature Abstracts, Feature Designs, and Feature Implementations, and
presents them through three navigation families.

Diagram publication is part of the same preview and production workflow. Before registry validation or Docusaurus rendering consumes diagram HTML, the build discovers every module-owned and feature-owned Archify declaration, verifies the officially installed project-local Archify 2.16 skill at `.agents/skills/archify` (`package.json` version `2.16.0-dev.0`), validates each maintained JSON source at showcase quality, and delivers a complete disposable diagram set. The delivered `generated/` tree, Docusaurus projections, search indexes, manifests, and site output are ignored read models; maintained Markdown and Archify JSON remain the authorities.

The Documentation collection reads `docs/**/*.md` directly. Architecture and Features use ignored projections under `docsite/.generated/content/` because separate Docusaurus content-plugin instances cannot safely share the same physical `specs/` loader root. Production output is rendered into a fresh candidate and promoted to `docsite/build/` only after source, route, rendering, and manifest validation succeeds.

## Module and Feature Collaboration

The root feature `feature.concorde.publish-project-docsite` owns the project-wide publication outcome. Its Documentation-owned refinement, `feature.documentation.publish-project-docsite`, realizes that outcome behind the boundaries declared by `module.concorde.documentation`. The root and Documentation one-level structures remain authoritative in `specs/concorde/architecture/diagrams/level-view.json` and `specs/concorde/architecture/modules/documentation/architecture/diagrams/level-view.json`; this design references those views instead of redefining module responsibility or placement.

Architecture Core, Spec Kit, and maintainers provide maintained inputs through `contract.documentation.project-content`. The Documentation module exposes preview/build behavior through `contract.documentation.build-interface`, invokes the external renderer through `contract.documentation.archify-renderer`, emits deterministic inventory through `contract.documentation.build-manifest`, and provides the finished site through `contract.documentation.architecture-site`. Archify retains ownership of schema validation and standalone HTML rendering; Docusaurus retains ownership of the generated site.

Inside Documentation, `docsite/plugins/concorde-content/diagrams.ts` owns declaration discovery and safe normalized mappings without requiring delivered bytes. `registry.ts` owns content discovery, classification, canonical hashes, logical routes, and metadata extraction. `docsite/scripts/render-diagrams.ts` adapts the Archify package/CLI contract and atomically promotes complete delivery sets. `prepare-publication.ts` orders delivery before registry validation and materialization. The preview and production wrappers invoke that shared preparation boundary before Docusaurus.

## Scenario Realization

For the `publish-architecture` scenario, the repository contains the official project-local Archify skill at `.agents/skills/archify`, recorded by `skills-lock.json`. The adapter resolves only that project-relative location, requires its real `package.json` to identify `archify` version `2.16.0-dev.0` and map its CLI to `bin/archify.mjs`, and runs Archify doctor before touching the live delivery set. It rejects missing, incompatible, escaping, or incomplete packages and never probes an agent home, global executable path, environment variable, or extra checkout as an authority.

Declaration discovery reads eligible module and contract front matter plus canonical feature `design.md` diagram declarations. It resolves only regular non-symbolic JSON sources, checks feature placement, role and kind rules, `meta.output` agreement, showcase quality, project/generated containment, HTML suffixes, and unique source/output mappings. It returns declarations in stable source-path order without requiring generated HTML, so `inspect` and `validate` remain non-rendering source checks that work in a clean checkout.

Preview and production preparation run Archify `validate` and `deliver` sequentially for each declaration, with explicit source and candidate-output paths. Architecture diagrams receive repository context; dynamic diagrams use the supported type-specific interface. The adapter verifies schema-v1 receipts, the exact diagram kind, maintained-source SHA-256 and byte count, delivered artifact SHA-256 and byte count, all nine showcase checks, composition pass, and zero errors or warnings. Raw receipts are process-local because they contain absolute paths; only normalized project-relative identities and hashes survive in build results. Browser-dependent `visual-check` is deliberately separate from ordinary publication.

All outputs are rendered beneath a private candidate root. Only a fully verified set atomically replaces the ignored root `generated/` tree, which removes stale and undeclared deliveries. Any discovery, package, renderer, receipt, or mid-set failure removes the candidate and preserves the previous complete diagram set. The registry then validates current logical routes and content, the materializer recreates Architecture and Feature projections, and Docusaurus produces pages, local search, and manifest data. A schema-valid site candidate is atomically promoted; later site failure leaves the last successful `docsite/build/` untouched.

Ordinary documentation remains recursively discovered from `docs/`. Architecture and feature pages retain canonical source provenance, textual content outside sandboxed interactive views, and standalone diagram links. Repository-relative links are mapped against canonical sources before rendering, and implementation artifacts remain deliberate exclusions from the permanent Features collection.

## Durable Implementation Decisions

- `docs/` and `specs/` are the only maintained content roots; `generated/`, `docsite/.generated/`, and `docsite/build/` are ignored, reproducible projections.
- Maintained Archify JSON and its textual counterpart own diagram meaning. Generated HTML, visual receipts, captures, and contact sheets are not version-controlled sources.
- Diagram declaration discovery is independent of delivered-output existence. Publication delivery is a later mandatory gate, eliminating the prior clean-checkout cycle.
- `.agents/skills/archify` is the single renderer boundary. The adapter requires the installed Archify 2.16 development package identity, bin containment, and doctor success instead of relying on an environment variable, `npx`, global PATH, agent-home installation, or CI-only checkout.
- Each declaration is validated and delivered with explicit paths in deterministic order. Normalized receipts verify source and artifact digests plus 9/9 showcase acceptance without persisting absolute paths.
- Diagram-set promotion and site-candidate promotion are separate atomic boundaries. A partial diagram set is never consumed, and an incomplete site never replaces the last successful publication.
- The registry remains the single inclusion and route-mapping authority shared by validation, link rewriting, projections, presentation metadata, tests, and manifest generation. Logical diagram routes do not imply generated HTML is maintained input.
- Five source collections map to three public navigation families. Feature abstracts, designs, and
  implementations are distinct permanent collections grouped beneath `/features`; every Markdown
  file under `attempt/` is excluded.
- Repository-relative Markdown is resolved against canonical sources before route rewriting. Missing, escaping, ambiguous, or temporally excluded targets fail validation.
- The build remains pinned to Node.js 20+, Docusaurus 3.10.2, TypeScript 5.9, React 19, Ajv 8, Vitest 4, and the committed npm lockfile.
- The root architecture view remains the sufficient Feature 002 core component model. `diagrams/project-docsite-publication-flow.json` remains one supplemental sequence view for publication order and is automatically delivered and embedded.
- Visual checking remains an explicit browser-backed evidence step. Automated delivery success is never presented as completed perceptual review.

## Traceability and Evidence

Behavior and outcomes remain in `design.md`. Detailed source, renderer, command, manifest, and published-output guarantees are governed by `contracts/content-sources.md`, `specs/concorde/architecture/modules/documentation/architecture/contracts/archify-renderer/contract.md`, `contracts/build-interface.md`, `contracts/build-manifest-contract.md`, `contracts/build-manifest.schema.json`, and `contracts/published-site.md`. Module ownership and boundaries remain under `specs/concorde/architecture/modules/documentation/`.

Implementation is centered in `docsite/plugins/concorde-content/diagrams.ts`, `registry.ts`, and `types.ts`; `docsite/scripts/render-diagrams.ts`, `prepare-publication.ts`, `start.ts`, and `build.ts`; Docusaurus configuration and presentation components; and the maintained contributor guides. `.gitignore` excludes complete generated delivery sets and temporary candidates. README links now point to maintained JSON/specification sources instead of committed HTML.

Executable evidence covers declaration ordering and containment, role/kind/output agreement,
project-local skill compatibility, receipt/digest gates, stale-orphan removal, atomicity, rollback,
source immutability, clean production builds, all eight standalone diagram routes, automatic
feature/module embedding, Manifest v8 repeatability, and failure preservation. The documentation
gate passes 18 Vitest files with 68 tests and validates 99 pages with 25 deliberate exclusions and
zero errors. The 231-test Python suite and deterministic Concorde validation also pass; all eight
diagrams pass the build-owned Archify showcase gate.

## Known Limitations

- The project-local Archify skill is an installed upstream snapshot rather than a registry dependency. Updating it requires an explicit official skill reinstall, review of `skills-lock.json` and package identity, and coordinated adapter, contract, diagram, and test verification.
- Browser containment captures and human light/dark perceptual review remain pending. Ordinary builds intentionally do not run `visual-check` or claim visual polish.
- Live preview prepares diagrams at startup. A maintained diagram changed while the Docusaurus server is already running requires explicit redelivery or preview restart before its HTML changes.
- Diagram delivery and site publication have separate atomic boundaries. A later Docusaurus failure may leave a newer ignored diagram set on disk, while the last successfully published site remains intact.
- Complete-set promotion currently owns the entire root `generated/` tree. Another future generated-output producer will require a coordinated namespace or narrower promotion boundary.
- Public hosting, deployment, authentication, analytics, comments, in-site editing, versioned documentation releases, redirects, API extraction, source-code reference generation, and test-report publication remain outside Feature 002.
- Source renames can change derived routes because redirects are not yet a published contract. The pinned Docusaurus/local-search dependency graph also retains previously recorded non-critical transitive advisories.
