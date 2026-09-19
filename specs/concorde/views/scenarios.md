# Views scenarios

These precise specifications belong directly to the [Views Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

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
| [Ownership](../spec/registry.md#terminology) | Defined in Registry. |
| [Composition](../spec/registry.md#terminology) | Defined in Registry. |
| [Use](../spec/registry.md#terminology) | Defined in Registry. |
| [Implementation binding](../spec/registry.md#terminology) | Defined in Registry. |
| [Entity](../module.md#terminology) | Defined in Concorde Framework. |
| [Requirement](../module.md#terminology) | Defined in Concorde Framework. |
| [Scenario](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Snapshot](../module.md#terminology) | Defined in Concorde Framework. |

## Publication service

### scenario.views.scaffold-propose — Proposing a docsite scaffold

- GIVEN a registered project and optional `--title`, `--repository`, `--url`, `--base-url` and `--github-pages` options
- WHEN `concorde docsite --propose` runs
- THEN it returns a deterministic project-relative JSON scaffold proposal
- AND it writes nothing to the project
- AND the proposed publishing template contains no standalone graph page, Graph navigation entry or graph-view-only resources or dependencies

### scenario.views.scaffold-apply — Applying an accepted scaffold proposal

- GIVEN a previously proposed, still-current JSON proposal
- WHEN `concorde docsite --apply --proposal PATH` runs under the host's worktree policy
- THEN it checks before-digests and writes only owned scaffold files
- AND it leaves every project Spec document unchanged

### scenario.views.scaffold-stale-rejected — A stale or unsafe scaffold proposal is rejected

- GIVEN a proposal whose before-digests no longer match the project, or that names a path outside the scaffold's own ownership
- WHEN `--apply` is requested
- THEN the application is rejected
- AND any already-staged files are restored to their original bytes

### scenario.views.publish-candidate — Publishing derives one canonical page per registered document

- GIVEN an explicitly registered project registry
- WHEN the site is built
- THEN every registered physical document publishes exactly one canonical page at a readable route derived from its source path
- AND a document referenced by several Modules still publishes once, showing its sole owner and every explicit inclusion reason
- AND inline Mermaid fences render in their authored position using the site's locked Mermaid integration

The route is `/specs/<source path with a leading specs/ root removed and .md dropped>`, or the full
path when a project's Specs are not entirely rooted at `specs/`. The Module Specs sidebar
uses registry Module parentage, with root Modules directly at the top level in registry order.
There is no file-directory tree or outer Module composition category. Every Module opens its
unique local `module.md`; expanding it reveals its owned Module Specs companions in document
order, followed by child Modules in registry order. Referenced documents remain under their sole
owner and do not create duplicate pages or sidebar entries. A Module without children or
Module Specs companions is a direct document link.

### scenario.views.reading-collections — Separate reading paths preserve complete Module specifications

- GIVEN registered companion documents whose metadata explicitly selects the implementation reading collection
- WHEN the site is built
- THEN the navbar exposes Module Specs and Implementation Specs as parallel reading tabs
- AND each registered reading document publishes once at its existing source-derived canonical route with all stable anchors, ownership and inclusion provenance retained
- AND Module Specs contains every Module entry and its module-role companions, while Implementation Specs contains only implementation-classified companions under the same registry parentage, omitting empty branches
- AND a detail page links back to its Module entry and that Module's explanation pages link to its Implementation Specs
- AND both collections remain searchable human-readable normative content in the same complete Module Spec context
- BUT a reference never duplicates a provider document into the consumer's sidebar or transfers ownership

Protocol 8 schema-2 metadata requires `document.role` to be `module` or `implementation`, without
a default. The publisher derives the two reading collections from that role. An empty implementation
collection creates neither a sidebar nor a tab; a Module's `module.md` entry must have role `module`.
The role is never inferred from filenames, headings, definition syntax, implementation bindings or
ordinary links. Role edits change metadata bytes and invalidate context, review and publication
evidence without changing context membership or canonical page routes. The retired
`concorde.publication` extension is rejected, including when it agrees with the new role.

Implementation Specs means precise normative specifications that implementations must satisfy,
including external guarantees, not merely internal code details or temporary implementation plans.
Authors keep purpose, correct use, significant design and important guarantees understandable in
the Module entry, and link to canonical exact definitions in companions instead of copying them.
The publisher preserves authored content; it does not automatically split sections or generate a
replacement summary. Module entries and topic pages cannot define requirements, scenarios or
canonical structured contracts. Every Concorde Module follows this organization; precise definitions
belong directly under their owning Module, not under a topical page's independent ownership.

### scenario.views.reject-reading-collection — Invalid publication classification fails admission

- GIVEN missing or invalid document.role, schema-1 metadata, the retired concorde.publication extension, an implementation-role Module entry, or a formal definition in an explanatory document
- WHEN the publication registry is loaded
- THEN admission fails with the source metadata or reading entry identified
- AND no candidate is materialized or promoted

### scenario.views.publish-without-graph — Publishing retains reading and navigation without a graph view

- GIVEN a valid registered project using the current publishing template
- WHEN the site is built and promoted
- THEN the site exposes no standalone `/graph` page, Graph navigation entry or graph-view UI
- AND it emits no `architecture-graph.json` or graph-specific global-data projection
- AND registered pages, Module navigation, source provenance, identity anchors and inline Mermaid rendering remain available
- AND enabled homepage and project-owned custom documentation surfaces retain their normal reading and navigation behavior

Removing this feature includes its dedicated implementation, resources and dependencies. A shared
resource or dependency remains when another retained publication function needs it; in particular,
inline Mermaid rendering remains supported. The docsite provides no substitute embedded graph view
or redirect from the removed graph page.

### scenario.views.publish-preserves-previous-on-failure — An incomplete or stale candidate does not replace the published build

- GIVEN changes to registered sources during generation, a missing expected page, an unresolved internal page or anchor link, or a failed Mermaid render
- WHEN the candidate is validated before promotion
- THEN promotion is refused
- AND the previously published build is preserved unchanged

### scenario.views.publish-legacy-redirect — Current document references and ownership aliases resolve

- GIVEN a still-registered document whose owner changes from Module A to Module B while a currently published document of A retains a reference to its source path or canonical page and an existing anchor
- WHEN the current build is validated and promoted
- THEN that retained reference reaches the document's single canonical page and the requested anchor independently of the referring document's owner
- AND a redirect stub for every legacy alias derived from a current owner resolves to that same canonical page, preserving a requested fragment
- BUT an unresolved retained internal reference prevents promotion until the reference is corrected

A cross-Module reference is legitimate navigation: A need not register a document merely to link
to it, and publication does not remove such a reference when ownership changes. Canonical
document identity and source-path resolution do not depend on the referring Module. This scenario
does not promise an unchanged source path after a document is moved to a different filesystem path.

The current registry and registered source documents are the authoritative inputs. Legacy aliases
are generated only for current owners under the rules in `pipeline.md`. Aliases of removed
ownerships have no indefinite retention guarantee and are not copied from a previous build. If a
current document still uses an alias that those inputs do not resolve, publication rejects the
candidate until that reference is corrected to the registered document's source path, canonical
route or a current alias. The publisher neither invents historical ownership nor silently drops
the reference; no historical-alias store is required.

This compatibility promise concerns registered-document navigation, not the removed standalone
graph page. Every Concorde Module contains an inline Mermaid entity diagram in its `module.md`
Relationships subsection, with accessible title and description. Publication renders that fence in
its authored position; the containing Markdown is the sole authored diagram source and already
participates in source identity. No external diagram JSON, standalone diagram HTML, renderer Skill
or separate diagram installation is used. Local document links resolve against the complete
explicit registered-page inventory, independently of the referring Module's collection; unknown
or ambiguous destinations and missing anchors fail validation.

### scenario.views.publish-repeat-without-graph — Rebuilding replaces obsolete graph output

- GIVEN an existing published build that contains the former standalone graph page and architecture-graph artifact
- WHEN a fresh build using the current publishing template successfully validates and is promoted
- THEN the replacement published build contains neither the former graph page nor its dedicated artifacts or assets
- AND a subsequent successful build retains that absence and the registered-document reading and navigation behavior
- BUT a failed candidate leaves the previous published build unchanged under the normal promotion rules

### scenario.views.publish-homepage — Publishing an explicitly configured project introduction

- GIVEN site identity schema 1 in `docsite/site.json` includes a valid `homepage` object
- WHEN the site builds
- THEN the root page renders the configured introduction, features, workflow and quickstart with the site's title and description metadata
- AND when `homepage.reference` is configured, a reference section after the quickstart renders its tables with section navigation, column headers and keyboard-accessible horizontal scrolling on narrow screens
- AND its primary Spec navigation resolves to the registered entry Module's canonical page, with local links respecting the configured base URL
- AND project-owned `homepage.links` and the repository link appear only when configured
- BUT the introduction does not join any Module collection, add a registered-page manifest entry, or grant agent context

### scenario.views.publish-homepage-default — Preserving the default entry redirect

- GIVEN the site identity omits `homepage`
- WHEN the site builds
- THEN its root redirects to the registered entry Module's canonical page and includes a visible continuation link
- AND the packaged renderer introduces no Concorde-specific marketing content into the consumer project

### scenario.views.publish-homepage-invalid — Rejecting incomplete introduction content

- GIVEN the site identity includes an invalid or incomplete `homepage` object
- WHEN publication loads that identity
- THEN it fails with an error naming `docsite/site.json` and the invalid field
- AND no candidate is promoted

The optional object contains nonempty `eyebrow`, `title` and `description` strings. Its `features`
object contains a nonempty `title` and nonempty `items` array; its `workflow` object contains
nonempty `title` and `description` strings and a nonempty `steps` array. Each array entry has
nonempty `title` and `description` strings. Its `quickstart` object contains nonempty `title`,
`description` and `code` strings. These values are project-owned presentation text, rendered
without interpreting HTML. The adapter remains project-neutral and scaffolding omits the option.

The optional `homepage.reference` object contains nonempty `title` and `description` strings and
a nonempty `tables` array. Each table has nonempty `title` and `description` strings, a nonempty
`columns` array of nonempty strings and a nonempty `rows` array. Every row contains exactly one
nonempty string per column. These values also render as plain text. Invalid reference content
fails with its field path; omitting the object preserves the homepage without a reference section.

### scenario.views.custom-docs — Publishing separate project documentation

- GIVEN a consumer project configures `customDocs` collections or a `custom-docs/index.ts` extension
- WHEN its site builds
- THEN its custom documents and pages have independent navbar entries outside Module Specs
- AND custom pages do not register Spec ownership, appear in the registered-page manifest or grant agent Spec context
- BUT a collection containing a registered Spec, a conflicting route, missing enabled content or broken internal link rejects the build

Without classified implementation companions, the generic template defaults to one documentation
tab, **Module Specs**. **Implementation Specs**, when present, is registered normative content,
not a custom docs collection. Optional `customDocs`
in site identity is an array of collections with nonempty `id`, `label`, `path` and
`routeBasePath`, plus optional `sidebarPath`. IDs are unique lowercase slug names other than
`default`. Route bases are distinct, non-overlapping slash-separated alphanumeric/underscore/hyphen
segments outside `specs/`. Paths and sidebar paths resolve relative to `docsite/`. Each collection
publishes Markdown/MDX through an independent docs plugin, with its own sidebar and search index.
Authors supply an index page with slug `/` for the collection tab's landing route.

Optional project-owned `docsite/custom-docs/index.ts` exports an object with `plugins` and
`navbarItems` arrays for executable custom pages. The adapter includes these additive extensions;
Docusaurus rejects duplicate routes, including conflicts with registered pages. Extension authors
keep their pages outside `/specs` and supply explicit tabs. Custom content stays outside the Spec
registry; it is not an implicit source of Spec context. We recommend separate tabs for all custom
docs rather than adding them to Module Specs. The scaffold excludes `custom-docs/` and
project-owned site identity bytes.

`homepage.links` optionally supplies an array of `{label, to}` values: nonempty labels and either
local absolute routes or HTTP(S) URLs. Local links honor the site's base URL. No Protocol or Graph
link is built into the homepage renderer.

### scenario.views.protocol-docs-tab — Concorde publishes its standard through custom docs

- GIVEN Concorde's project-owned configuration selects `protocol/` as a custom docs collection
- WHEN the site builds
- THEN Spec Protocol remains at `/protocol` with its chapter sidebar and search index
- AND it retains an independent tab without Spec provenance wrappers or registry membership
- BUT ordinary consumer scaffolds copy neither this configuration nor the site's custom documentation and assets

The removed `protocolDocs` field is rejected whenever present, including false, with a migration
message directing authors to `customDocs` and the template README. Concorde's protocol collection
and sidebar are project configuration, not a special case in the generic template. Inline Mermaid
remains available in registered and custom documentation.

These generated views are human navigation, not agent context grants. The publication Tool may read
multiple registered collections deterministically; an agent still receives one host-bound target
snapshot.

### scenario.views.publish-reference-link — References preserve one canonical page

- GIVEN one provider-owned interface document referenced by two consumer Modules, one by Module and one by document ID
- WHEN a publication candidate is built
- THEN it emits one canonical definition page with its sole owner and inclusion provenance
- AND consumer Markdown links point to that page and its stable contract/scenario anchors without embedding its body
- AND reference or ownership changes invalidate source-bound publication evidence

## Publication pipeline

### scenario.views.operation-graphs-in-owner-specs — Operation Graphs are read in their owning Specs

- GIVEN Concorde's source checkout, where every executable Graph has one Graph Spec in the implementation-role documents of the Module that owns it
- WHEN the site is built
- THEN no navbar tab, homepage link or route publishes a separate Operation or execution-graph page, and no `agent-graphs` page is emitted
- AND each Graph Spec appears once, on its owner's Implementation Specs page, with its State, Nodes and Edges parts before its Mermaid flowchart
- AND the owner's module-role reading links directly to that Graph Spec

Publication renders a Graph Spec's Mermaid fence like any other inline diagram and derives nothing
from the executable factories, so building the site needs no Python graph environment. That a Graph
Spec equals its compiled Graph is proven by the configured Graph Spec check, not by publication.

### scenario.views.load-registry — Loading the registry validates identities and memberships

- GIVEN `.concorde/config.json` with `profile_version: 15` and a safe relative registry path
- WHEN `loadScopedRegistry` runs
- THEN it returns a model whose Module IDs are unique, whose Module parents are acyclic and whose entry target exists and is a Module
- AND malformed identities, ownership, references or contract bindings throw before any file is written
- AND it returns no graph-specific node or edge projection

### scenario.views.materialize — Materializing writes disposable staged content and its identity record

- GIVEN a loaded registry model
- WHEN `materializeScoped` runs
- THEN it replaces the disposable generated content and static directories, writes each reading page under `content/specs/<stagedPath>` without an appended machine inventory, and writes the sidebar projection
- AND every registered page, including Module entries, exposes level-2 sections and level-3 subsections in its page table of contents
- AND only after every asset and the sidebar succeed does it write the materialization identity record
- AND a failed write can leave partial derived assets that a fresh materialization replaces on retry

The reading source is published without metadata blocks or a duplicate Files section. The paired
metadata stays authoritative for identities and implementation mappings and contributes its own
source digest. A disclosure component shows identity, owner, inclusion provenance and both source
digests without changing reading membership or creating another canonical page.

### scenario.views.id-anchors — Publish readable definition titles with stable identity anchors

- GIVEN a loaded registry model whose documents define scenario/requirement headings and entity meaning anchors with paired metadata
- WHEN `materializeScoped` runs and the site is built
- THEN every scenario and requirement heading displays only its authored title, with its own ID retained as an explicit heading anchor, for example `### Title {#req.x}`
- AND table-of-contents labels and indexed heading text use that title without the definition ID prefix
- AND definitions with the same title retain distinct ID anchors, and changing a title does not change its ID anchor
- AND it preserves each entity's readable meaning anchor, including adjacent anchors on a single line for a coherent shared explanation
- AND a `path#id` link to that scenario, requirement or entity resolves on the published site
- AND source document bytes, obligation bodies, ordinary prose and fenced examples remain unchanged by the title transformation

This is the default registered-Spec publishing behavior, not a CSS visibility rule or a change to
Spec syntax or identity. It recognizes level-2 through level-5 definition headings with the
Protocol's spaced em dash, en dash or hyphen separator and preserves title Markdown and heading
level. Source definitions still carry their IDs for validation, test associations and agent context;
publication removes only the ID and separator from the displayed heading, not the stable link target.

### scenario.views.build-site — buildSite runs the full prepare/build/validate/promote path

- GIVEN installed Node/Docusaurus dependencies and a loaded registry model
- WHEN `buildSite` runs
- THEN it clears the candidate, prepares sources, runs Docusaurus, validates the built artifacts and only then promotes the candidate
- AND a spawn error, nonzero exit or failed validation rejects without promoting

### scenario.views.validate-candidate-mismatch — Validation rejects a stale or incomplete candidate

- GIVEN a build-manifest artifact whose schema version, source digest, page inventory or redirect stub coverage does not exactly match the current model, or a retained internal navigation link whose destination or requested anchor is absent from the candidate
- WHEN `validateScopedBuild` runs
- THEN it rejects without repairing the artifacts or promoting output

Digest format and path safety are Module-wide requirements; see
[req.views.hash-format](requirements.md#req.views.hash-format) and
[req.views.safe-relative-paths](requirements.md#req.views.safe-relative-paths). Promotion and loader
isolation are specified by [req.views.promote-atomic](requirements.md#req.views.promote-atomic),
[req.views.promote-requires-checked-candidate](requirements.md#req.views.promote-requires-checked-candidate)
and [req.views.no-contract-context-expansion](requirements.md#req.views.no-contract-context-expansion).
The absence of a standalone graph is specified by
[req.views.no-docsite-graph-view](requirements.md#req.views.no-docsite-graph-view).
