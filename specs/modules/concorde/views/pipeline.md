```concorde-document
{
  "id": "document.views.pipeline",
  "targets": [
    "module.views"
  ],
  "main_visible": true
}
```
# Publication pipeline

## interface.views.build

The public API is TypeScript and Docusaurus plugin hooks. Profile 9 publication reads an explicit
project registry, creates derived documentation, validates a built candidate, and promotes only a
successfully checked candidate. It exposes no agent tool or read proxy. Consumers do not need a
Python API or a provider Spec to invoke the functions and interpret the values defined here.

## Interface signatures

```typescript
// plugins/scoped-content/model.ts
isScoped(root: string): boolean;
loadScopedRegistry(root: string): ScopedRegistry;
safeRead(root: string, path: string): string;
rewriteLinks(registry: ScopedRegistry, page: Page): string;
hash(value: string | Buffer): string;
legacyAliasRoute(targetId: string, sourcePath: string): string;
// plugins/scoped-content/materialize.ts
primaryDocument(target: Target): string;
scopedSidebar(registry: ScopedRegistry, kind?: 'module' | 'implementation'): object[];
materializeScoped(registry: ScopedRegistry): Promise<void>;
// plugins/scoped-content/index.ts
validateScopedBuild(root: string, directory: string): Promise<void>;
scopedContent(context: LoadContext, options: unknown): Plugin<ScopedRegistry>; // default export
// scripts/prepare-publication.ts and scripts/build.ts
preparePublication(projectRoot: string, options?: {mode?: 'preview' | 'build'}): Promise<{registry: ScopedRegistry}>;
buildSite(): Promise<void>;
promoteCandidate(candidate: string, destination: string, backup: string): Promise<void>;
```

`root` is a project-root filesystem path. Relative member paths use POSIX spelling without absolute
paths, backslashes, empty/dot/traversal components or symlinks. `safeRead` requires a regular file
and returns UTF-8 text; invalid paths throw `Error`, and OS read errors retain their Node error code.
`hash` returns `sha256:` followed by 64 lowercase hexadecimal digits. `isScoped` returns false for
missing configuration or a non-9 profile, true for `profile_version === 9`, and propagates malformed
JSON/unsafe path/read errors. Consumers of this API select the Profile 9 branch with `isScoped`.
This public build contract accepts Profile 9 only. Legacy fixture readers remain separate diagnostic
utilities; their records and rendering paths are not another supported publication mode.

`loadScopedRegistry` reads `.concorde/config.json`, which must contain `profile_version: 9` and a
safe relative `registry` path. The registry is `{schema_version: 2, project_id: string, entry_target: string,
targets: Module[], implementations: ImplementationSpec[], checks: unknown[]}` with project metadata retained in its source bytes. Each
Target has all the fields below. Its IDs/focuses are unique, Module parents are acyclic,
entry target exists, uses names Modules and implementation references name Implementation Specs and local focus documents define their IDs.
Every document has exactly one `concorde-document` block
`{id: stable_id, targets: nonempty_unique_target_ids, main_visible: boolean}` matching its references.
Malformed identities, axes, memberships, diagram declarations or required/provided
contract agreement throw `Error`; the loader never follows a contract edge to import extra context.
A `concorde-contract` has id/version/role/peer/schema/semantics/example. Internal required contracts
must match the named provider's schema; peers named `external:...` do not require a local provider.

## Public model types

```typescript
type Kind = 'module' | 'implementation';
interface Focus { id: string; title: string; document: string }
interface Target {
  id: string; kind: Kind; title: string; documents: string[];
  parent: string | null; uses: string[];
  implementations: string[]; features: Focus[]; interfaces: Focus[]; checks: string[];
  diagrams: []; // inline sources are already in registered Markdown documents
}
interface Page {
  sourcePath: string; route: string; stagedPath: string; title: string; content: string;
  contentDigest: string; documentId: string; documentTargets: string[]; mainVisible: boolean;
  contextSection: 'target_spec' | 'shared_specs';
  memberships: {targetId: string; kind: Kind; primary: boolean}[];
  aliases: string[]; kind: Kind; primaryOf: string | null; inlineOverview: boolean;
}
interface Edge {
  source: string; target: string;
  kind: 'composes' | 'uses' | 'implemented_by' | 'requires';
  contract?: string;
}
interface ScopedRegistry {
  schema_version: 16; projectRoot: string; registryPath: string; entryTarget: string;
  sourceDigest: string; targets: Target[]; pages: Page[]; edges: Edge[];
}
```

Target/document order follows the registry. There is exactly one Page per distinct registered
physical document, in the order its sourcePath was first registered. Its canonical route is
`/specs/` followed by its sourcePath with a leading `specs/` segment removed — only when every
registered document's path starts with `specs/` — and its `.md` extension dropped; a project whose
documents are not all under `specs/` keeps full paths. Its staged path is that same (possibly
unstripped) relative path, `.md` extension kept. `loadScopedRegistry` throws when two documents
would map to the same canonical route, when a canonical route equals a legacy alias route, or when
a staged path falls under the reserved `projections/` prefix.
A shared physical document keeps its single document identity, identical byte digest and one Page,
carrying a `memberships` entry `{targetId, kind, primary}` per referencing target in registry order.
`kind` is the kind of the membership marked `primary`, else the first membership's kind; `primaryOf`
is that membership's targetId, or `null` when no membership is primary. `aliases` lists, for every
membership, the legacy route it previously published at: `/specs/<target-id>/<key>`, where `key` is
the first 16 hex digits of `hash(sourcePath)` after `sha256:` (`legacyAliasRoute` computes this).
The Markdown H1 supplies the page title, falling back to the primary membership's target title, or
the first membership's target title when none is primary. `content` excludes front matter;
`contentDigest` hashes the complete source bytes. Edges distinguish Module composition, uses, implementation reuse and required-interface relationships.

`sourceDigest` hashes JSON serialization of ordered `[path, contentDigest]` pairs: configuration,
registry and each distinct registered document in first-reference order. A shared physical document
contributes its bytes once; membership changes are represented by the registry input. The complete
Markdown digest includes every Mermaid fence and source declaration. Inline diagrams create no
additional source or route record. This is a byte/version identity, not a semantic-completeness claim.

## Independent Protocol documentation

When `docsite/site.json` sets optional boolean `protocolDocs` to true, publication adds a
**Spec Protocol** navbar tab before the software Spec tabs. A separate Docusaurus docs collection
reads Markdown from `protocol/` and publishes it under `/protocol/` with its own chapter sidebar
and local search index. The collection requires no project Spec metadata, Module/Feature identity
or registry membership. Its pages do not appear in the software architecture graph or registered
Spec manifest. Missing enabled content and broken chapter links fail the site build. Omitting the
option disables this collection; scaffolding a consumer project does not enable or copy it.

The adapter renders inline `mermaid` fences using Docusaurus's Mermaid theme in both Protocol and
registered Spec pages. Protocol illustrations remain part of their independent chapter sources;
software diagrams belong to their registered Markdown documents. Both retain accessible titles
and descriptions, and neither creates a separate external diagram source or delivery route.
This renderer choice does not change the Protocol's tool-neutral requirements.

## Materialization and required build collaborators

The primary Spec navigation mirrors the directory hierarchy of explicitly registered source paths;
it never discovers new membership by scanning directories. A secondary target view separates
`moduleSpecsSidebar` and `implementationSpecsSidebar`: Module categories follow registered parentage,
and Implementation Specs are listed independently. The navbar exposes Module Specs, Graph and,
when present, Implementation Specs; the optional independent Protocol tab precedes them.
Directory grouping, structural composition and implementation reuse remain distinct views.

A Module category links directly to its `module.md` through a Docusaurus category `link` of type
`doc`. Its child items contain only additional registered documents and child Modules, never a
second entry for `module.md`. A Module with no child items is a direct document link. The Module
page displays its complete authored content, including Architecture and other overview sections,
with section navigation. Mermaid diagrams render exactly where their fences occur in the authored
Markdown; the renderer does not inject or duplicate an overview before or after the article. Document titles and labels use the filename without `.md`, except Module
entry pages, which use the Module's title. Source provenance retains the exact source path.

Every registered document has one Docusaurus doc reference, either as an item or a category link.
Further appearances of explicitly shared Module documents use links to the same canonical page.
This preserves access through each owning Module without duplicate doc IDs. The generated sidebar
JSON contains both named sidebars; the packaged navbar and sidebar adapter consume that projection.
`primaryDocument` requires exactly one
registered module.md for Modules and returns the first member for other kinds; a Page's matching
`memberships` entry marks that choice with `primary: true`, and diagrams and the site entry use it
rather than arbitrary array order. `rewriteLinks` rewrites supported local Markdown links to the
registered page routes. Diagram references use the owning document's Architecture anchor; there
are no external diagram-source or delivered-HTML links. Invalid or unregistered local destinations
are rejected. Outside fenced code
blocks it handles inline links and images with these forms, whose URL has no whitespace or closing
parenthesis:

```markdown
[label](url)
![label](url)
```

A URL beginning with a scheme, `#`, or `/` is preserved unchanged. Other destinations
resolve relative to the source document directory using POSIX normalization; an optional `#anchor`
is preserved. The resolved path selects the single page registered at that sourcePath — there is
now exactly one — and an unregistered destination is rejected. Relative non-Spec assets
have no matching page and are rejected; callers use a supported absolute or root-relative asset URL.
Unsupported Markdown forms are left unchanged. Link validation occurs during rewrite/materialization,
not during registry loading. The function returns text without changing sources.

`materializeScoped` consumes a model returned by the loader. Its `projectRoot` owns all output paths.
It replaces `docsite/.generated/content/` and `docsite/.generated/static/`, writes each page under
`content/specs/<stagedPath>` with its Mermaid fences intact, and writes
`docsite/.generated/specs-sidebar.json`. The Markdown renderer generates diagram views during the
site build; materialization does not copy standalone diagram HTML. Markdown front matter specifies format, slug, title and
sidebar label. At entry it removes `docsite/.generated/scoped-materialization.json`; only after all
assets and the sidebar succeed does it write this identity record as
`{schema_version: 1, sourceDigest: registry.sourceDigest}`. The function does not edit registered
Spec sources or promote `docsite/build`.
A failed write/copy rejects the promise and can leave partial derived assets. Retry requires a
fresh model and re-materializes these disposable directories; callers must not publish partial assets.

The source-checkout check `python scripts/development/check-docsite-types.py` prepares the actual
both results of `scopedSidebar(loadScopedRegistry(projectRoot), kind)` as `docsite/.generated/specs-sidebar.json`, then
runs TypeScript with `--noEmit` against the docsite tsconfig. It installs the locked Node dependencies
when their identity marker is absent or stale. This check must work in a fresh delivery worktree
using only registered sources; deriving its imported sidebar does not publish pages or establish
publication readiness. Registry loading or TypeScript failure still fails the check.

For Profile 9, `preparePublication(projectRoot)` resolves the root, loads the model, materializes
Markdown and navigation, clears the selected Docusaurus generated directory, and returns `{registry}`.
It requires no separate diagram-renderer process. Docusaurus renders each Mermaid fence in the
page build. Invalid syntax or a failed diagram render rejects the candidate before promotion. `buildSite()` operates on the docsite
containing this module, with project root its parent. Installed Node/Docusaurus dependencies must
be present. The Docusaurus collaborator must build into the supplied candidate directory, load the
plugin, call its hooks, report rendered routes and exit zero. A spawn error or nonzero exit rejects
without promoting. The function does not accept an arbitrary root argument.

The default `scopedContent` plugin requires Docusaurus `LoadContext.siteDir` and `baseUrl`; options may
provide `{projectRoot?: string}`, defaulting to the site's parent. `loadContent` loads the current
model and requires a valid materialization identity with the same source digest before returning it.
Missing, malformed or mismatched identity rejects and requires fresh preparation. This detects
source changes between materialization and plugin loading even when the page routes stay the same.
`contentLoaded({content, actions})` calls `actions.setGlobalData` with Workspace 15 entry target,
page metadata without Markdown bodies and architecture nodes/edges. `getPathsToWatch()` returns
absolute configuration, registry and registered Markdown paths, which include the diagram sources. `postBuild({outDir, routesPaths})`
requires the fresh source digest and materialization identity to match the loaded model, and every expected page route to be in
the rendered route inventory after base-URL normalization. Otherwise it throws before emitting
verification artifacts. After the build manifest and architecture graph, it writes one legacy
redirect stub per alias at `<outDir>/<alias without its leading slash>.html`: a minimal HTML
document with a base-URL-prefixed `<meta http-equiv="refresh">` and `<link rel="canonical">` to the
document's canonical page, plus a visible link, mirroring the root redirect page. These are the
complete collaborator promises this Profile 9 path relies on.

## Build artifacts, validation and promotion

Successful plugin post-build writes these JSON artifacts in `outDir`:

```typescript
// build-manifest.json
{ schema_version: 16, sourceDigest: string,
  pages: {sourcePath: string; route: string; contentDigest: string; targets: string[]; aliases: string[]}[] }
// architecture-graph.json
{ schema_version: 1, sourceDigest: string, nodes: Target[], edges: Edge[] }
```

`validateScopedBuild(root, directory)` reloads the current model and reads both artifacts from the
candidate directory. It resolves with no value only when schema versions, source digests, ordered
page path/route/digest/targets/aliases entries and complete ordered graph nodes/edges match exactly,
and every alias has a redirect stub in the candidate directory whose content contains that page's
canonical route. Stale or incomplete manifest/graph, missing files, a missing or non-matching
redirect stub, or malformed JSON reject. This function does not repair artifacts or promote output.
Route coverage is measured by the plugin's post-build hook; callers must not manufacture a manifest
to bypass that hook.

`buildSite` owns `docsite/.generated/candidate`, `docsite/build` and
`docsite/.generated/previous-build`. It clears the candidate, prepares sources, runs Docusaurus,
validates the built artifacts and only then calls `promoteCandidate`. Validation failure removes
the candidate and preserves the previous build. Observed source changes during post-build or fresh
validation reject; the identity describes the inputs actually checked and must be checked again
if sources change before a later independent use of the candidate.
Preparation/build callers must exclusively own these derived output directories through promotion;
concurrent materialization or manual edits to staged/candidate artifacts are unsupported. The
identity is a host build record, not a signature authenticating arbitrary externally supplied HTML.

`promoteCandidate` is a filesystem transaction helper, with caller-supplied distinct candidate,
destination and backup paths on a rename-compatible filesystem. Its caller must have successfully
validated the exact candidate. It clears the disposable backup, moves an existing destination to
backup, moves the candidate to destination, and removes the backup on success. A failed move/removal
attempts to restore the prior destination and rejects; filesystem failure during rollback can still
require operator recovery. The helper itself does not validate Spec contents and must not be called
on unchecked or stale output.

```typescript
if (!isScoped(projectRoot)) throw new Error('This consumer requires Profile 9');
const registry = loadScopedRegistry(projectRoot);
await materializeScoped(registry); // inspect derived assets; not yet a published build
await buildSite();                // integrated prepare/build/validate/promotion path
```

Repeated loading of unchanged inputs preserves identities. Repeated successful builds replace
derived output. No returned model, manifest or successful deterministic check proves that the Spec
supports every possible future task; independent Spec review and actual task gaps remain separate.

## Module main-document and overview validation

Profile 9 publication requires one local module.md for every Module. The complete Module collection
must describe Architecture outside code fences and provide usage interfaces for its declared
features. main_visible is presentation metadata and does not trim a Module's context. Architecture
diagrams are required in each Concorde Module's reading entry by this project's convention; the
Protocol itself remains tool-neutral. Inline source declarations and accessible Mermaid titles
must agree with the local written model. A declared diagram does not establish semantic completeness.
Implementation Specs have separate identities, explicit files and unique file ownership. Module
composition, dependency declarations and implementation references are checked independently.
These checks establish structure, not universal semantic completeness.

Diagram rendering belongs to the normal Markdown/site candidate transaction. It writes no
`generated/diagrams/` tree and cannot change Framework outputs under generated/protocol,
generated/agents or generated/docs. The site uses its locked Mermaid dependency, with no separately
installed renderer Skill, generated-source JSON or independent diagram receipt.

The main page preserves the authored title, introduction and Architecture section order. The
`inlineOverview` presentation flag indicates a main-page inline overview; it grants no membership
or separate rendering authority. Module main pages use the full reading column.
The renderer presents concorde-document identity, references and visibility in a Spec metadata
disclosure instead of a leading JSON code block, without changing the authored source or digest.

Production builds use docsite/.generated/docusaurus-production for Docusaurus-generated modules
and aliases. preparePublication mode build clears only that generated directory; the build process
sets DOCUSAURUS_GENERATED_FILES_DIR_NAME to the same relative path. Default preview mode uses
.docusaurus. A production build preserves an active preview's generated modules and cache, so
development-only debug routes cannot overwrite the production module graph.

## Mermaid rendering and source compatibility

The Markdown renderer consumes the literal body of each `mermaid` fence, supports the project's
flowchart, entity-relationship and state-diagram syntax, and produces an accessible diagram within
the containing page. `accTitle` and `accDescr` remain available to assistive technology. A diagram
must fit the reading column or allow inspection without hiding content. Renderer directives may
not fetch external source files or execute arbitrary page script. Render failures identify the
owning source document and prevent publication of a candidate that silently drops a diagram.

Source edits use ordinary document versioning: changing an edge, label, title or description changes
the containing document digest and invalidates source-dependent build evidence. A shared Markdown
member still publishes once and retains all registered memberships. Dependency links and diagram
nodes do not add target contexts or graph edges to the explicit registry-derived relationship view.

The `diagrams` registry property remains present as an empty array for this representation. Old
external-source declarations are rejected with a migration diagnostic before preparation rather
than ignored. Migration moves their meaningful model into registered Markdown, removes the external
records and updates links to the owning document's Architecture section. Standalone legacy diagram
HTML URLs have no preservation promise in this revision; canonical Spec page and legacy document
alias redirects retain the compatibility contract above. Rendering support still requires ordinary
site dependencies to be installed; initialization does not fetch them.
