```concorde-document
{
  "id": "document.views.pipeline",
  "owner": "module.views",
  "main_visible": true
}
```
# Publication pipeline

The public API is TypeScript and Docusaurus plugin hooks. Profile 12 publication reads an explicit
project registry, creates derived documentation, validates a built candidate, and promotes only a
successfully checked candidate. It exposes no agent tool or read proxy. Consumers do not need a
Python API or a provider Spec to invoke the functions and interpret the values defined here.
Publication has no Module/Scenario graph view or architecture-graph output. Its registry validation and
Module navigation still use declared relationships; inline authored Mermaid diagrams remain part
of ordinary document rendering.

## Concorde-only Agent execution publication

### scenario.views.agent-flows — Inspect actual Agent and LangGraph execution

- GIVEN Concorde's source checkout with the development Python environment and its own docsite extension
- WHEN the site is built and the reader opens the top-level Agent Flows tab at `/agent-flows`
- THEN the page shows compiled development, discovery/query, topology, planning, coordination, reflection and recursive Agent Flows plus expanded public Studio entries without executing Agents
- AND the build invokes the same development topology factory as runtime, with new-change, skipped-authoring, resume and no-code variants
- AND stage responsibilities, Agent calls, key inputs and outputs, stop conditions and bounded code-review repair are explained with valid links to their Spec sections
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

## Loading, materializing and building

### scenario.views.load-registry — Loading the registry validates identities and memberships

- GIVEN `.concorde/config.json` with `profile_version: 12` and a safe relative registry path
- WHEN `loadScopedRegistry` runs
- THEN it returns a model whose Module IDs are unique, whose Module parents are acyclic and whose entry target exists and is a Module
- AND malformed identities, ownership, references or contract bindings throw before any file is written
- AND it returns no graph-specific node or edge projection

### scenario.views.materialize — Materializing writes disposable staged content and its identity record

- GIVEN a loaded registry model
- WHEN `materializeScoped` runs
- THEN it replaces the disposable generated content and static directories, writes each page under `content/specs/<stagedPath>` with a `## Files` section listing that page's owning Module's exact registered files when it is a Module's primary page, and writes the sidebar projection
- AND only after every asset and the sidebar succeed does it write the materialization identity record
- AND a failed write can leave partial derived assets that a fresh materialization replaces on retry

The appended `## Files` section is a reading convenience only; the complete file inventory remains
the registered `concorde-entities` blocks in the Module's own Spec. The leading `concorde-document`
block is stripped from rendered content; a Spec metadata disclosure component presents that
identity, its references and its visibility instead, without changing the authored source or its
digest.

### scenario.views.id-anchors — Materializing injects scenario, requirement and entity anchors

- GIVEN a loaded registry model whose documents define scenario and requirement headings and `concorde-entities` blocks
- WHEN `materializeScoped` runs
- THEN it emits every scenario and requirement heading with its own ID as an explicit heading anchor, for example `### req.x — Title {#req.x}`
- AND it inserts an HTML anchor `<a id="entity.x"></a>` immediately before every entity's `concorde-entities` block
- AND a `path#id` link to that scenario, requirement or entity resolves on the published site

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
[req.views.hash-format](module.md#req.views.hash-format) and
[req.views.safe-relative-paths](module.md#req.views.safe-relative-paths). Promotion and loader
isolation are specified by [req.views.promote-atomic](module.md#req.views.promote-atomic),
[req.views.promote-requires-checked-candidate](module.md#req.views.promote-requires-checked-candidate)
and [req.views.no-contract-context-expansion](module.md#req.views.no-contract-context-expansion).
The absence of a standalone graph is specified by
[req.views.no-docsite-graph-view](module.md#req.views.no-docsite-graph-view).

## Interface signatures

```typescript
// plugins/scoped-content/model.ts
requireScoped(root: string): void;
loadScopedRegistry(root: string): ScopedRegistry;
safeRead(root: string, path: string): string;
rewriteLinks(registry: ScopedRegistry, page: Page): string;
hash(value: string | Buffer): string;
legacyAliasRoute(targetId: string, sourcePath: string): string;
primaryDocument(target: Target): string;
// plugins/scoped-content/materialize.ts
scopedSidebar(registry: ScopedRegistry): object[];
materializeScoped(registry: ScopedRegistry): Promise<void>;
// plugins/scoped-content/index.ts
validateScopedBuild(root: string, directory: string): Promise<void>;
scopedContent(context: LoadContext, options: unknown): Plugin<ScopedRegistry>; // default export
// scripts/prepare-publication.ts and scripts/build.ts
preparePublication(projectRoot: string, options?: {mode?: 'preview' | 'build'}): Promise<{registry: ScopedRegistry}>;
buildSite(): Promise<void>;
promoteCandidate(candidate: string, destination: string, backup: string): Promise<void>;
```

`root` is a project-root filesystem path. `safeRead` requires a regular file and returns UTF-8
text; invalid paths throw `Error`, and OS read errors retain their Node error code. `hash` returns
`sha256:` followed by 64 lowercase hexadecimal digits. `requireScoped` returns normally only for
`profile_version === 12`; a missing configuration, a different profile, and a malformed JSON,
unsafe path or read error each throw an `Error` naming the reason. Every entry point of this public
build contract calls it first: publication accepts Profile 12 projects only, and no other profile
has a compatibility rendering path.

`loadScopedRegistry` reads `.concorde/config.json`, which must contain `profile_version: 12` and a
safe relative `registry` path. The registry is
`{schema_version: 4, project_id: string, entry_target: string, targets: Module[], checks: unknown[]}`
with project metadata retained in its source bytes. Each Target has all the fields below. Its IDs
are unique, Module parents are acyclic, the entry target exists and is a Module, and `uses` names
Modules. Each Module has explicit `references` with typed Module/document identities. Every
document has one `concorde-document` block `{id, owner, main_visible}` matching sole ownership in
`documents`. Malformed identities, ownership, references, diagrams or contract bindings throw
`Error` before writes. Canonical contracts contain id/version/schema/semantics/example; separate
bindings select them with local role/peer/conditions/guarantees/obligations. Included definitions
retain their owner and only the explicit one-level resolution supplies validation context.
The loader never follows links or interface bindings as context edges. Removing graph presentation
does not remove ownership, reference or agreement validation responsibilities.

## Public model types

```typescript
type Kind = 'module';
interface Target {
  id: string; kind: Kind; title: string; documents: string[];
  references: {kind: "module" | "document"; id: string}[];
  parent: string | null; uses: string[]; files: string[]; checks: string[];
}
interface Page {
  sourcePath: string; route: string; stagedPath: string; title: string; content: string;
  contentDigest: string; documentId: string; owner: string; mainVisible: boolean;
  includedBy: {targetId: string; reasons: {kind: 'owned' | 'module' | 'document'; id: string}[]}[];
  aliases: string[]; kind: Kind; primaryOf: string | null;
}
interface ScopedRegistry {
  schema_version: 19; projectRoot: string; registryPath: string; entryTarget: string;
  sourceDigest: string; targets: Target[]; pages: Page[];
}
```

Publication model schema 19 replaces shared membership fields with sole owner and explicit inclusion
provenance. It retains the absence of the former graph `edges` projection and `Edge` type.
`Target.parent` and `Target.uses` remain registry metadata for navigation, provenance and validation.
This change does not change registry schema 4, Profile 12 or any UA graph format.

A file may be listed by several Modules, unlike a document: schema 4 has no single implementation
owner, so a shared file's reverse lookup is a plain list of listing Modules rather than one
authoritative binding. Target/document order follows the registry. There is exactly one Page per
distinct registered physical document, in the order its sourcePath was first registered. Its
canonical route is `/specs/` followed by its sourcePath with a leading `specs/` segment removed —
only when every registered document's path starts with `specs/` — and its `.md` extension dropped;
a project whose documents are not all under `specs/` keeps full paths. Its staged path is that same
(possibly unstripped) relative path, `.md` extension kept. `loadScopedRegistry` throws when two
documents would map to the same canonical route, when a canonical route equals a legacy alias
route, or when a staged path falls under the reserved `projections/` prefix.

A referenced physical document retains one Page and one sole `owner`. `includedBy` records every
Module whose one-level context includes it, in registry order, with all sorted inclusion reasons.
`kind` is `module`; `primaryOf` is the owner only when this page is its unique module.md, otherwise
null. `aliases` lists the legacy-format route for the current owner only:
`/specs/<owner-id>/<key>`, where `key` is the first 16 hex digits of `hash(sourcePath)` after
`sha256:`. References contribute no ownership alias. Removed owners contribute no alias and no
historical aliases are inferred. Retained links to a removed alias must be corrected or fail the
candidate, as specified in [current document references](publication.md#scenario.views.publish-legacy-redirect).
The Markdown H1 supplies the title, falling back to the owner's title. `content` excludes front
matter; `contentDigest` hashes complete source bytes. Body Markdown links remain links and never
transclude another file. Ownership and inclusion provenance may be displayed beside the page.

`sourceDigest` hashes JSON serialization of ordered `[path, contentDigest]` pairs: configuration,
registry and each distinct registered document in first-reference order. A shared physical document
contributes its bytes once; ownership and reference changes are represented by the registry input. The complete
Markdown digest includes every Mermaid fence and source declaration. Inline diagrams create no
additional source or route record. This is a byte/version identity, not a semantic-completeness
claim.

## Project introduction

Site identity schema 1 optionally carries the `homepage` presentation object described in
[publication](publication.md#scenario.views.publish-homepage). The content plugin passes the
validated identity to the root renderer and watches `docsite/site.json` for changes. When the
option is absent, the root preserves its redirect to the registered entry Module. The introduction
is a human navigation surface outside registered Spec membership and `sourceDigest`; the
registered-page manifest retains its registry-derived meaning.

## Independent Protocol documentation

When `docsite/site.json` sets optional boolean `protocolDocs` to true, publication adds a
**Spec Protocol** navbar tab before the software Spec tabs. A separate Docusaurus docs collection
reads Markdown from `protocol/` and publishes it under `/protocol/` with its own chapter sidebar
and local search index. The collection requires no project Spec metadata, Module identity or
registry membership. Its pages do not appear in the registered Spec manifest. Missing enabled
content and broken chapter links fail the site build. Omitting the option disables this collection;
scaffolding a consumer project does not enable or copy it.

The adapter renders inline `mermaid` fences using Docusaurus's Mermaid theme in both Protocol and
registered Spec pages. Protocol illustrations remain part of their independent chapter sources;
software diagrams belong to their registered Markdown documents. Both retain accessible titles and
descriptions, and neither creates a separate external diagram source or delivery route. This
renderer choice does not change the Protocol's tool-neutral requirements.

## Materialization and required build collaborators

The materialization identity is the UTF-8 JSON file
`docsite/.generated/scoped-materialization.json`, relative to the project root, containing
`{schema_version: 1, sourceDigest: string}`. Its version 1 is independent of `ScopedRegistry`
schema 19. Materialization writes compact JSON followed by a newline, after the assets and
sidebar succeed as specified in [materialization](#scenario.views.materialize). `sourceDigest`
is the loaded registry's source digest, with the digest format defined above; the record adds no
page inventory or projection-content identity.

`postBuild` parses this record and requires `schema_version` to equal 1 and `sourceDigest` to
equal the loaded registry's `sourceDigest`, alongside the fresh-source and route checks below.
Read failures, JSON parse failures and version or digest mismatches reject post-build before
verification artifacts are emitted; the normal build failure rules preserve the previously
promoted site. This retains the existing identity format and comparisons.

The primary Spec navigation mirrors the directory hierarchy of explicitly registered source paths;
it never discovers new membership by scanning directories. `scopedSidebar` returns one tree
following registered Module parentage; there is no separate Implementation Spec sidebar, because
Profile 12 registers only Modules. The navbar exposes Module Specs and, when present, the optional
independent Protocol tab and a self-hosting-only Projections group of rendered
`generated/docs/instructions.json` and `generated/docs/wire.json` pages. An ordinary consumer
project produces neither file, so those pages are omitted rather than linking to unmaterialized
content. The Agent instructions projection displays common responsibilities and separate mode
sections with each mode's context/result/authority contract and complete common-plus-selected-mode
text; browsing these pages does not combine modes into a runtime prompt or grant agent context.
There is no Graph navbar item, graph route, graph component or graph-specific global data.

A Module category links directly to its `module.md` through a Docusaurus category `link` of type
`doc`. Its child items contain only additional registered documents and child Modules, never a
second entry for `module.md`. A Module with no child items is a direct document link. The Module
page displays its complete authored content, including Ontology and other overview sections,
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
collaborator promises this Profile 12 path relies on.

## Build artifacts, validation and promotion

Successful plugin post-build writes this JSON verification artifact in `outDir`:

```typescript
// build-manifest.json
{ schema_version: 19, sourceDigest: string,
  pages: {sourcePath: string; route: string; contentDigest: string; owner: string; includedBy: Page["includedBy"]; aliases: string[]}[] }
```

Build-manifest schema 19 identifies the publication contract without an architecture-graph
artifact. Older manifests require a fresh build. Publication neither produces nor requires
`architecture-graph.json`; it has no replacement graph artifact. UA export remains independent.

`validateScopedBuild(root, directory)` reloads the current model and reads the manifest from the
candidate directory. It resolves with no value only when its schema version, source digest and
ordered page path/route/digest/owner/includedBy/aliases entries match exactly, and every alias has a redirect
stub in the candidate directory whose content contains that page's canonical route. A stale or
incomplete manifest, missing manifest, missing or non-matching redirect stub, or malformed JSON
rejects. It also validates internal navigation links in the completed candidate after redirect
stubs exist. Every link emitted by the site's published documents must resolve to a candidate page
or other existing site-owned destination; a nonempty fragment targeting a page must identify an
anchor present on the resolved page. Current aliases resolve to their canonical pages for this
check, including fragment validation. This covers same-page fragments, root-relative links and
links produced by Markdown forms that `rewriteLinks` leaves unchanged, as well as rewritten
source-path links. It includes enabled reading collections without adding them to Spec membership
or the registered-page manifest.

Resolve navigation URLs against the referring page and the configured site URL/base URL. A
destination is internal when it has the configured site's origin and its path is within the
configured base URL; same-site absolute URLs within that base URL are internal too. Query strings
do not change the destination page or anchor lookup; preserve them in navigation. Other origins,
same-origin destinations outside the base URL and non-navigation schemes retain their existing
external handling without network availability checks. A missing destination, missing
requested anchor or unresolved redirect rejects with the referring page and destination identified.
Validation never silently removes a reference, infers document ownership and references, repairs source text or
retains historical output to make the check pass.

This function does not repair artifacts or promote output. Route coverage is measured by the
plugin's post-build hook; callers must not manufacture a manifest to bypass that hook.

`buildSite` owns `docsite/.generated/candidate`, `docsite/build` and
`docsite/.generated/previous-build`. It clears the candidate, prepares sources, runs Docusaurus,
validates the built artifacts and only then calls `promoteCandidate`. Validation failure removes
the candidate and preserves the previous build. Successful promotion replaces the previous build
as a directory, so a previously published graph page or dedicated graph artifact cannot survive
by being copied forward. Observed source changes during post-build or fresh validation reject;
the identity describes the inputs actually checked and must be checked again if sources change
before a later independent use of the candidate. Preparation/build callers must exclusively own
these derived output directories through promotion; concurrent materialization or manual edits to
staged/candidate artifacts are unsupported. The identity is a host build record, not a signature
authenticating arbitrary externally supplied HTML.

`promoteCandidate` is a filesystem transaction helper, with caller-supplied distinct candidate,
destination and backup paths on a rename-compatible filesystem. Its caller must have successfully
validated the exact candidate. It clears the disposable backup, moves an existing destination to
backup, moves the candidate to destination, and removes the backup on success. A failed
move/removal attempts to restore the prior destination and rejects; filesystem failure during
rollback can still require operator recovery. The helper itself does not validate Spec contents and
must not be called on unchecked or stale output.

```typescript
requireScoped(projectRoot);       // throws unless the project declares profile_version 12
const registry = loadScopedRegistry(projectRoot);
await materializeScoped(registry); // stage derived assets; not yet a published build
await buildSite();                // integrated prepare/build/validate/promotion path
```

Repeated loading of unchanged inputs preserves identities. Repeated successful builds replace
derived output. No returned model, manifest or successful deterministic check proves that the Spec
supports every possible future task; independent Spec review and actual task gaps remain separate.

## Module main-document validation

Profile 12 publication requires one local `module.md` for every Module, and requires its Purpose,
Requirements, Scenarios and Ontology headings to appear, by exact text and outside code fences, in
that order, with Ontology's Entities and Relationships subsections each present in that order;
other headings may interleave. `main_visible` is presentation metadata and does not trim a
Module's context. Module composition, dependency declarations and required-interface contracts
remain independently checked against the registry without producing a graph projection. These
checks establish structure, not universal semantic completeness.

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

## Mermaid rendering and source compatibility

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

## Protocol 5 publication migration status

The TypeScript loader admits Profile 12/schema 4 and publishes schema 19 with unique owner and
includedBy provenance. It validates one-level references and canonical definition/binding agreement,
exposes canonical definition anchors and renders links without transclusion. Manifest identity and
watched registry/source inputs invalidate publication when ownership or references change.
