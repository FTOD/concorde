# Feature Abstract: Create Unified Project Docsite

`feature.concorde.publish-project-docsite` · specified at `module.concorde` · about five minutes.
This page is enough to understand what the docsite shows, how it is built, and what must hold; the
links at the end only redirect you when you want more.

## Purpose

Present the whole project as one website: the root `README.md` project introduction, maintained
architecture sources and their delivered Archify views, project documentation authored under
`docs/`, and every feature's canonical specification and permanent design under `specs/`, so that a
maintainer, contributor, reviewer, or prospective user can understand intended behavior and accepted
realization without navigating the repository by hand. The site is a read-only projection: it never
becomes a second content authority, and its `/` homepage is the maintained README rather than a
separate site-only narrative.

It also exists to teach. A maintained set of framework guides — overview, quick start, specification
model, project structure, workflow, and command reference — gives a first-time reader a progressive
path into Concorde instead of leaving them to reconstruct the framework from normative
specifications alone.

## Functionality

**One project entry point and three navigation families over the maintained source hierarchy.**

| Family | Sources | What a visitor gets |
|---|---|---|
| Home | root `README.md` | The same introduction visible in the repository, leading with the project summary, key features, and all Concorde-specific commands before status and detailed setup material. |
| Architecture | `specs/**/module.md`, its sibling `design.md`, and `specs/**/architecture/contracts/**/contract.md` | The maintained hierarchy with stable ID, kind, owning module or parent, and provenance; every diagram beneath a module's `architecture/diagrams/` is delivered and embedded on the module page in a sandbox beside a standalone link. |
| Documentation | every eligible Markdown file recursively under `docs/`, plus its declared supplemental diagrams | The authored hierarchy preserved, including the framework guides, docs-owned interactive views, and a landing page with a recommended reading path. |
| Features | the canonical `abstract.md`, `design.md`, and `implementation.md` of every feature directory under `specs/` | Navigation mirrors the declared module hierarchy, lists each module's registered features, and nests explicit sub-features beneath their parent; routes remain identity-derived and drafts stay visible. |

**What a maintainer can do.**

- **Preview and build** from the independent `docsite/` project with one documented entry point;
  both operations use the same inclusion, routing, navigation, and validation rules.
- **Deliver diagrams as part of the build**: every declared module-, feature-, and docs-owned Archify JSON
  source is discovered, validated, and rendered to standalone HTML before the site consumes it, using
  the officially installed project-local `.agents/skills/archify` package — no committed HTML, no
  manual rendering step, no machine-specific renderer environment variable.
- **Author without registration**: a new document under `docs/` or a new `design.md` under `specs/`
  appears on the next build; nothing is copied into `docsite/`.
- **Maintain one introduction**: editing root `README.md` updates both the repository presentation and
  the next generated homepage; the manifest records one source-to-`/` mapping and the page displays
  that provenance.
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

This feature declares no core diagram of its own: the project-level interaction view
<a href="/architecture/concorde-interaction-architecture.html">Concorde interaction architecture</a>
(maintained source `specs/concorde/architecture/diagrams/level-view.json`) already shows Auto-Docs,
Workspace Files, Skills, Scripts, Spec Kit, and the maintainer. The
supplemental <a href="/architecture/project-docsite-publication-flow.html">docsite publication
flow</a> (maintained source `diagrams/project-docsite-publication-flow.json`) answers only the
call-order question. In one sketch:

```text
README.md ────┐
docs/**/*.md ─┼─▶ source registry ──▶ diagram delivery ──▶ content materialization ──▶ Docusaurus build
specs/**      ─┘        │                  Archify skill (.agents/skills/archify)                 │
   (module.md · contract.md · design.md · design)     │ validate + deliver every declared JSON     │
                                                    ▼                                            ▼
                                             generated/ (disposable)         candidate validation ──▶ atomic promotion ──▶ browser
```

- **`docsite/`** owns configuration, presentation, and the preview and build entry points; it is
  realized by the Auto-Docs module's refinement `feature.auto-docs.publish-project-docsite`
  behind `contract.auto-docs.build-interface`, `contract.auto-docs.build-manifest`, and
  `contract.auto-docs.architecture-site`.
- **Root `README.md`, `docs/`, and `specs/`** are the maintained published sources, consumed through
  `contract.auto-docs.project-content`; Scripts keeps the `specs/` sources valid.
- **The Archify renderer**, reached through `contract.auto-docs.archify-renderer`, owns diagram
  validation and standalone HTML; Docusaurus owns the generated pages, search index, and manifest.
- **Generated projections** — the delivered `generated/` tree, staged content, the build manifest,
  and the site — are reproducible, ignored read models.

## Logic

**From maintained sources to a browsable site**

1. **Discover** every declared Archify JSON source and verify the project-local renderer.
2. **Validate and deliver** each diagram to a candidate set; only a complete, verified set replaces
   the disposable delivery tree.
3. **Register** the sources: map `README.md` uniquely to `/`, classify every other file into its
   collection, derive routes, extract identity, and validate links and metadata.
4. **Project independently**: derive Architecture pages and Features module groups from declared
   module containment; derive feature routes from stable identity and explicit feature containment,
   regardless of their shared physical placement under `specs/`.
5. **Materialize** the independent Architecture and Features projections and build the site with
   Docusaurus, including search and the deterministic manifest.
6. **Validate the candidate** and promote it atomically; any failure preserves the last successful
   output and names the responsible source.
7. **Browse**: the visitor reads the same README at the repository or site root, reaches all three
   families from it, follows provenance back to maintained files, and edits meaning there — never in
   a generated page.

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
- Root `README.md` is the only maintained project introduction and owns `/`; it opens with the
  project explanation, key features, and all five Concorde-specific commands, and no site-only page
  duplicates that narrative (FR-009, FR-051, FR-052).
- The homepage preserves supported README Markdown and rewrites repository-relative links for the
  generated routes without altering repository rendering; registry, validation, search, manifest,
  and provenance treat it as exactly one project document, while missing, invalid, or competing
  homepage sources fail before publication (FR-053, FR-054, FR-055).
- The homepage offers distinct Architecture, Documentation, and Features entry points. Features
  navigation follows declared module containment and module feature registration, then explicit
  parent/sub-feature containment; raw storage segments never become route parents. Providing modules
  are visible navigation groups while refinement relationships remain metadata and cross-links;
  titles, stable IDs, kinds, statuses, provenance, and drafts remain available
  (FR-009, FR-010, FR-011, FR-018, FR-028, FR-048, FR-049, FR-050).
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
- Preview and production discover, validate, and deliver every module-, feature-, or docs-owned diagram before consuming
  it; a clean checkout builds without committed HTML; the renderer is the compatibility-checked
  project-local skill; failed delivery stops publication with no stale fallback; deliveries,
  receipts, and build products stay out of version control; manifests carry only project-relative
  provenance (FR-041, FR-042, FR-043, FR-044, FR-045, FR-046, FR-047).
- A custom page beneath `docs/` may declare supplemental Archify JSON from its adjacent `diagrams/`
  directory; Auto-Docs embeds it on that page with source provenance and a standalone route (FR-056).

## Read Next

- **Exact requirements, scenarios, and success criteria** — [design.md](design.md): six user stories,
  FR-001 to FR-056, and the measurable outcomes.
- **How the accepted implementation realizes this feature** — [implementation.md](implementation.md) (accepted
  realization and implementation detail).
- **The contracts** — `contracts/content-sources.md`,
  `contracts/build-interface.md`,
  `contracts/build-manifest-contract.md` with its
  schema (`contracts/build-manifest.schema.json`), and `contracts/published-site.md`.
- **The level this feature belongs to** — [module.md](../../module.md) (the root summary) and the
  module that realizes it: [Auto-Docs](../../architecture/modules/auto-docs/module.md) with its
  refinement [publish-project-docsite](../../architecture/modules/auto-docs/features/001-publish-project-docsite/design.md).
- **Contributing to the site** — [docs/contributing/docsite.md](../../../../docs/contributing/docsite.md),
  the shared project homepage [README.md](../../../../README.md), and the guides the site publishes:
  [docs/index.md](../../../../docs/index.md),
  [docs/ontology.md](../../../../docs/ontology.md), and
  [docs/project-structure.md](../../../../docs/project-structure.md).
