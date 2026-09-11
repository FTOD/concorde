```concorde-document
{
  "id": "document.views.publication",
  "targets": [
    "module.views"
  ],
  "main_visible": true
}
```
# Publication service

## Scaffolding a project's docsite

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

## Scaffold proposal exchange and ownership

The Docsite scaffold command exchanges the following JSON value with its caller. The schema uses
JSON Schema's `type`, `properties`, `required`, `items`, `enum`, `minItems` and
`additionalProperties` vocabulary; the path, digest and content rules below further constrain it.
`--apply --proposal PATH` accepts this value directly, as `{"proposal": value}`, or as
`{"result": {"proposal": value}}` in the propose command's Tool result. PATH is a safe
project-relative JSON file. Proposal generation returns `result.proposal` and a separate
`result.prerequisites` array of `{name, status, detail}` strings for Node and npm; prerequisite
warnings do not install dependencies or change proposal bytes.

```concorde-contract
{
  "id": "contract.views.scaffold-proposal",
  "version": 1,
  "role": "provided",
  "peer": "external:docsite-caller",
  "schema": {
    "type": "object",
    "required": ["proposal_version", "template_root", "template_digest", "identity", "github_pages", "files", "conflicts"],
    "properties": {
      "proposal_version": {"enum": [1]},
      "template_root": {"enum": ["docsite"]},
      "template_digest": {"type": "string"},
      "identity": {"type": "object"},
      "github_pages": {"type": "boolean"},
      "files": {"type": "array", "minItems": 1, "items": {
        "type": "object", "required": ["path", "sha256"],
        "properties": {"path": {"type": "string"}, "sha256": {"type": "string"}, "source": {"type": "string"}, "content": {"type": "string"}},
        "additionalProperties": false
      }},
      "conflicts": {"type": "array", "items": {
        "type": "object", "required": ["path", "reason"],
        "properties": {"path": {"type": "string"}, "reason": {"type": "string"}},
        "additionalProperties": false
      }}
    },
    "additionalProperties": false
  },
  "semantics": "An exact, package-digest-bound scaffold proposal; the local ownership and content rules determine which files may be created. It grants no replacement or deletion authority.",
  "example": {"proposal_version": 1, "template_root": "docsite", "template_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000", "identity": {"schema_version": 1, "title": "Example", "url": "https://localhost", "baseUrl": "/", "organizationName": "example", "projectName": "example"}, "github_pages": false, "files": [{"path": "docsite/package.json", "source": "docsite/package.json", "sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000"}], "conflicts": []}
}
```

The example illustrates the schema, not an applicable package inventory or real digest. Each file
entry has exactly one of `source` and `content`, and paths are unique and sorted. `sha256` hashes
the resolved UTF-8 content bytes. The complete file set is the installed adapter inventory plus
`docsite/site.json`, and, only when `github_pages` is true,
`.github/workflows/deploy-docsite.yml`. An adapter entry's source and destination are its identical
package-relative path; the workflow source is `docsite/scaffold/deploy-docsite.yml` and its only
destination is the workflow path above. Only site identity uses inline `content`, containing the
proposal's `identity` serialized as sorted-key, two-space-indented JSON with a final newline.
No remapping, additional destination, partial inventory, replacement or deletion operation is
owned. In particular, the scaffold does not upgrade an existing consumer site by deleting its old
graph source files; graph removal from this repository's publishing template is a source change,
and successful site builds replace obsolete published output as specified below.

The adapter inventory consists of regular files below the installed package's `docsite/` with
suffix `.css`, `.json`, `.md`, `.svg`, `.ts`, `.tsx` or `.yml`, excluding any directory component
named `node_modules`, `build`, `.generated`, `.docusaurus` or `coverage`, the root-relative
`tests/repository/` subtree, `scaffold/`, and the root `site.json`. Non-excluded symlinks are
invalid. These template files contain no removed graph feature. Inventory discovery reads the
installed template, never consumer Spec directories. `template_digest` hashes UTF-8 lines sorted
by path, each `path`, a tab and the lowercase SHA-256 hex of its bytes, joined by newlines with a
final newline. The workflow's own file digest also binds its bytes. A changed package digest or
file digest invalidates acceptance.

Identity has `schema_version: 1`, nonempty `title`, absolute HTTP(S) `url`, slash-prefixed and
slash-suffixed `baseUrl`, `organizationName`, `projectName`, and optional absolute HTTP(S)
`repository`. Title defaults to the registered entry Module's title. A GitHub repository supplies
owner/repository names, `https://<owner>.github.io`, and `/<repo>/` (or `/` for the owner's Pages
repository); otherwise defaults are `https://localhost`, `/` and the lowercase title with
non-alphanumeric runs replaced by hyphens, stripped at the ends, falling back to `project`.
Explicit options override their corresponding defaults. Scaffolding omits optional homepage and
Protocol content. `conflicts` lists proposed paths already present, with reason `target already
exists`; it is informational and authorizes no overwrite.

Apply first validates the proposal and its owned inventory. If every destination already equals
the accepted bytes it returns `unchanged` without writing. Otherwise every destination must be
absent: any existing destination, including a mix of exact and absent files, returns `conflict`
without writing. Existing symlinks or unsafe paths reject. The creation transaction checks a null
before-digest (absence) for every destination before staging and again before each write; these
before-digests are transaction state, not fields in the exchanged proposal. A concurrent change
rejects with original-byte recovery for writes already performed. Invalid proposals return
`invalid`; staging failures return `failed`; successful creation returns `success` with the
created paths. Repeating an unchanged proposal is idempotent. No accepted proposal can replace or
delete existing files, including project Specs.

For a Module, its unique local `module.md` is the source entry, independent of collection order.

## Publishing registered Specs

### scenario.views.publish-candidate — Publishing derives one canonical page per registered document

- GIVEN an explicitly registered project registry
- WHEN the site is built
- THEN every registered physical document publishes exactly one canonical page at a readable route derived from its source path
- AND a document shared by several Modules still publishes once, showing every declared membership
- AND inline Mermaid fences render in their authored position using the site's locked Mermaid integration

The route is `/specs/<source path with a leading specs/ root removed and .md dropped>`, or the full
path when a project's Specs are not entirely rooted at `specs/`. The primary sidebar mirrors the
registered documents' own directory hierarchy with file-name entries, from registered documents
only, never directory scanning. A secondary sidebar presents the Module composition tree. Every
Module opens its `module.md`.

### scenario.views.publish-without-graph — Publishing retains reading and navigation without a graph view

- GIVEN a valid registered project using the current publishing template
- WHEN the site is built and promoted
- THEN the site exposes no standalone `/graph` page, Graph navigation entry or graph-view UI
- AND it emits no `architecture-graph.json` or graph-specific global-data projection
- AND registered pages, directory and Module navigation, source provenance, identity anchors and inline Mermaid rendering remain available
- AND enabled homepage, Protocol and instruction projection surfaces retain their normal reading and navigation behavior
- BUT publication does not invoke, replace or remove the separate UA exporter or official viewer

Removing this feature includes its dedicated implementation, resources and dependencies. A shared
resource or dependency remains when another retained publication function needs it; in particular,
inline Mermaid rendering remains supported. The docsite provides no substitute embedded UA view or
redirect from the removed graph page. UA continues through its existing independent commands.

### scenario.views.publish-preserves-previous-on-failure — An incomplete or stale candidate does not replace the published build

- GIVEN changes to registered sources during generation, a missing expected page, or a failed Mermaid render
- WHEN the candidate is validated before promotion
- THEN promotion is refused
- AND the previously published build is preserved unchanged

### scenario.views.publish-legacy-redirect — Legacy routes resolve for current document memberships

- GIVEN a registered document and a legacy alias derived from one of its current registered memberships
- WHEN the current build is promoted
- THEN a redirect stub for that legacy route still resolves to the document's one canonical page
- AND aliases are recomputed from current memberships; publication does not retain historical aliases for removed memberships

This compatibility promise concerns registered-document aliases, not the removed standalone graph
page. Every Concorde Module contains an inline Mermaid entity diagram in its `module.md`
Relationships subsection, with accessible title and description. Publication renders that fence in
its authored position; the containing Markdown is the sole authored diagram source and already
participates in source identity. No external diagram JSON, standalone diagram HTML, renderer Skill
or separate diagram installation is used. Local links resolve only registered document membership;
unknown or ambiguous links fail validation.

### scenario.views.publish-repeat-without-graph — Rebuilding replaces obsolete graph output

- GIVEN an existing published build that contains the former standalone graph page and architecture-graph artifact
- WHEN a fresh build using the current publishing template successfully validates and is promoted
- THEN the replacement published build contains neither the former graph page nor its dedicated artifacts or assets
- AND a subsequent successful build retains that absence and the registered-document reading and navigation behavior
- BUT a failed candidate leaves the previous published build unchanged under the normal promotion rules

## Retained projection input agreement

For Concorde's self-hosted reading surfaces, the Docsite build interface consumes the existing
Distribution (`module.distribution`) projections at the exact project-relative paths
`generated/docs/instructions.json` and `generated/docs/wire.json`. Both files must exist to enable
the pair of reading pages and their Projections navigation; if either is absent, both pages and
that navigation are omitted. These presentation inputs do not join registered Spec membership,
the registered-page manifest or its `sourceDigest`, and grant no Agent context.

The JSON records have the following retained shapes, using TypeScript notation as in the local
publication model. Neither file has a `schema_version` envelope.

```typescript
interface InstructionProjection {
  agents: {
    name: string; spec: string; harness: string; instructions: string; sources: string[];
    modes: {name: string; instructions: string; contract: object}[];
  }[];
  skills: {name: string; description: string; capability: string; body: string}[];
}
type WireProjection = Record<string, object>; // type ID -> JSON Schema object
```

An Agent's `name` identifies its reading section, `spec` is a source path string, `harness` names
its harness and `sources` lists its instruction source paths. Its `instructions` is the public
common responsibility text. Each mode's `name` identifies the mode, its `contract` is displayed
directly as JSON, and its `instructions` already contains the complete common-plus-selected-mode
text: publication does not concatenate the common text again. Modes remain separate reading
sections, never one combined runtime prompt. Skill records supply the skill name, description,
capability identity and body for reading. Agent, mode and skill arrays retain input order.

The wire projection maps each type ID directly to its JSON Schema object. Publication shows the
type IDs in sorted order and displays their values as JSON. It has no `contracts` array and
requires no synthetic title, version, semantics or example fields. These are the existing
Distribution inputs, not a new producer format or a schema migration.

When the pair is enabled, publication uses `safeRead` and JSON parsing for both files, preserving
the path/read and parse failures defined by the build interface. This description adds no
projection validator, duplicate-ID check or version admission rule. Failure follows the normal
candidate failure and preservation rules. Repeated builds read current inputs and derive the
pair's availability again. Neither projection enables a graph page or an embedded UA replacement;
these reading semantics belong to [publication without a graph](#scenario.views.publish-without-graph).

## Project introduction

### scenario.views.publish-homepage — Publishing an explicitly configured project introduction

- GIVEN site identity schema 1 in `docsite/site.json` includes a valid `homepage` object
- WHEN the site builds
- THEN the root page renders the configured introduction, features, workflow and quickstart with the site's title and description metadata
- AND when `homepage.reference` is configured, a reference section after the quickstart renders its tables with section navigation, column headers and keyboard-accessible horizontal scrolling on narrow screens
- AND its primary Spec navigation resolves to the registered entry Module's canonical page, with local links respecting the configured base URL
- AND Protocol and repository links appear only when their corresponding site identity options are enabled
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

## Independent Protocol documentation

### scenario.views.protocol-docs-tab — Enabling the optional Protocol documentation collection

- GIVEN `docsite/site.json` sets optional boolean `protocolDocs` to true
- WHEN the site builds
- THEN a Spec Protocol navbar tab publishes the `protocol/` chapters under `/protocol/` with their own chapter sidebar and local search index, independent of any project Spec registry
- BUT missing enabled content or a broken chapter link fails the site build

The collection requires no project Spec metadata or registry membership, and its pages do not
appear in the registered Spec manifest. Omitting the option disables this collection; scaffolding
a consumer project does not enable or copy it. The adapter renders inline `mermaid` fences using
Docusaurus's Mermaid theme in both Protocol and registered Spec pages; both retain accessible
titles and descriptions.

These generated views are human navigation, not agent context grants. The publication Tool may read
multiple registered collections deterministically; an agent still receives one host-bound target
snapshot.

## Main routing view

Consumer-visible scaffold and publication lifecycle behavior remains on `module.views`. Select
`module.views` for registry loading, page materialization, link rewriting, sidebars, inline diagram
rendering or build-manifest validation.

Production builds keep their Docusaurus-generated modules separate from the development preview.
Building the site does not clear the preview's `.docusaurus` directory. Both views still derive
from the current registered sources and independently verify their publication inputs.

For this Framework repository, the Agent instructions projection shows common responsibilities
and separate mode sections. Each mode section displays its explicit context/result/authority
contract and its complete common-plus-selected-mode instruction text. This human browsing view
never combines all modes into one runtime prompt or grants an Agent additional context.
