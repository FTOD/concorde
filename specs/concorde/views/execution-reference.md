# Views execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Views Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module Specs](../module.md#terminology) | Defined in Concorde Framework. |
| [Implementation Specs](../module.md#terminology) | Defined in Concorde Framework. |
| [Registry](../module.md#terminology) | Defined in Concorde Framework. |
| [Document role](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Document unit](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Publication candidate](pipeline.md#terminology) | Defined in From source documents to a published site. |
| [Promotion](pipeline.md#terminology) | Defined in From source documents to a published site. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Entity](../module.md#terminology) | Defined in Concorde Framework. |
| [Requirement](../module.md#terminology) | Defined in Concorde Framework. |
| [Scenario](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Semantic completeness](../spec/structure.md#terminology) | Defined in What structural validation tells you. |

## Publication pipeline {#pipeline-publication-pipeline}

The public API is TypeScript and Docusaurus plugin hooks. Profile 15 publication reads an explicit
project registry, creates derived documentation, validates a built publication candidate, and promotes only a
successfully checked candidate. It exposes no agent tool or read proxy. Consumers do not need a
Python API or a provider Spec to invoke the functions and interpret the values defined here.
Publication has no Module/Scenario graph view or architecture-graph output. Its registry validation and
Module navigation still use declared relationships; inline authored Mermaid diagrams remain part
of ordinary document rendering.

#### Project introduction {#pipeline-project-introduction}

Site identity schema 1 optionally carries the `homepage` presentation object described in
[publication](scenarios.md#scenario.views.publish-homepage). The content plugin passes the
validated identity to the root renderer and watches `docsite/site.json` for changes. When the
option is absent, the root preserves its redirect to the registered entry Module. The introduction
is a human navigation surface outside registered Spec membership and `sourceDigest`; the
registered-page manifest retains its registry-derived meaning.

#### Project-owned custom documentation {#pipeline-project-owned-custom-documentation}

The generic template defaults to the Module Specs tab and registry-parent sidebar; explicitly
classified implementation companions enable the parallel Implementation Specs tab. Both are
registered Spec reading, not custom docs. Optional
`customDocs` collections and `custom-docs/index.ts` supply independent project documentation
and executable pages under the [custom docs agreement](scenarios.md#scenario.views.custom-docs).
They remain outside registered-page identity, ownership and agent context. Collection paths cannot
include registered Specs; duplicate published routes fail the build. Concorde configures its
Protocol collection and Agent Graphs extension through these same entry points. The removed
`protocolDocs` option fails with migration guidance; unregistered instruction/wire projections
are no longer read or published. Inline Mermaid remains supported in registered and custom docs.

#### Mermaid rendering and source compatibility {#pipeline-mermaid-rendering-and-source-compatibility}

The Markdown renderer consumes the literal body of each `mermaid` fence, supports the project's
flowchart, entity-relationship and state-diagram syntax, and produces an accessible diagram within
the containing page. `accTitle` and `accDescr` remain available to assistive technology. A diagram
must fit the reading column or allow inspection without hiding content. Renderer directives may not
fetch external source files or execute arbitrary page script. Render failures identify the owning
source document and prevent publication of a candidate that silently drops a diagram.

Source edits use ordinary document versioning: changing an edge, label, title or description
changes the containing document digest and invalidates source-dependent build evidence. A shared
Markdown document still publishes once and retains its sole owner and all explicit inclusion reasons. Dependency links and
diagram nodes do not add target contexts or undeclared registry relationships. Rendering support
still requires ordinary site dependencies to be installed; initialization does not fetch them.

#### Operation contract navigation {#pipeline-operation-contract-navigation}

Execution explanations link to [Planning](../planning/execution-reference.md), [Tasks](../planning/execution-reference.md),
[Implementation](../implementation/execution-reference.md), [Spec Authoring](../spec-authoring/execution-reference.md),
[Review](../review/execution-reference.md), [Validation](../validation/execution-reference.md),
[Delivery](../delivery/execution-reference.md), [Query and Routing](../query-routing/execution-reference.md),
[Topology](../topology/execution-reference.md), [Development Graph](../dev-loop/execution-reference.md) and
[Specification Graph](../specify-loop/execution-reference.md). These are Spec ownership boundaries;
executable graphs still come only from the current factories under the
[Harness inspection contract](../harness/scenarios.md#scenario.harness.graph-inspection).
Moving a definition requires updating retained source links; it creates no invented executable graph.

### Design {#pipeline-design}

#### Materialization and required build collaborators {#pipeline-materialization-and-required-build-collaborators}

The materialization identity is the UTF-8 JSON file
`docsite/.generated/scoped-materialization.json`, relative to the project root, containing
`{schema_version: 1, sourceDigest: string}`. Its version 1 is independent of `ScopedRegistry`
schema 21. Materialization writes compact JSON followed by a newline, after the assets and
sidebar succeed as specified in [materialization](scenarios.md#scenario.views.materialize). `sourceDigest`
is the loaded registry's source digest, with the digest format defined above; the record adds no
page inventory or projection-content identity.

`postBuild` parses this record and requires `schema_version` to equal 1 and `sourceDigest` to
equal the loaded registry's `sourceDigest`, alongside the fresh-source and route checks below.
Read failures, JSON parse failures and version or digest mismatches reject post-build before
verification artifacts are emitted; the normal build failure rules preserve the previously
promoted site. This retains the existing identity format and comparisons.

Both Spec sidebars follow registry `parent` relationships. In `moduleSpecsSidebar`, root Modules
are top-level items; each Module opens its `module.md` and expands to its owned module-collection
companions and child Modules. `implementationSpecsSidebar` contains only explicitly classified
implementation companions, in document order, nested under owner and ancestor Module categories
in registry order. Its categories have no duplicated Module-entry doc links; empty branches are
omitted. No file-directory tree or outer composition category is generated. References remain
navigation to the sole owner's canonical page and never create extra sidebar document entries.
`scopedSidebar` defaults to the module collection and `publicationSidebar` aliases it.
Materialization selects each page's displayed sidebar from its collection, and omits the
implementation sidebar entirely when there are no such pages. The navbar uses the same condition.
Provenance navigation links explanation pages to their owner's implementation companions and detail
pages back to their Module entry; links honor the configured site base URL.

In Module Specs, a Module category links directly to its `module.md` through a Docusaurus category
`link` of type `doc`. Its child items contain only additional module-collection documents and child
Modules, never a second entry for `module.md`. A Module with no child items is a direct document link. The Module
page displays its complete authored content, including Usage and Design,
with section navigation. Mermaid diagrams render exactly where their fences occur in the authored
Markdown; the renderer does not inject or duplicate an overview before or after the article.
Document titles and labels use the filename without `.md`, except Module entry pages, which use
the Module's title. Source provenance retains the exact source path.

Every registered document has one Docusaurus doc reference, either as an item or a category link.
Consumer appearances of referenced documents use ordinary links to that same canonical page.
This preserves access through each owning Module without duplicate doc IDs. `primaryDocument`
requires exactly one registered `module.md` for a Module; a Page's sole `owner` and `primaryOf`
marks that choice with the owning Module ID, and diagrams and the site entry use it rather than
arbitrary array order. `rewriteLinks` rewrites supported local Markdown links to the registered
page routes. Diagram references use the owning document's Relationships subsection anchor; there
are no external diagram-source or delivered-HTML links. Invalid or unregistered local destinations
are rejected. Outside fenced code blocks it handles inline links and images with these forms, whose
URL has no whitespace or closing parenthesis:

```markdown
[label](url)
![label](url)
```

A URL beginning with a scheme, `#`, or `/` is preserved unchanged. For other destinations,
separate the suffix beginning at the first `#`, then separate the suffix beginning at the first
`?` in the remaining part. Only the path before those suffixes resolves relative to the source
document directory using POSIX normalization and selects the single page registered at that
sourcePath. An empty path with a query selects the current source document. Append the original
query and fragment suffixes to the canonical route in that order, preserving their contents,
including additional question marks in a query and question marks within a fragment. Neither
suffix participates in registered-document lookup. An invalid or unregistered source path is
rejected even when it has a query. Relative non-Spec assets have no matching page and are
rejected; callers use a supported absolute or root-relative asset URL. Unsupported Markdown forms
are left unchanged by this rewrite function. A reference selects from all registered source
paths, not just the referring Module's collection, so changing a document's owner alone does
not invalidate its source-path or canonical-page references. Link validation begins during
rewrite/materialization, not during registry loading. The function returns text without changing
sources. Preserving a URL or an unsupported Markdown form during rewriting does not exempt a
navigation link emitted in the candidate from the final internal-link validation below.

`contentLoaded({content, actions})` calls `actions.setGlobalData` with the Workspace 15 entry
target and page metadata without Markdown bodies. It supplies no architecture nodes or edges.
`getPathsToWatch()` returns absolute configuration, registry and registered Markdown paths, which
include the inline diagram sources. `postBuild({outDir, routesPaths})` requires the fresh source
digest and materialization identity to match the loaded model, and every expected page route to be
in the rendered route inventory after base-URL normalization. Otherwise it throws before emitting
verification artifacts. After the build manifest, it writes one legacy redirect stub per alias at
`<outDir>/<alias without its leading slash>.html`: a minimal HTML document with a
base-URL-prefixed `<meta http-equiv="refresh">` and `<link rel="canonical">` to the document's
canonical page, plus a visible link, mirroring the default root redirect. Following an alias with
a fragment preserves that fragment at the canonical destination. These are the complete
collaborator promises this Profile 15 path relies on.

#### Module main-document validation {#pipeline-module-main-document-validation}

Profile 15 publication requires one local `module.md` per Module starting with the unique level-2
Purpose, Terminology, Usage, Design and Relationships sections, each with explanatory prose. The entry and
explanatory topics have role module; formal requirements, scenarios and canonical contracts are
permitted only in directly Module-owned implementation-role companions. Every unit has schema-2
metadata with an explicit role, and the retired publication extension is rejected. The publisher's primary-page table of contents shows major sections rather than flooding
navigation with every formal definition ID. All definitions remain readable, searchable and linked.

Every reading file has a matching metadata companion. Invalid ownership, metadata shapes, local
meaning anchors, requirement/scenario syntax or scoped diagram entities/labels reject publication.
Canonical contract examples are checked using an explicit offline schema vocabulary; schema
references cannot fetch resources. These checks do not prove semantic completeness. The Protocol
defines reading membership; this publisher's layout never trims complete paired-source context.

Diagram rendering belongs to the normal Markdown/site candidate transaction. It writes no
`generated/diagrams/` tree and cannot change Framework outputs under `generated/protocol`,
`generated/agents` or `generated/docs`. The site uses its locked Mermaid dependency, with no
separately installed renderer Skill, generated-source JSON or independent diagram receipt.

Production builds use `docsite/.generated/docusaurus-production` for Docusaurus-generated modules
and aliases. `preparePublication` mode `build` clears only that generated directory; the build
process sets `DOCUSAURUS_GENERATED_FILES_DIR_NAME` to the same relative path. Default preview mode
uses `.docusaurus`. A production build preserves an active preview's generated modules and cache,
so development-only debug routes cannot overwrite the production module graph. Here, Docusaurus's
module graph refers to its internal build machinery, not a published graph view.

#### Publication compatibility status {#pipeline-publication-compatibility-status}

The TypeScript loader admits Profile 15/schema 5 and publishes schema 21 with unique owner and
includedBy provenance. It validates one-level references and canonical definition/binding agreement,
exposes canonical definition anchors and renders links without transclusion. Manifest identity and
watched registry/source inputs invalidate publication when ownership or references change.

### Precise specifications {#pipeline-precise-specifications}

The Views Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
