# Feature Abstract: Create Unified Project Docsite

`feature.concorde.publish-project-docsite` · specified at `module.concorde` · about five minutes.
This page is enough to understand what the docsite shows, how it is built, and what must hold; the
links at the end only redirect you when you want more.

## Purpose

Present the whole project as one website: the maintained architecture sources and their delivered
Archify views, the project documentation authored under `docs/`, and every feature's canonical
specification and permanent design under `specs/`, so that a maintainer, contributor, reviewer, or
prospective user can understand intended behavior and accepted realization without navigating the
repository by hand. The site is a read-only projection: it never becomes a second content authority.

It also exists to teach. A maintained set of framework guides — overview, quick start, specification
model, project structure, workflow, and command reference — gives a first-time reader a progressive
path into Concorde instead of leaving them to reconstruct the framework from normative
specifications alone.

## Functionality

**Three navigation families over two canonical source roots.**

| Family | Sources | What a visitor gets |
|---|---|---|
| Architecture | `specs/**/module.md` and `specs/**/contracts/**/contract.md` | The maintained hierarchy with stable ID, kind, owning module or parent, and provenance; when a source declares an Archify JSON view, its delivered HTML is embedded in a sandbox beside a standalone link. |
| Documentation | every eligible Markdown file recursively under `docs/` | The authored hierarchy preserved, including the framework guides and a landing page with a recommended reading path. |
| Features | the canonical `design.md` of every feature directory under `specs/` | Each feature by title, stable ID, and lifecycle status, grouped with its permanent design; drafts stay visible as drafts. |

**What a maintainer can do.**

- **Preview and build** from the independent `docsite/` project with one documented entry point;
  both operations use the same inclusion, routing, navigation, and validation rules.
- **Deliver diagrams as part of the build**: every declared module- and feature-owned Archify JSON
  source is discovered, validated, and rendered to standalone HTML before the site consumes it, using
  the officially installed project-local `.agents/skills/archify` package — no committed HTML, no
  manual rendering step, no machine-specific renderer environment variable.
- **Author without registration**: a new document under `docs/` or a new `design.md` under `specs/`
  appears on the next build; nothing is copied into `docsite/`.
- **Search and trace**: project-wide discovery across all three families, and every page records
  its maintained source path and content kind.
- **Fail loudly**: broken internal links, unreadable sources, invalid metadata, route collisions,
  and missing, invalid, or escaping diagram deliveries stop the build with a diagnostic that names
  the source; a failed build never replaces the last successful site.

**Not part of this feature**: public hosting, deployment, authentication, analytics, comments,
in-site editing, and versioned release archives; API references, source-code extraction, and test
reports remain later features; plans, tasks, checklists, and `attempt/` artifacts are never
presented as feature specifications.

## Structure

This feature declares no core diagram of its own: the root level view
<a href="/architecture/concorde-root.html">Concorde root</a> (maintained source
`specs/concorde/architecture.json`) already shows Documentation, Architecture Core, Spec Kit
Integration, the coding agent, and the maintainer at the level where the feature is owned. The
supplemental <a href="/architecture/project-docsite-publication-flow.html">docsite publication
flow</a> (maintained source `diagrams/project-docsite-publication-flow.json`) answers only the
call-order question. In one sketch:

```text
docs/**/*.md ─┐                                   Archify skill (.agents/skills/archify)
specs/**      ─┴─▶ source registry ──▶ diagram delivery ──▶ content materialization ──▶ Docusaurus build
   (module.md · contract.md · design.md · design)     │ validate + deliver every declared JSON     │
                                                    ▼                                            ▼
                                             generated/ (disposable)         candidate validation ──▶ atomic promotion ──▶ browser
```

- **`docsite/`** owns configuration, presentation, and the preview and build entry points; it is
  realized by the Documentation module's refinement `feature.documentation.publish-project-docsite`
  behind `contract.documentation.build-interface`, `contract.documentation.build-manifest`, and
  `contract.documentation.architecture-site`.
- **`docs/` and `specs/`** are the only maintained content roots, consumed through
  `contract.documentation.project-content`; Architecture Core keeps the `specs/` sources valid.
- **The Archify renderer**, reached through `contract.documentation.archify-renderer`, owns diagram
  validation and standalone HTML; Docusaurus owns the generated pages, search index, and manifest.
- **Generated projections** — the delivered `generated/` tree, staged content, the build manifest,
  and the site — are reproducible, ignored read models.

## Logic

**From maintained sources to a browsable site**

1. **Discover** every declared Archify JSON source and verify the project-local renderer.
2. **Validate and deliver** each diagram to a candidate set; only a complete, verified set replaces
   the disposable delivery tree.
3. **Register** the sources: classify each file into its collection, derive its route, extract its
   identity, and validate links and metadata.
4. **Materialize** the Architecture and Features projections and build the site with Docusaurus,
   including search and the deterministic manifest.
5. **Validate the candidate** and promote it atomically; any failure preserves the last successful
   output and names the responsible source.
6. **Browse**: the visitor reaches all three families from the landing page, follows provenance back
   to the maintained file, and edits meaning there — never in a generated page.

**Rules the implementation must keep**

- `docsite/` holds configuration and presentation only; `docs/` is the canonical home of project
  documentation, and feature and architecture specifications stay in the one `specs/` hierarchy
  under their owning modules (FR-001, FR-002, FR-003, FR-004, FR-032).
- Every eligible document, canonical `design.md`, module, and contract source is included and
  discovered on the next build without a copy or per-page registration; supporting files under
  `specs/` are not specifications (FR-005, FR-006, FR-007, FR-012, FR-027).
- Collection and presentation never modify `docs/` or `specs/`; the site, staged content, indexes,
  and other projections are disposable, and readers edit meaning only in maintained sources
  (FR-008, FR-021, FR-026).
- The landing page offers distinct Architecture, Documentation, and Features entry points;
  navigation preserves the maintained hierarchies and exposes title, stable ID, kind, status, and
  provenance, and drafts remain discoverable with their recorded status (FR-009, FR-010, FR-011,
  FR-018, FR-028).
- Every page identifies its source path and kind, supported relative links resolve across the three
  families with a path back to the source, discovery spans the whole project, and one reading
  experience applies to all collections (FR-013, FR-014, FR-015, FR-016, FR-022).
- Broken links, unreadable sources, invalid required metadata, and route collisions stop a
  successful build with an actionable diagnostic; empty sources yield an explanatory landing or a
  diagnostic; a failed build is never reported as complete and never replaces the last successful
  output (FR-017, FR-024, FR-025).
- Preview and production share one rule set, and repeated builds from identical inputs give the same
  inventory, navigation, and mapping without an LLM call (FR-019, FR-020).
- Contributors are told how to install prerequisites, preview, build, and diagnose failures
  (FR-023).
- A declared Archify view is embedded in a sandbox with a direct link and textual provenance;
  missing, invalid, escaping, or unpublishable views stop the build; Markdown, JSON, and delivered
  HTML remain separate authorities and projections (FR-029, FR-030, FR-031).
- The feature maintains one text-backed publication sequence view that the canonical feature page
  discovers and embeds automatically (FR-033).
- The Documentation collection explains what Concorde controls, offers a quick-start path, separates
  the authority and lifecycle of each artifact class, maps the workspace, walks the end-to-end
  workflow, distinguishes Spec Kit phases from Concorde operations, and links every summarizing
  guide to its canonical source (FR-034, FR-035, FR-036, FR-037, FR-038, FR-039, FR-040).
- Preview and production discover, validate, and deliver every declared diagram before consuming
  it; a clean checkout builds without committed HTML; the renderer is the compatibility-checked
  project-local skill; failed delivery stops publication with no stale fallback; deliveries,
  receipts, and build products stay out of version control; manifests carry only project-relative
  provenance (FR-041, FR-042, FR-043, FR-044, FR-045, FR-046, FR-047).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): five user stories,
  FR-001 to FR-047, and the measurable outcomes.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (accepted
  realization and implementation detail).
- **The contracts** — `contracts/content-sources.md`,
  `contracts/build-interface.md`,
  `contracts/build-manifest-contract.md` with its
  schema (`contracts/build-manifest.schema.json`), and `contracts/published-site.md`.
- **The level this feature belongs to** — [module.md](../../module.md) (the root summary) and the
  module that realizes it: [Documentation](../../modules/documentation/module.md) with its
  refinement [publish-project-docsite](../../modules/documentation/features/001-publish-project-docsite/design.md).
- **Contributing to the site** — [docs/contributing/docsite.md](../../../../docs/contributing/docsite.md),
  and the guides the site publishes: [docs/index.md](../../../../docs/index.md) and
  [docs/project-structure.md](../../../../docs/project-structure.md).
