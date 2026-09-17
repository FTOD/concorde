# Views scenarios

These precise specifications belong directly to the [Views Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Implementation Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
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
| [Entity](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Requirement](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Scenario](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Capability](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Snapshot](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

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
- BUT publication does not invoke, replace or remove the separate UA exporter or official viewer

Removing this feature includes its dedicated implementation, resources and dependencies. A shared
resource or dependency remains when another retained publication function needs it; in particular,
inline Mermaid rendering remains supported. The docsite provides no substitute embedded UA view or
redirect from the removed graph page. UA continues through its existing independent commands.

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
docs rather than adding them to Module Specs. The scaffold excludes `custom-docs/`, the existing
checkout-only `concorde-only/` assets, and project-owned site identity bytes.

`homepage.links` optionally supplies an array of `{label, to}` values: nonempty labels and either
local absolute routes or HTTP(S) URLs. Local links honor the site's base URL. No Protocol or Flow
link is built into the homepage renderer.

### scenario.views.protocol-docs-tab — Concorde publishes its standard through custom docs

- GIVEN Concorde's project-owned configuration selects `protocol/` as a custom docs collection and registers the Agent Flows extension
- WHEN the site builds
- THEN Spec Protocol remains at `/protocol` with its chapter sidebar and search index and Agent Flows remains at `/agent-flows`
- AND both retain independent tabs without Spec provenance wrappers or registry membership
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

### scenario.views.agent-flows — Inspect actual Agent and LangGraph execution

- GIVEN Concorde's source checkout with the development Python environment and its own docsite extension
- WHEN the site is built and the reader opens the top-level Agent Flows tab at `/agent-flows`
- THEN the page shows compiled Spec preparation, development, discovery/query, topology, planning, coordination, Issue solving and Agent invocation node Flows plus expanded public Studio entries without executing Agents
- AND specify-loop has a directly navigable section showing its actual authoring, review, resume and result transitions, linked from its dev-loop node
- AND a searchable sidebar lists every Capability and shared Flow family, with a selected detail view and stable fragment links supporting direct access and browser navigation
- AND the sidebar includes both dev-loop and the specify Capability, keeps the current selection visible, and can be opened or closed on small screens
- AND the build invokes the same development topology factory as runtime, with new-change, skipped-authoring, resume and no-code variants
- AND step responsibilities, Agent calls, key inputs and outputs, stop conditions and bounded code-review repair are explained with valid links to their Spec sections
- AND execution diagrams come from the same LangGraph factories as runtime, with runtime-bound Flow instances distinguished from public entries
- AND source byte digests identify the inspected implementation inputs
- AND light/dark themes, keyboard-focusable scroll regions, node-detail links, width controls and a textual transition list support long graphs and small screens
- AND graph export or broken internal links fail the production build before promotion
- AND the packaged consumer template excludes `docsite/concorde-only/`, exposes no Agent Flows tab or route, and requires no Python graph data

This extension is private to the Concorde source checkout, not a Flow catalog protocol or a new
Spec context input. `docsite/concorde-only/flows.py` inspects compiled factories; the plugin stages
the result through Docusaurus `createData` and registers its own route. Use the checkout's `.venv`
or set `CONCORDE_PYTHON` to the development interpreter when building a source copy. The ordinary
publication registry and consumer build contract remain independent of this extension.

### scenario.views.load-registry — Loading the registry validates identities and memberships

- GIVEN `.concorde/config.json` with `profile_version: 14` and a safe relative registry path
- WHEN `loadScopedRegistry` runs
- THEN it returns a model whose Module IDs are unique, whose Module parents are acyclic and whose entry target exists and is a Module
- AND malformed identities, ownership, references or contract bindings throw before any file is written
- AND it returns no graph-specific node or edge projection

### scenario.views.materialize — Materializing writes disposable staged content and its identity record

- GIVEN a loaded registry model
- WHEN `materializeScoped` runs
- THEN it replaces the disposable generated content and static directories, writes each reading page under `content/specs/<stagedPath>` without an appended machine inventory, and writes the sidebar projection
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

## Understand Anything viewer service

### scenario.views.viewer-launch — Launching opens the first existing raw graph with the official viewer

- GIVEN an installed Framework manifest, a verified runtime marker and at least one existing raw graph in the manifest's ordered graph_paths
- WHEN `run-ua-graph-viewer.py --project-root PATH` runs
- THEN it selects the first existing graph, validates its shape and starts the official viewer with the requested port and browser behavior
- AND it returns the child process's exit code

The launcher selects the first existing raw graph in the manifest's ordered `graph_paths` list:
`.understand-anything/knowledge-graph.json`, then `.ua/knowledge-graph.json` in the current package.
The graph must be a regular JSON object with a string version, object project, and arrays nodes and
edges. Symlinks in the graph path are rejected.

### scenario.views.viewer-invalid-first-graph — An invalid first-choice graph fails without falling back

- GIVEN the first existing graph in order is not a regular JSON object with a string version, object project and array nodes/edges, or is reached through a symlink
- WHEN the launcher runs
- THEN it fails immediately
- AND it does not fall back to a later graph in the order

### scenario.views.viewer-missing-runtime — A missing or mismatched runtime blocks launch

- GIVEN a missing, unverified or mismatched runtime marker, viewer package identity or entrypoint file
- WHEN the launcher runs
- THEN it reports `CONCORDE VIEWER FAILED` on stderr and exits 3
- AND it does so before starting any process

### scenario.views.viewer-interrupted — Keyboard interruption is reported distinctly

- GIVEN a running viewer child process
- WHEN the launch is interrupted from the keyboard
- THEN the launcher returns exit code 130

These launcher boundaries are Module-wide requirements, not outcomes of this one scenario; see
[req.views.no-graph-generation](requirements.md#req.views.no-graph-generation),
[req.views.no-dependency-install](requirements.md#req.views.no-dependency-install) and
[req.views.cli-syntax-errors](requirements.md#req.views.cli-syntax-errors) in `requirements.md`.

After admission, the launcher checks Node.js >=18 and runs Node with the installed entrypoint and
project directory, forwarding the optional flags. The child runs from the project directory. The
launcher prints which graph it selected and returns the child exit code.

## UA graph exporter

### scenario.views.ua-graph-skeleton — Exporting derives a skeleton graph when none exists

- GIVEN a project with an explicit Spec registry and no existing raw UA graph at either manifest
  path
- WHEN `ua-graph` runs
- THEN it writes `.ua/knowledge-graph.json` with one node per registered Module, `contains` edges
  for composition, `depends_on` edges for `uses`, `documents` edges to sole document owners, explicit `references` edges without recursive expansion, and
  `contains` edges from each Module to the files its entities bind
- AND it writes one layer per Module whose registry `files` are nonempty, whose members are the
  files for which that Module is the first registered lister together with the documents that
  Module solely owns, and no `layer:unlisted`

### scenario.views.ua-graph-overlay — Re-exporting overlays and replaces only Concorde's own elements

- GIVEN an existing raw UA graph, produced by the real Understand Anything tool or by a prior export
- WHEN `ua-graph` runs
- THEN it removes only the nodes tagged `concorde-ua-graph`, the layers named `layer:module.*` or
  `layer:unlisted`, the `layer:<id>` belonging to each removed Module node (including Module IDs
  without a `module.` prefix), and the edges whose source or target is one of those removed node IDs or a
  `module:<id>` ID for a currently registered Module, then adds a freshly derived set of those same
  kinds of elements
- AND every other node, edge, layer, and the graph's `project`, `version`, `tour` and extension
  fields retain their JSON values; whitespace and array ordering may be normalized
- AND a foreign node whose own ID happens to start with `module:` (for example a real scan's own
  "module" node kind) is left untouched when that ID is neither a removed node ID nor a currently
  registered Module ID; edges naming it are preserved only when neither endpoint is in the
  declared ownership scope, so an edge to a currently registered Module node is replaced
- AND a Module's bound file reuses an existing node's ID when the UA graph already has a
  file-like node at that `filePath`, instead of creating a duplicate
- AND a Module's registered document likewise reuses an existing document-like node's ID at that
  `filePath` instead of creating a duplicate, and joins the layer of its sole owner
  when that Module has nonempty registry `files`; otherwise it remains outside generated
  layers, in both fresh export and overlay, and never joins `layer:unlisted`
- AND running the export again against its own prior output produces byte-identical output

### scenario.views.ua-graph-shared-file — A shared file gets one layer and a related edge to the rest

- GIVEN one implementation file that several Modules' entities list
- WHEN `ua-graph` runs
- THEN every listing Module still gets its own `contains` edge to that file's node, from its own
  entity
- AND the file's node joins only the layer of the Module registered first for that file
- AND every other listing Module gets one additional `related` edge from that file's node naming
  it as also listed by that Module

### scenario.views.ua-graph-check — `--check` reports drift from the current registry without writing

- GIVEN a previously exported or overlaid graph and a registry that has since changed
- WHEN `ua-graph --check` runs
- THEN it recomputes the same derivation and compares it to the file on disk
- AND a match returns success and a difference returns an `invalid` finding, in both cases without
  writing

### scenario.views.ua-graph-invalid-input — A malformed existing graph is rejected without writing

- GIVEN an existing file at the target path that is not a JSON object, is reached through a
  symlink, is a directory, lacks a string `version`, an object `project`, or array `nodes` and
  `edges`, contains malformed node, edge or layer records or duplicate node or layer IDs, or
  has a foreign node or layer ID that collides with an exported node or layer ID
- WHEN `ua-graph` runs, with or without `--check`
- THEN it fails with an error naming the existing file
- AND it does not write any change to that file

These exporter boundaries are Module-wide requirements; see
[req.views.ua-graph-registry-only](requirements.md#req.views.ua-graph-registry-only) and
[req.views.ua-graph-idempotent](requirements.md#req.views.ua-graph-idempotent) in `requirements.md`.

Context references are distinct graph edges and never acquire contains/depends_on meaning. A
referenced document stays in its owner's layer; neither its implementation files nor its owner's
references are imported. The exporter uses the schema-5 registry and keeps ownership, references and implementation listings separate. Existing external overlay
admission remains contract version 1: the new edge type fits its open string type vocabulary.
