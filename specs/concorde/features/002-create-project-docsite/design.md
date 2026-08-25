# Feature Design: Publish Project Docsite

**Design status**: Accepted current realization.

## Realization Overview

Feature 002 is realized by the private TypeScript Docusaurus project under `docsite/`. It publishes a read-only project model from two maintained source roots without creating a second content authority: `specs/` supplies architecture sources plus permanent feature specifications and designs, while `docs/` supplies project-authored guidance. A shared registry classifies those inputs into four source collections—Architecture, Documentation, Feature Specifications, and Feature Designs—and presents them through three navigation families: Architecture, Documentation, and Features.

The Documentation collection reads `docs/**/*.md` directly. Architecture and Features use ignored projections under `docsite/.generated/content/` because separate Docusaurus content-plugin instances cannot safely share the same physical `specs/` loader root. Those projections preserve canonical source identity and are recreated for each preview or build. The successful site contains provenance-bearing pages, local search, sandboxed Archify views, and a schema-valid deterministic build manifest. Production output is built as a candidate and promoted only after source, route, rendering, and manifest validation succeeds.

## Module and Feature Collaboration

The root feature `feature.concorde.publish-project-docsite` owns the project-wide outcome. Its Documentation-owned refinement, `feature.documentation.publish-project-docsite`, realizes that outcome behind the boundaries declared by `module.concorde.documentation`. The bounded root and Documentation structures remain defined by `specs/concorde/architecture.json` and `specs/concorde/modules/documentation/architecture.json`; this design relies on those views instead of redefining their one-level organization.

Architecture Core, Spec Kit, and project maintainers provide maintained inputs through `contract.documentation.project-content`. Architecture Core supplies module and contract sources and their declared bounded views; Spec Kit supplies canonical feature `spec.md` and accepted `design.md` pairs; maintainers supply ordinary Markdown under `docs/`. The Documentation module invokes Archify through `contract.documentation.archify-renderer`, exposes deterministic npm operations through `contract.documentation.build-interface`, emits JSON inventory through `contract.documentation.build-manifest`, and provides the finished static read model through `contract.documentation.architecture-site`.

Inside the Documentation boundary, the Concorde content registry owns discovery, classification, canonical hashing, stable routes, and metadata extraction. Validation and link mapping operate on that registry. The materializer creates renderer-only Architecture and Features inputs, Docusaurus renders three content families and local search, shared page components expose provenance and embedded diagrams, and the build wrapper verifies and promotes the complete candidate.

## Scenario Realization

For `publish-architecture`, a maintainer invokes `inspect`, `validate`, `start`, `test`, `build`, `typecheck`, or `check` from `docsite/`. The registry discovers every eligible `**/module.md`, `**/contracts/**/contract.md`, `docs/**/*.md`, `**/spec.md`, and `**/design.md`, parses identity and navigation metadata, hashes exact source bytes, records temporal Markdown as excluded, and rejects invalid paths, identities, declarations, links, and routes with stable diagnostics.

Declared architecture and feature-diagram JSON remains maintained intent. Its delivered HTML must resolve beneath `generated/`, match the declaration in the owning source, and remain fresh enough to enter the registry. Feature diagrams are discovered from `spec.md`, limited to one core architecture view plus any supplemental views, and projected with role, kind, scenarios, route, title, source path, and SHA-256 provenance. The Feature 002 publication sequence remains supplemental because the root architecture view already provides the stable component view at this level.

After validation, the materializer removes and recreates ignored Architecture and Features projections while Documentation continues to read canonical `docs/` directly. Registry-backed Markdown transformation maps same-family and cross-family source links to public routes and preserves fragments. Three Docusaurus content instances render the Architecture, Documentation, and paired Features views; the shared layout adds source kind, canonical path, stable identity, ownership, lifecycle status, paired-design provenance, and sandboxed Archify presentations. Local search covers all three route spaces without a hosted crawler or LLM.

During production publication, the build wrapper renders into a fresh candidate directory. The content plugin verifies that every expected source route was actually rendered and writes manifest v3 with four collection declarations, sorted pages, explicit exclusions, route inventory, generator versions, source hashes, diagram provenance, and passed deterministic checks. The wrapper validates that manifest against the normative schema and atomically promotes the candidate to `docsite/build/`; a failed candidate is removed and the prior successful site is restored or retained.

Ordinary documentation authoring requires changes only beneath `docs/`; add, rename, move, and removal operations are reflected by the next registry build without page registration in `docsite/`. Concorde's maintained Documentation baseline consists of `docs/index.md`, six progressive framework guides, and `docs/contributing/docsite.md`. The landing page links directly to the learning path, and guides that summarize normative behavior link back to canonical Architecture or Features authorities.

## Durable Implementation Decisions

- `docs/` and `specs/` remain the only maintained content roots. `docsite/` owns publication code, configuration, presentation, tests, caches, projections, and generated output, but no canonical copies.
- The registry is the single inclusion and route-mapping authority shared by validation, link rewriting, projections, presentation metadata, tests, and manifest generation. All observable lists and findings use normalized project-relative paths and stable sorting.
- Four source collections map to three public navigation families. Feature specifications and accepted feature designs are distinct permanent collections grouped together under `/features`; every Markdown file under `implementation/` is explicitly excluded as `not-canonical-feature-artifact`.
- Architecture and Features are copied only into ignored, disposable renderer projections. Published provenance always points to canonical `specs/` paths, and validation and build operations do not mutate `docs/` or `specs/`.
- Repository-relative Markdown is resolved against the canonical source before route rewriting. Included cross-collection targets become published routes with fragments preserved; missing, escaping, ambiguous, or temporally excluded Markdown targets fail validation.
- Manifest v3 is custom UTF-8 JSON governed by the feature's schema and example. It contains no timestamp or absolute path, records source hashes and verified routes, and is emitted only for a successful candidate.
- Feature and architecture diagrams are declaration-driven. Maintained JSON and generated HTML keep distinct authority, delivered views are sandboxed, and each page retains textual source provenance and a standalone-view link.
- `npm run build` owns failure-safe candidate publication. Validation, projection recreation, rendering, actual-route verification, manifest emission, schema validation, and atomic promotion form one success boundary; any failure returns non-zero and preserves the previous successful output.
- The implementation is pinned to Node.js 20 or newer, Docusaurus 3.10.2, TypeScript 5.9, React 19, Ajv 8, and the committed npm lockfile. Local search is self-hosted through the pinned Docusaurus search plugin.
- Accessibility is structural rather than decorative: pages retain searchable text outside diagrams, provenance uses semantic labels, interactive views have titles and sandbox restrictions, keyboard focus remains visible, and narrow-layout behavior is covered by executable checks.
- The self-hosting Documentation baseline remains ordinary recursively discovered Markdown. It introduces no special manifest kind, second guide registry, or presentation-owned normative source.

## Traceability and Evidence

The detailed source, build, manifest, and published-output guarantees remain in `contracts/content-sources.md`, `contracts/build-interface.md`, `contracts/build-manifest-contract.md`, `contracts/build-manifest.schema.json`, `contracts/build-manifest.example.json`, and `contracts/published-site.md`. Module-level ownership and boundary summaries remain under `specs/concorde/modules/documentation/`, while `diagrams/project-docsite-publication-flow.json` and its delivered HTML trace the publication call order without replacing those contracts.

The implementation is concentrated in `docsite/plugins/concorde-content/` for registry, validation, link mapping, manifest projection, and Docusaurus lifecycle integration; `docsite/scripts/` for inspection, validation, projection materialization, and atomic production builds; and `docsite/src/` plus the three sidebar/configuration files for navigation, provenance, diagrams, and the landing experience. The eight maintained project documents under `docs/` provide the progressive framework learning path.

Executable evidence remains under `docsite/tests/`: contract tests cover stable commands, diagnostics, source rules, and manifest schema; unit tests cover registry ordering, architecture identity, feature identity, and canonical link mapping; integration tests cover authoring, permanent feature publication, framework-guide inventory and authority links, accessibility, scale, source immutability, production routes and diagrams, repeatable manifests, and atomic rollback. The complete `npm run check`, direct Concorde validation, and docsite validation pass for the accepted source state.

## Known Limitations

Public hosting, deployment, authentication, analytics, comments, in-site editing, versioned documentation releases, API extraction, source-code reference generation, and test-report publication remain outside this feature. The site is an English-language, unversioned local/static read model. Source renames can change derived routes because redirects are not yet a published contract.

The pinned Docusaurus and local-search dependency graph retains non-critical transitive npm advisories recorded during validation; compatibility-preserving dependency remediation remains follow-up maintenance. Generated projections, search indexes, manifests, and Archify HTML are disposable outputs and must be rebuilt rather than edited.
