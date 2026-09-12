```concorde-document
{
  "id": "document.views.publication",
  "owner": "module.views",
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
  "version": 2,
  "schema": {
    "type": "object",
    "required": [
      "proposal_version",
      "template_root",
      "template_digest",
      "identity",
      "github_pages",
      "files",
      "conflicts"
    ],
    "properties": {
      "proposal_version": {
        "enum": [
          2
        ]
      },
      "template_root": {
        "enum": [
          "docsite"
        ]
      },
      "template_digest": {
        "type": "string"
      },
      "identity": {
        "type": "object"
      },
      "github_pages": {
        "type": "boolean"
      },
      "files": {
        "type": "array",
        "minItems": 1,
        "items": {
          "type": "object",
          "required": [
            "path",
            "sha256"
          ],
          "properties": {
            "path": {
              "type": "string"
            },
            "sha256": {
              "type": "string"
            },
            "source": {
              "type": "string"
            },
            "content": {
              "type": "string"
            }
          },
          "additionalProperties": false
        }
      },
      "conflicts": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "path",
            "reason"
          ],
          "properties": {
            "path": {
              "type": "string"
            },
            "reason": {
              "type": "string"
            }
          },
          "additionalProperties": false
        }
      }
    },
    "additionalProperties": false
  },
  "semantics": "An exact, package-digest-bound scaffold proposal; the local ownership and content rules determine which files may be created. It grants no replacement or deletion authority.",
  "example": {
    "proposal_version": 2,
    "template_root": "docsite",
    "template_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "identity": {
      "schema_version": 1,
      "title": "Example",
      "url": "https://localhost",
      "baseUrl": "/",
      "organizationName": "example",
      "projectName": "example"
    },
    "github_pages": false,
    "files": [
      {
        "path": "docsite/package.json",
        "source": "docsite/package.json",
        "sha256": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
      }
    ],
    "conflicts": []
  }
}
```
```concorde-contract-binding
{
  "id": "contract.views.scaffold-proposal",
  "version": 2,
  "role": "provided",
  "peer": "external:docsite-caller",
  "selection_condition": "When a caller proposes or applies a docsite scaffold.",
  "relied_upon_guarantees": [
    "[Canonical agreement](#contract.views.scaffold-proposal) defines the exchanged value for this operation."
  ],
  "obligations": [
    "Preserve unrelated files and enforce exact proposal digests before applying any scaffold change."
  ]
}
```


Version 2 excludes project-owned custom docs and the retired projection publisher from the template.
Version-1 proposals are rejected with instructions to regenerate using `docsite --propose`;
acceptance of old template bytes does not authorize this changed inventory.

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
`tests/repository/`, `concorde-only/` and `custom-docs/` subtrees, `scaffold/`, and the root `site.json`. Non-excluded symlinks are
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
- AND a document referenced by several Modules still publishes once, showing its sole owner and every explicit inclusion reason
- AND inline Mermaid fences render in their authored position using the site's locked Mermaid integration

The route is `/specs/<source path with a leading specs/ root removed and .md dropped>`, or the full
path when a project's Specs are not entirely rooted at `specs/`. The sole Module Specs sidebar
uses registry Module parentage, with root Modules directly at the top level in registry order.
There is no file-directory tree or outer Module composition category. Every Module opens its
unique local `module.md`; expanding it reveals its owned supplementary documents in document
order, followed by child Modules in registry order. Referenced documents remain under their sole
owner and do not create duplicate pages or sidebar entries. A Module without children or
supplements is a direct document link.

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

## Retired unregistered projections

Publication ignores `generated/docs/instructions.json` and `generated/docs/wire.json`, even when
stale files exist. It emits no Projections navigation or instruction/wire reading pages. Successful
whole-directory promotion removes previously published projection pages; failed builds preserve
the previous output. Runtime schema generation and APIs remain Distribution/Development facilities.
Registered Specs are not restricted by the formerly reserved `projections/` source-path prefix.

## Project introduction

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

## Project-owned custom documentation

### scenario.views.custom-docs — Publishing separate project documentation

- GIVEN a consumer project configures `customDocs` collections or a `custom-docs/index.ts` extension
- WHEN its site builds
- THEN its custom documents and pages have independent navbar entries outside Module Specs
- AND custom pages do not register Spec ownership, appear in the registered-page manifest or grant agent Spec context
- BUT a collection containing a registered Spec, a conflicting route, missing enabled content or broken internal link rejects the build

The generic template defaults to one documentation tab, **Module Specs**. Optional `customDocs`
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

## Main routing view

Consumer-visible scaffold and publication lifecycle behavior remains on `module.views`. Select
`module.views` for registry loading, page materialization, link rewriting, sidebars, inline diagram
rendering or build-manifest validation.

Production builds keep their Docusaurus-generated modules separate from the development preview.
Building the site does not clear the preview's `.docusaurus` directory. Both views still derive
from the current registered sources and independently verify their publication inputs.

### scenario.views.publish-reference-link — References preserve one canonical page

- GIVEN one provider-owned interface document referenced by two consumer Modules, one by Module and one by document ID
- WHEN a publication candidate is built
- THEN it emits one canonical definition page with its sole owner and inclusion provenance
- AND consumer Markdown links point to that page and its stable contract/scenario anchors without embedding its body
- AND reference or ownership changes invalidate source-bound publication evidence
