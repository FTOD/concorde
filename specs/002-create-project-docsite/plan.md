# Implementation Plan: Create Unified Project Docsite

**Branch**: `002-create-project-docsite` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-create-project-docsite/spec.md`

## Summary

Create an independent TypeScript Docusaurus project under `docsite/` that reads canonical architecture
Markdown from `architecture/`, project Markdown from `docs/`, and canonical feature `spec.md` files
from `specs/`. Three Docusaurus docs-plugin instances provide separate `/architecture`, `/docs`, and
`/features` route spaces. A local
Concorde content plugin builds a shared source registry, validates metadata and cross-collection links,
adds source provenance, emits a deterministic build manifest, and verifies the rendered route
inventory. A build wrapper renders to a candidate directory and promotes it only after all checks pass.

## Technical Context

**Language/Version**: Node.js 20 or newer; TypeScript 5.9.x for site configuration, plugins,
presentation components, scripts, and tests

**Primary Dependencies**: Docusaurus 3.10.2 (`@docusaurus/core`, classic preset, and docs content
plugin), React 19, `@easyops-cn/docusaurus-search-local` 0.55.3, `fast-glob`, `gray-matter`, Unified
Markdown parsing utilities, and Ajv 8

**Storage**: Read-only version-controlled Markdown under `architecture/`, `docs/`, and `specs/`;
maintained Archify JSON under `architecture/`; delivered diagram projections under `generated/`;
disposable Docusaurus cache, candidate build, search index, and JSON build manifest under `docsite/`

**Testing**: Vitest 4 for unit and contract tests; Ajv validation of the manifest schema and example;
Docusaurus production-build integration tests; shell-level repeatability and source-immutability checks

**Target Platform**: Static website built on Linux/macOS/Windows with Node.js 20+ and viewed in current
standards-compliant desktop and mobile browsers

**Project Type**: Independent static documentation website within the Concorde monorepository

**Performance Goals**: Clean install and local preview within 5 minutes on a typical contributor
machine; content validation and registry generation within 5 seconds for 1,000 Markdown sources;
client search responses within 500 ms for the initial project corpus

**Constraints**: No canonical content copies in `docsite/`; no writes under `architecture/`, `docs/`, or `specs/`; no LLM
or hosted search required; deterministic routes and manifest; failed builds preserve the last successful
site; paths and manifest entries remain project-relative; Docusaurus and plugin versions are lockfile
pinned

**Scale/Scope**: Three content collections, up to 1,000 Markdown sources and 250 canonical feature
specifications in the initial design; one English-language, unversioned project site; local preview and
production build only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Gate | Pre-design evaluation | Post-design evaluation |
|---|---|---|
| Concorde is the workflow product and proving ground | PASS — feature 002 publishes Concorde's own architecture, maintained docs, and Spec Kit features. | PASS — quickstart validates all three collections and declared views against this repository. |
| Spec Kit-native and composable | PASS — `specs/` remains Spec Kit-owned and is consumed without relocation or rewriting. | PASS — the content-source contract includes only canonical `spec.md`; no parallel feature source is introduced. |
| Recursive, bounded architecture | PASS — the root feature uses the existing root `publish-architecture` view and is realized by Documentation. | PASS — implementation tasks must add an adjacent Documentation refinement and bounded module view before architecture completion. |
| Explicit ownership and feature alignment | PASS — `feature.concorde.publish-project-docsite` owns the project outcome at the root level. | PASS — `module.concorde.documentation` owns generation; its planned refinement links only to the root feature. |
| Contracts govern every boundary | PASS — publication is already exposed through `contract.documentation.architecture-site`; source and build details require design contracts. | PASS — content-source, build-command, published-site, and manifest contracts now define inputs, outputs, failures, compatibility, and evidence. |
| One authority per fact | PASS — `architecture/`, `docs/`, and `specs/` remain maintained authorities; the site and Archify HTML are projections. | PASS — direct external paths, provenance banners, ignored build directories, and disposable indexes prevent canonical duplication. |
| Deterministic validation and reviewed evidence | PASS — the feature requires reproducible builds and explicit diagnostics without an LLM. | PASS — sorted registries, schema checks, fixture tests, route verification, and atomic promotion supply deterministic evidence. |
| Accessibility, provenance, and textual representation | PASS — all initial sources are textual and the specification requires provenance. | PASS — the shared page wrapper exposes content kind, source path, ID/status where applicable, and semantic text outside presentation chrome. |

No constitution violations or justified exceptions remain. Architecture-source updates and Archify
validation are implementation gates, not deferred exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/002-create-project-docsite/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── build-interface.md
│   ├── build-manifest-contract.md
│   ├── build-manifest.schema.json
│   ├── build-manifest.example.json
│   ├── content-sources.md
│   └── published-site.md
└── tasks.md                         # created later by $speckit-tasks
```

### Source Code (repository root)

```text
docs/
├── index.md                         # canonical project-documentation entry page
└── contributing/
    └── docsite.md                   # contributor-facing author/build guidance

docsite/
├── package.json
├── package-lock.json
├── tsconfig.json
├── docusaurus.config.ts
├── sidebars.docs.ts
├── sidebars.features.ts
├── static/
│   └── img/
├── plugins/
│   └── concorde-content/
│       ├── index.ts                 # lifecycle, global data, post-build verification
│       ├── registry.ts              # discovery, metadata, routes, stable sorting
│       ├── links.ts                 # cross-collection Markdown link mapping
│       ├── manifest.ts              # deterministic manifest projection
│       └── validation.ts            # findings and contract checks
├── scripts/
│   ├── build.ts                     # validate, candidate build, atomic promotion
│   └── inspect.ts                   # print registry/validation summary
├── src/
│   ├── components/
│   │   ├── ContentProvenance.tsx
│   │   └── ProjectSummary.tsx
│   ├── css/
│   │   └── custom.css
│   ├── pages/
│   │   └── index.tsx
│   └── theme/
│       └── DocItem/
│           └── Layout/
│               └── index.tsx        # wraps both docs instances with provenance
└── tests/
    ├── contract/
    │   ├── build-manifest.test.ts
    │   └── content-sources.test.ts
    ├── integration/
    │   ├── production-build.test.ts
    │   ├── source-immutability.test.ts
    │   └── atomic-promotion.test.ts
    ├── unit/
    │   ├── links.test.ts
    │   ├── registry.test.ts
    │   └── validation.test.ts
    └── fixtures/
        ├── valid-project/
        └── invalid-projects/

architecture/concorde/
├── module.md                        # register root feature and publication contract
├── architecture.json               # trace root publication interaction
└── modules/documentation/
    ├── module.md                    # register Documentation refinement and contracts
    ├── architecture.json            # bounded Documentation publication scenario
    ├── contracts/
    │   ├── project-content/contract.md
    │   └── architecture-site/contract.md
    └── features/
        └── publish-project-docsite.md

generated/architecture/
└── documentation.html              # regenerated Archify projection, never edited
```

**Structure Decision**: `docsite/` is a self-contained npm project and owns only publication code,
configuration, formatting, tests, caches, and generated output. Root `architecture/`, `docs/`, and
`specs/` remain separate maintained sources. The local plugin is intentionally private to the
site until a later Concorde extension feature extracts a reusable publication command.

## Design

### Content Pipeline

```text
architecture/**/*.md + docs/**/*.md + specs/**/spec.md + delivered Archify HTML
  -> discover and parse
  -> validate identities, metadata, links, and routes
  -> load through three docs-plugin instances
  -> render provenance and local search index
  -> verify actual route inventory
  -> write build-manifest.json
  -> atomically promote candidate output
```

The source registry is the single build-time authority for inclusion and route mapping. Both the
Concorde plugin and cross-collection link transformer use it; the Docusaurus instances remain the
rendering boundary. Registry entries and findings are sorted by normalized project-relative path, so
filesystem enumeration order cannot change the result.

### Docusaurus Composition

- An Architecture docs instance reads `../architecture`, publishes below `/architecture`, accepts
  `**/*.md`, and embeds a sandboxed delivered view when Markdown declares one.
- The classic preset's default docs instance reads `../docs`, publishes below `/docs`, accepts `*.md`,
  and uses an autogenerated documentation sidebar.
- A second `@docusaurus/plugin-content-docs` instance with ID `features` reads `../specs`, includes only
  `**/spec.md`, publishes below `/features`, and generates labels from the canonical feature title.
- The blog is disabled. The root landing page is a maintained presentation component in `docsite/`,
  not copied content.
- Docusaurus link, anchor, Markdown-link, and duplicate-route severities are all configured to throw.
- Local search indexes `/architecture`, `/docs`, and `/features`; it does not enable Ask AI or depend on a remote crawler.
- Last-update timestamps are disabled because wall-clock and VCS-derived presentation data are outside
  the deterministic content contract.

### Validation and Provenance

The Concorde plugin validates sources before page rendering. Project documents require a unique
project-relative path and a title from front matter or the first level-one heading. Feature
specifications additionally require a unique stable feature ID, `kind: feature`, owning module, title,
and recorded status. A shared page wrapper obtains registry data by route and displays content kind,
source path, and feature ID/status without changing the source document.

Markdown file links are resolved against the source file first. When the target belongs to either
collection, the link transformer maps it through the registry to its site route while preserving the
anchor. This supports `docs`-to-`specs` links despite the separate Docusaurus plugin instances. Missing,
ambiguous, outside-root, and excluded targets become actionable validation findings.

### Safe Build Lifecycle

`npm run build` invokes a TypeScript wrapper rather than Docusaurus directly. It validates sources,
creates a fresh candidate output beneath ignored `docsite/.generated/`, runs the production build,
verifies routes and the manifest, then promotes the candidate to `docsite/build/`. Promotion retains
the previous build until the candidate rename succeeds. Any validation, rendering, or promotion error
returns a non-zero exit status and leaves the last successful output in place.

### Architecture Alignment

The existing root feature remains the canonical Spec Kit feature because the user outcome spans
project documentation, Spec Kit feature sources, and publication. Implementation is structurally
refined by `feature.documentation.publish-project-docsite`, owned by
`module.concorde.documentation`. That refinement links to the root feature and records only placement,
contracts, and its representative scenario; it does not duplicate this specification's requirements.

Before implementation is architecture-complete:

1. Register the root feature and its canonical spec in `architecture/concorde/module.md`.
2. Register the Documentation refinement and split its inline contracts into canonical contract files.
3. Add the required project-content contract and reconcile the architecture-site output contract with
   the contracts designed here.
4. Add a bounded Documentation view and update the existing root publication trace without revealing
   Documentation internals at the root level.
5. Validate both maintained Archify JSON files and regenerate their HTML projections.

## Implementation Phases

### Phase A — Architecture and Contracts

Update module ownership, refinement, boundary contracts, and Archify views first. Validate stable IDs,
one-level visibility, cross-boundary interactions, and generated Archify freshness.

### Phase B — Independent Site Skeleton

Create the locked npm/TypeScript Docusaurus project, root `docs/` entry content, three docs instances,
navigation, formatting, ignored build paths, and basic local preview.

### Phase C — Registry and Publication Controls

Implement source discovery, metadata parsing, route mapping, cross-collection links, provenance,
manifest generation, deterministic search, diagnostics, and atomic candidate promotion.

### Phase D — Evidence and Self-Hosting

Add unit, contract, fixture, integration, source-immutability, repeatability, and atomic-failure tests.
Run the production build against Concorde's real `architecture/`, `docs/`, and `specs/`, then verify the generated site
and manifest without committing generated site output.

## Complexity Tracking

No constitution violations require complexity justification.
