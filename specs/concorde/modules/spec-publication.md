```concorde-document
{
  "id": "document.module.spec-publication",
  "targets": ["module.spec-publication"],
  "main_visible": false
}
```

# Spec publication

## api.publication.build

The public API is TypeScript and Docusaurus plugin hooks. Profile 8 publication reads an explicit
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
// plugins/scoped-content/materialize.ts
primaryDocument(target: Target): string;
scopedSidebar(registry: ScopedRegistry): object[];
materializeScoped(registry: ScopedRegistry): Promise<void>;
// plugins/scoped-content/index.ts
validateScopedBuild(root: string, directory: string): Promise<void>;
scopedContent(context: LoadContext, options: unknown): Plugin<ScopedRegistry>; // default export
// scripts/prepare-publication.ts and scripts/build.ts
preparePublication(projectRoot: string, options?: {mode?: 'preview' | 'build'}): Promise<PreparedPublication | {registry: ScopedRegistry}>;
buildSite(): Promise<void>;
promoteCandidate(candidate: string, destination: string, backup: string): Promise<void>;
```

`root` is a project-root filesystem path. Relative member paths use POSIX spelling without absolute
paths, backslashes, empty/dot/traversal components or symlinks. `safeRead` requires a regular file
and returns UTF-8 text; invalid paths throw `Error`, and OS read errors retain their Node error code.
`hash` returns `sha256:` followed by 64 lowercase hexadecimal digits. `isScoped` returns false for
missing configuration or a non-8 profile, true for `profile_version === 8`, and propagates malformed
JSON/unsafe path/read errors. Consumers of this API select the Profile 8 branch with `isScoped`.
Legacy `PreparedPublication = {registry: ContentRegistry, diagrams: DiagramDeliverySet}` is the
separate deterministic pre-Profile-8 path; those legacy values are not returned for Profile 8 roots.

`loadScopedRegistry` reads `.concorde/config.json`, which must contain `profile_version: 8` and a
safe relative `registry` path. The registry is `{schema_version: 1, entry_target: string,
targets: Target[], checks: unknown[]}` with project metadata retained in its source bytes. Each
Target has all the fields below. Its IDs/focuses are unique, parent axes are acyclic and kind-correct,
entry target exists, participation names Domains and local focus documents define their IDs.
Every document has exactly one `concorde-document` block
`{id: stable_id, targets: nonempty_unique_target_ids, main_visible: boolean}` matching its references.
Malformed identities, axes, memberships, diagram declarations or required/provided
contract agreement throw `Error`; the loader never follows a contract edge to import extra context.
A `concorde-contract` has id/version/role/peer/schema/semantics/example. Internal required contracts
must match the named provider's schema; peers named `external:...` do not require a local provider.

## Public model types

```typescript
type Kind = 'domain' | 'service' | 'module';
interface Focus { id: string; title: string; document: string }
interface Target {
  id: string; kind: Kind; title: string; documents: string[];
  scope_parent: string | null; component_parent: string | null; participates_in: string[];
  implementation: string[]; features: Focus[]; apis: Focus[]; checks: string[];
  diagrams: {source: string; kind: string; title: string; recipe?: 'system-overview'}[];
}
interface Page {
  targetId: string; kind: Kind; title: string; sourcePath: string; contentDigest: string;
  route: string; stagedPath: string; content: string; documentId: string;
  documentTargets: string[]; mainVisible: boolean;
  contextSection: 'target_spec' | 'shared_specs'; primary: boolean; inlineOverview: boolean;
  architectureDiagrams?: {
    kind: string; title: string; source: string; sourceSha256: string; route: string;
  }[];
}
interface Edge {
  source: string; target: string;
  kind: 'scope_contains' | 'composes' | 'participates_in' | 'requires';
  contract?: string;
}
interface ScopedRegistry {
  schema_version: 14; projectRoot: string; registryPath: string; entryTarget: string;
  sourceDigest: string; targets: Target[]; pages: Page[]; edges: Edge[];
}
```

Target/document order follows the registry. For each target/document reference there is one Page.
A shared physical document keeps its single document identity and identical byte digest, while
receiving a route in each referencing target: `/specs/<target-id>/<key>`, where `key` is the first
16 hex digits of `hash(sourcePath)` after `sha256:`. Its staged path is `<target-id>/<key>.md`.
The Markdown H1 supplies the page title, falling back to the target title. `content` excludes front
matter; `contentDigest` hashes the complete source bytes. Edges keep the independent scope,
composition, participation and required-contract dimensions.

`sourceDigest` hashes JSON serialization of ordered `[path, contentDigest]` pairs: configuration,
registry, and then every target's document and diagram-source references in registry order. Shared
references appear once per membership in this ordered input sequence. It is a byte/version identity,
not a semantic-completeness claim. Diagram sources declare matching kind/title and a generated HTML
output under `generated/diagrams/`; `sourceSha256` omits the digest prefix, and diagram routes are
`/diagrams/<first-16-hex-of-hash(source-path)>.html`.

## Materialization and required build collaborators

`scopedSidebar` returns category/doc item objects with `type`, `label`, `items`, category `collapsed`
and doc `id`. A Domain category also has `link: {type: doc, id}` pointing to its ontology.md
page; the same page is not repeated as a child item. `primaryDocument` requires exactly one
registered ontology.md for Domains and returns the first member for other kinds. Page.primary
marks that choice; diagrams and the site entry use it rather than arbitrary array order.
Separate root groups present Domain scopes and components; child categories follow
the corresponding parent axis. `rewriteLinks` rewrites only supported local Markdown links to the
registered page routes and rejects invalid or unregistered local destinations. Outside fenced code
blocks it handles inline links and images with these forms, whose URL has no whitespace or closing
parenthesis:

```markdown
[label](url)
![label](url)
```

A URL beginning with a scheme, `#`, or `/` is preserved unchanged. Other destinations
resolve relative to the source document directory using POSIX normalization; an optional `#anchor`
is preserved. Matching pages are selected by sourcePath: prefer the route belonging to the source
page's target; otherwise accept the destination only when exactly one page matches. A shared
destination with no same-target reference is ambiguous and is rejected. Relative non-Spec assets
have no matching page and are rejected; callers use a supported absolute or root-relative asset URL.
Unsupported Markdown forms are left unchanged. Link validation occurs during rewrite/materialization,
not during registry loading. The function returns text without changing sources.

`materializeScoped` consumes a model returned by the loader. Its `projectRoot` owns all output paths.
It replaces `docsite/.generated/content/` and `docsite/.generated/static/`, writes each page under
`content/specs/<stagedPath>`, copies declared diagram HTML to its static route and writes
`docsite/.generated/specs-sidebar.json`. Markdown front matter specifies format, slug, title and
sidebar label. At entry it removes `docsite/.generated/scoped-materialization.json`; only after all
assets and the sidebar succeed does it write this identity record as
`{schema_version: 1, sourceDigest: registry.sourceDigest}`. The function does not edit registered
Spec sources or promote `docsite/build`.
A failed write/copy rejects the promise and can leave partial derived assets. Retry requires a
fresh model and re-materializes these disposable directories; callers must not publish partial assets.

For Profile 8, `preparePublication(projectRoot)` resolves the root, loads the model, renders declared
diagrams when present, materializes assets, clears the selected Docusaurus generated directory, and returns
`{registry}`. Its required diagram renderer accepts the project root and produces each declared
HTML output before copying; rejection stops preparation. `buildSite()` operates on the docsite
containing this module, with project root its parent. Installed Node/Docusaurus dependencies must
be present. The Docusaurus collaborator must build into the supplied candidate directory, load the
plugin, call its hooks, report rendered routes and exit zero. A spawn error or nonzero exit rejects
without promoting. The function does not accept an arbitrary root argument.

The default `scopedContent` plugin requires Docusaurus `LoadContext.siteDir` and `baseUrl`; options may
provide `{projectRoot?: string}`, defaulting to the site's parent. `loadContent` loads the current
model and requires a valid materialization identity with the same source digest before returning it.
Missing, malformed or mismatched identity rejects and requires fresh preparation. This detects
source changes between materialization and plugin loading even when the page routes stay the same.
`contentLoaded({content, actions})` calls `actions.setGlobalData` with Workspace 14 entry target,
page metadata without Markdown bodies and architecture nodes/edges. `getPathsToWatch()` returns
absolute configuration, registry, Spec and diagram-source paths. `postBuild({outDir, routesPaths})`
requires the fresh source digest and materialization identity to match the loaded model, and every expected page route to be in
the rendered route inventory after base-URL normalization. Otherwise it throws before emitting
verification artifacts. These are the complete collaborator promises this Profile 8 path relies on.

## Build artifacts, validation and promotion

Successful plugin post-build writes these JSON artifacts in `outDir`:

```typescript
// build-manifest.json
{ schema_version: 14, sourceDigest: string,
  pages: {sourcePath: string; route: string; contentDigest: string}[] }
// architecture-graph.json
{ schema_version: 1, sourceDigest: string, nodes: Target[], edges: Edge[] }
```

`validateScopedBuild(root, directory)` reloads the current model and reads both artifacts from the
candidate directory. It resolves with no value only when schema versions, source digests, ordered
page path/route/digest entries and complete ordered graph nodes/edges match exactly. Stale or
incomplete manifest/graph, missing files or malformed JSON reject. This function does not repair
artifacts or promote output. Route coverage is measured by the plugin's post-build hook; callers
must not manufacture a manifest to bypass that hook.

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
if (!isScoped(projectRoot)) throw new Error('This consumer requires Profile 8');
const registry = loadScopedRegistry(projectRoot);
await materializeScoped(registry); // inspect derived assets; not yet a published build
await buildSite();                // integrated prepare/build/validate/promotion path
```

Repeated loading of unchanged inputs preserves identities. Repeated successful builds replace
derived output. No returned model, manifest or successful deterministic check proves that the Spec
supports every possible future task; independent Spec review and actual task gaps remain separate.

## Domain main-document and overview validation

Profile 8 publication rejects a missing or duplicate ontology.md member, shared or non-main-visible
Domain main Spec, and a main Spec without a real Ontology heading outside code fences. It rejects
a Domain without exactly one architecture declaration using recipe system-overview, an unsupported
recipe/kind pairing, duplicate source paths, mismatched source kind/title or non-showcase overview.
Other document names remain unrestricted and all registered members are published. These checks
prove structural conformance; they do not prove that a Domain's Ontology is semantically complete.

The renderer's Profile 8 transaction owns only generated/diagrams/. It validates all sources and
exact delivery receipts in a candidate directory, then atomically replaces that subdirectory.
Framework build outputs under generated/protocol, generated/roles and generated/docs survive both
success and failure. Legacy diagnostic rendering retains its existing output-root contract.
Profile 8 follows Archify's automatic legend by default; the legacy hidden-legend convention does
not constrain new Domain overviews. Rendering requires the project's pinned Archify package.

The main page keeps its title and introduction before the diagram. When the authored main Spec has
an Architecture overview section, inlineOverview binds the registered diagrams to that section;
otherwise a Domain's diagram follows its article. Domain main pages use the full reading column.
The renderer presents concorde-document identity, references and visibility in a Spec metadata
disclosure instead of a leading JSON code block, without changing the authored source or digest.

Production builds use docsite/.generated/docusaurus-production for Docusaurus-generated modules
and aliases. preparePublication mode build clears only that generated directory; the build process
sets DOCUSAURUS_GENERATED_FILES_DIR_NAME to the same relative path. Default preview mode uses
.docusaurus. A production build preserves an active preview's generated modules and cache, so
development-only debug routes cannot overwrite the production module graph.
