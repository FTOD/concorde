# Implementation Plan: Create Unified Project Docsite

**Branch**: `002-create-project-docsite` | **Date**: 2026-08-24 | **Spec**: [../spec.md](../spec.md)

**Accepted design baseline**: [../design.md](../design.md)

**Lifecycle**: Active temporal reconciliation plan. It records the remaining delta and validation
work for the current attempt; it does not amend the accepted design.

**Input**: Feature specification from `specs/concorde/features/002-create-project-docsite/spec.md`

## Summary

Create an independent TypeScript Docusaurus project under `docsite/` that presents three logical
navigation families and four source collections from two maintained roots: module and contract
specifications plus permanent feature specifications and accepted feature designs from the unified
`specs/` hierarchy, and project Markdown from `docs/`. A shared
registry classifies canonical files by path and meaning. Because Docusaurus cannot safely run the
Architecture and Features docs instances over the same physical source directory, the build creates
two ignored, disposable projections while retaining provenance to canonical `specs/` paths. A local
Concorde content plugin validates metadata and cross-collection links, emits a deterministic build
manifest, and verifies the rendered route inventory before candidate output is promoted.

The accepted design already establishes permanent design publication and a recursively discovered
Documentation collection. This attempt preserves that implementation and adds the content baseline
required by the revised specification: a progressive Documentation landing page plus maintained
quick-start, framework-overview, specification-model, project-structure, core-workflow, and command
guides. Each guide remains an ordinary project document, summarizes rather than duplicates normative
intent, and links readers to canonical architecture or feature sources. The delta also adds
inventory, route, link, and reader-exercise evidence for that baseline without changing manifest v3,
the three navigation families, source classification, or the accepted durable design.

## Accepted Design Delta

The accepted `design.md` remains byte-for-byte unchanged. Its existing realization already supports
recursive `docs/**/*.md` discovery, source-relative links, deterministic navigation, provenance,
search, and publication. The current implementation attempt adds only:

1. six maintained framework guides and an expanded Documentation landing page under `docs/`;
2. explicit content-purpose and canonical-authority-link rules for that guide set;
3. a Documentation-baseline inventory check covering source discovery, routes, landing-page links,
   and successful cross-collection authority links; and
4. manual reader exercises for artifact classification and correct edit/workflow selection, with
   automated prerequisites recorded separately from participant results.

No new Docusaurus instance, registry kind, route base, generated projection, or diagram is required.

## Technical Context

**Language/Version**: Node.js 20 or newer; TypeScript 5.9.x for site configuration, plugins,
presentation components, scripts, and tests

**Primary Dependencies**: Docusaurus 3.10.2 (`@docusaurus/core`, classic preset, and docs content
plugin), React 19, `@easyops-cn/docusaurus-search-local` 0.55.3, `fast-glob`, `gray-matter`, Unified
Markdown parsing utilities, and Ajv 8

**Storage**: Read-only version-controlled Markdown and Archify JSON under `specs/`; project Markdown
under `docs/`; delivered diagram projections under `generated/`; disposable Architecture/Features
content projections, Docusaurus cache, candidate build, search index, and JSON build manifest under
`docsite/.generated/` or `docsite/build/`

**Testing**: Vitest 4 for unit and contract tests; Ajv validation of the manifest schema and example;
Docusaurus production-build integration tests; shell-level repeatability and source-immutability checks

**Target Platform**: Static website built on Linux/macOS/Windows with Node.js 20+ and viewed in current
standards-compliant desktop and mobile browsers

**Project Type**: Independent static documentation website within the Concorde monorepository

**Performance Goals**: Clean install and local preview within 5 minutes on a typical contributor
machine; content validation and registry generation within 5 seconds for 1,000 Markdown sources;
client search responses within 500 ms for the initial project corpus

**Constraints**: No maintained content copies in `docsite/`; generated projections are ignored and
recreated from the registry; no writes under `docs/` or `specs/`; no LLM or hosted search required;
deterministic routes and manifest; failed builds preserve the last successful site; paths and manifest
entries remain canonical and project-relative; Docusaurus and plugin versions are lockfile pinned

**Scale/Scope**: Four content collections presented through three navigation families, including an
eight-page minimum Concorde Documentation baseline, up to 1,000 Markdown sources and 250 feature
specification/design pairs; one English-language, unversioned project site; local preview and
production build only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Gate | Pre-design evaluation | Post-design evaluation |
|---|---|---|
| Concorde is the workflow product and proving ground | PASS — feature 002 publishes Concorde's own architecture, maintained docs, and permanent feature artifacts. | PASS — quickstart validates all four source collections, three navigation families, and declared views against this repository. |
| Spec Kit-native and composable | PASS — Spec Kit remains authoritative for each feature `spec.md`; Concorde architecture artifacts share `specs/` without creating a parallel feature source. | PASS — path-based classification preserves the authority of module, contract, view, and feature artifacts while generated projections point back to canonical paths. |
| Recursive, bounded architecture | PASS — the root feature uses the root publication trace and is realized by Documentation. | PASS — the adjacent Documentation refinement and its bounded one-level view exist without exposing child internals at the root. |
| Explicit ownership and feature alignment | PASS — `feature.concorde.publish-project-docsite` owns the project outcome at the root level. | PASS — `feature.documentation.publish-project-docsite` is owned by `module.concorde.documentation` and refines only the adjacent root feature. |
| Contracts govern every boundary | PASS — publication is already exposed through `contract.documentation.architecture-site`; source and build details require design contracts. | PASS — content-source, build-command, published-site, and manifest contracts now define inputs, outputs, failures, compatibility, and evidence. |
| One authority per fact | PASS — feature `spec.md` owns behavioral intent, feature `design.md` owns accepted realization, module/contract Markdown owns architectural prose, module and feature-owned Archify JSON own their distinct structural/explanatory views, and `docs/` owns project documentation. | PASS — framework guides provide progressive explanation but link normative claims back to canonical architecture or feature sources; canonical-path provenance, temporal exclusions, ignored staging/build directories, and disposable projections/indexes preserve those authorities. |
| Deterministic validation and reviewed evidence | PASS — the feature requires reproducible builds and explicit diagnostics without an LLM. | PASS — sorted registries, schema checks, fixture tests, route verification, and atomic promotion supply deterministic evidence. |
| Accessibility, provenance, and textual representation | PASS — all initial sources are textual and the specification requires provenance. | PASS — the shared page wrapper exposes content kind, source path, ID/status where applicable, and semantic text outside presentation chrome; the Documentation landing page supplies a text-first learning path through all six guides. |

No constitution violations or justified exceptions remain. The implemented architecture sources,
Archify delivery receipts, and executable docsite evidence satisfy the post-design gates; browser
visual review remains separately recorded as pending where the required browser is unavailable.

## Project Structure

### Documentation (this feature)

```text
specs/concorde/features/002-create-project-docsite/
├── spec.md
├── design.md
├── diagrams/
│   └── project-docsite-publication-flow.json
├── contracts/
│   ├── build-interface.md
│   ├── build-manifest-contract.md
│   ├── build-manifest.schema.json
│   ├── build-manifest.example.json
│   ├── content-sources.md
│   └── published-site.md
└── implementation/
    ├── checklists/
    │   └── requirements.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md
    └── validation.md
```

### Source Code (repository root)

```text
docs/
├── index.md                         # ordered Documentation reading path and authority summary
├── quick-start.md                   # preview, local bundle setup, and first feature
├── framework-overview.md            # purpose, influences, hierarchy, and adjacent boundaries
├── specification-model.md           # modules, features, contracts, diagrams, and hardening
├── project-structure.md              # workspace locations, authority, and correct edit paths
├── core-workflow.md                 # end-to-end architecture-aware development lifecycle
├── commands.md                      # normal phases, Concorde operations, and installed layers
└── contributing/
    └── docsite.md                   # contributor-facing author/build guidance

docsite/
├── package.json
├── package-lock.json
├── tsconfig.json
├── docusaurus.config.ts
├── sidebars.architecture.ts
├── sidebars.docs.ts
├── sidebars.features.ts
├── .generated/                     # ignored, disposable renderer/build workspace
│   └── content/
│       ├── architecture/            # projected from canonical specs modules/contracts
│       └── features/                # projected from canonical specs feature specs
├── static/
│   └── img/
├── plugins/
│   └── concorde-content/
│       ├── index.ts                 # lifecycle, global data, post-build verification
│       ├── registry.ts              # discovery, metadata, routes, stable sorting
│       ├── links.ts                 # cross-collection Markdown link mapping
│       ├── manifest.ts              # deterministic manifest projection
│       ├── types.ts                 # registry and projection types
│       └── validation.ts            # findings and contract checks
├── scripts/
│   ├── build.ts                     # validate, candidate build, atomic promotion
│   ├── inspect.ts                   # print registry/validation summary
│   ├── materialize-content.ts       # recreate renderer-only projections
│   └── validate.ts                  # deterministic preflight entry point
├── src/
│   ├── components/
│   │   ├── ArchitectureView.tsx
│   │   ├── ContentProvenance.tsx
│   │   └── ProjectSummary.tsx
│   ├── css/
│   │   └── custom.css
│   ├── pages/
│   │   └── index.tsx
│   └── theme/
│       └── DocItem/
│           └── Layout/
│               └── index.tsx        # wraps all three docs instances with provenance
└── tests/
    ├── contract/
    │   ├── build-interface.test.ts
    │   ├── build-manifest.test.ts
    │   └── content-sources.test.ts
    ├── integration/
    │   ├── accessibility.test.ts
    │   ├── atomic-promotion.test.ts
    │   ├── document-authoring.test.ts
    │   ├── framework-guides.test.ts
    │   ├── feature-publication.test.ts
    │   ├── performance.test.ts
    │   ├── production-build.test.ts
    │   └── source-immutability.test.ts
    ├── unit/
    │   ├── architecture-sources.test.ts
    │   ├── feature-specifications.test.ts
    │   ├── links.test.ts
    │   └── registry.test.ts
    └── fixtures/
        ├── valid-project/
        └── invalid-projects/

specs/concorde/
├── module.md                        # register root feature and publication contract
├── architecture.json               # trace root publication interaction
├── features/
│   └── 002-create-project-docsite/  # canonical root feature workspace
└── modules/documentation/
    ├── module.md                    # register Documentation refinement and contracts
    ├── architecture.json            # bounded Documentation publication scenario
    ├── contracts/
    │   ├── architecture-site/contract.md
    │   ├── build-interface/contract.md
    │   ├── build-manifest/contract.md
    │   └── project-content/contract.md
    └── features/
        └── 001-publish-project-docsite/
            ├── spec.md
            └── design.md

generated/architecture/
├── concorde-root.html               # regenerated Archify projection, never edited
├── documentation.html               # regenerated Archify projection, never edited
└── project-docsite-publication-flow.html # feature-owned explanatory projection, never edited
```

**Structure Decision**: `docsite/` is a self-contained npm project and owns only publication code,
configuration, formatting, tests, caches, and generated output. Root `docs/` and the unified `specs/`
hierarchy remain the two maintained source roots. The local plugin is intentionally private to the
site until a later Concorde extension feature extracts a reusable publication command. Files beneath
`docsite/.generated/content/` are renderer inputs only and always retain canonical source provenance.

## Design

### Content Pipeline

```text
specs/**/module.md + specs/**/contracts/**/contract.md + specs/**/{spec,design}.md + docs/**/*.md + delivered Archify HTML
  -> discover and parse
  -> validate identities, metadata, links, and routes
  -> recreate ignored Architecture and Features renderer projections from canonical specs paths
  -> load projected Architecture, direct Documentation, and projected Features through three docs instances
  -> render provenance and local search index
  -> verify actual route inventory
  -> write build-manifest.json
  -> atomically promote candidate output
```

The source registry is the single build-time authority for inclusion and route mapping. The
materializer, Concorde plugin, and cross-collection link transformer use it; the Docusaurus instances
remain the rendering boundary. Projected paths are mapped back to canonical `specs/` paths before
link resolution and provenance. Registry entries and findings are sorted by normalized
project-relative canonical path, so filesystem enumeration order cannot change the result.

### Docusaurus Composition

- An Architecture docs instance reads a disposable build-time projection of module and
  boundary-contract Markdown, publishes below `/architecture`, and embeds declared delivered views.
- The classic preset's default docs instance reads `../docs`, publishes below `/docs`, accepts `*.md`,
  and uses an autogenerated documentation sidebar. The framework-guide baseline uses the same
  ordinary project-document path; front-matter positions provide a stable progressive order without
  per-page registration in site configuration.
- A second `@docusaurus/plugin-content-docs` instance with ID `features` reads a disposable projection
  of permanent `**/spec.md` and `**/design.md` files, publishes below `/features`, groups each pair,
  and generates labels from feature titles.
- The blog is disabled. The root landing page is a maintained presentation component in `docsite/`,
  not copied content.
- Docusaurus link, anchor, Markdown-link, and duplicate-route severities are all configured to throw.
- Local search indexes `/architecture`, `/docs`, and `/features`; it does not enable Ask AI or depend on a remote crawler.
- Last-update timestamps are disabled because wall-clock and VCS-derived presentation data are outside
  the deterministic content contract.

### Maintained Documentation Baseline

The implementation maintains eight project documents. `docs/index.md` introduces the three site
views and links directly to the six learning guides. `docs/contributing/docsite.md` remains the
publication-maintainer guide. The six new pages form this reader journey:

| Order | Source | Reader outcome | Canonical authority link |
|---|---|---|---|
| 1 | `docs/quick-start.md` | Preview this site or install a local Concorde release and begin a feature. | Features 001 and 003 |
| 2 | `docs/framework-overview.md` | Explain Concorde's purpose, influences, bounded hierarchy, and non-goals. | Root module architecture |
| 3 | `docs/specification-model.md` | Distinguish module architecture, behavior spec, accepted design, contracts, diagrams, and temporal attempts. | Feature 001 |
| 4 | `docs/project-structure.md` | Choose the correct canonical edit location for a representative change. | Root module architecture |
| 5 | `docs/core-workflow.md` | Follow ownership, specification, review, implementation, validation, hardening, and publication. | Feature 001 |
| 6 | `docs/commands.md` | Distinguish normal Spec Kit phases, Concorde commands, skills, adapters, launchers, and runtime. | Feature 003 |

The guide names are maintained project paths, not a new registry enum or manifest schema. A focused
integration test validates that every baseline path is discovered exactly once, has the expected
route and landing-page link, and includes at least one resolvable canonical authority link when it
summarizes normative behavior. Existing link and production-build validation remain responsible for
the destination routes and rendered output.

### Validation and Provenance

The Concorde plugin validates sources before page rendering. Project documents require a unique
project-relative path and a title from front matter or the first level-one heading. Feature
specifications additionally require a unique stable feature ID, `kind: feature`, owning module,
title, and recorded status. Feature designs require a paired canonical specification and a non-empty
title. A shared page wrapper obtains registry data by route and displays content kind, source path,
and feature ID/status where applicable without changing the source document.

Markdown file links are resolved against the canonical source file first. When the target belongs to
any of the three logical collections, the link transformer maps it through the registry to its site
route while preserving the anchor. This supports `docs`-to-`specs` and cross-view `specs` links despite
the separate Docusaurus plugin instances and staged render roots. Missing, ambiguous, outside-root,
and excluded targets become actionable validation findings.

### Safe Build Lifecycle

`npm run build` invokes a TypeScript wrapper rather than Docusaurus directly. It validates the
canonical registry, recreates the Architecture and Features content projections, creates a fresh
candidate output beneath ignored `docsite/.generated/`, runs the production build, verifies routes and
the manifest, then promotes the candidate to `docsite/build/`. Promotion retains the previous build
until the candidate rename succeeds. Any validation, materialization, rendering, or promotion error
returns a non-zero exit status and leaves the last successful output in place.

### Architecture Alignment

The root feature remains the canonical project-level Spec Kit feature because the user outcome spans
project documentation, feature specifications, architecture specifications, and publication. The
narrower `feature.documentation.publish-project-docsite`, maintained at
`specs/concorde/modules/documentation/features/001-publish-project-docsite/spec.md`, refines that
outcome with Documentation-owned requirements and a representative example; it does not replace or
repeat the parent specification.

The architecture-complete design is now represented by:

1. root feature registration and canonical path in `specs/concorde/module.md`;
2. adjacent Documentation feature registration and module ownership;
3. module-owned contract identities under `specs/concorde/modules/documentation/contracts/`;
4. feature-local Phase 1 contract documents, schemas, and examples that define the detailed
   representation and behavior referenced by those module contracts;
5. bounded root and Documentation Archify views that preserve one-level visibility; and
6. a separate text-backed Feature 002 sequence that explains build-component invocation without
   expanding either module view; and
7. validated, regenerated HTML projections and recorded executable publication evidence.

## Feature Diagram Strategy

Feature 002 preserves an explicit core-view sufficiency rationale: the bounded root
`specs/concorde/architecture.json` already shows the stable Documentation, Architecture Core, Spec
Kit Integration, maintainer, and coding-agent relationships at this feature's ownership level, so a
second feature-owned core architecture view would duplicate canonical structure.

| Role and source | Narrow question and textual counterpart | Delivery and validation |
|---|---|---|
| Supplemental sequence: `diagrams/project-docsite-publication-flow.json` | Call order for `publish-architecture`, explained by the spec's “Scenario and Component Diagram” section plus the content-source, build-interface, manifest, and published-site contracts. | Deliver `generated/architecture/project-docsite-publication-flow.html`; require Archify 9/9 showcase validation, source provenance, declaration-driven feature-page embedding, source/output freshness, and a truthful visual-review receipt that remains pending when no browser is available. |

The supplemental sequence cannot redefine source ownership, contracts, or the stable module
organization. Its JSON remains below `diagrams/`; the generated HTML remains a disposable read model.

## Implementation Phases

### Phase A — Architecture and Contracts

Establish module ownership, adjacent refinement, boundary-contract registrations, detailed
representations, module Archify views, and the feature-owned publication sequence first. Validate
stable IDs, one-level visibility, text/diagram agreement, cross-boundary interactions, and generated
Archify freshness.

### Phase B — Independent Site Skeleton

Create the locked npm/TypeScript Docusaurus project, root `docs/` entry content, three docs instances,
navigation, formatting, ignored projection/build paths, and basic local preview.

### Phase C — Registry and Publication Controls

Implement source discovery, metadata parsing, renderer projection materialization, canonical route
mapping, cross-collection links, provenance, manifest generation, deterministic search, diagnostics,
and atomic candidate promotion.

### Phase D — Evidence and Self-Hosting

Add unit, contract, fixture, integration, source-immutability, repeatability, and atomic-failure tests,
including permanent feature-design inclusion and temporal implementation exclusion. Run the
production build against Concorde's real `docs/` and `specs/`, then verify manifest v3 and the
generated site without committing generated site output.

### Phase E — Framework Orientation Delta

Author the six framework guides, revise the Documentation landing page and README entry points, and
add the baseline inventory/authority-link integration test. Re-run source immutability, route and
link validation, search/build checks, and the full production gate against all eight project
documents. Record automated evidence separately from the two participant-dependent comprehension
criteria; do not infer participant success from a passing build.

## Complexity Tracking

No constitution violations require complexity justification.
