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
Module opens its `module.md`. The relationship graph distinguishes composes, uses and
required-interface edges.

### scenario.views.publish-preserves-previous-on-failure — An incomplete or stale candidate does not replace the published build

- GIVEN changes to registered sources during generation, a missing expected page, or a failed Mermaid render
- WHEN the candidate is validated before promotion
- THEN promotion is refused
- AND the previously published build is preserved unchanged

### scenario.views.publish-legacy-redirect — Legacy routes keep resolving after a document's membership changes

- GIVEN a document's previously published per-membership legacy route
- WHEN the current build is promoted
- THEN a redirect stub for that legacy route still resolves to the document's one canonical page

Every Concorde Module contains an inline Mermaid entity diagram in its `module.md` Relationships
subsection, with accessible title and description. Publication renders that fence in its authored
position; the containing Markdown is the sole authored diagram source and already participates in
source identity. No external diagram JSON, standalone diagram HTML, renderer Skill or separate
diagram installation is used. Local links resolve only registered document membership; unknown or
ambiguous links fail validation.

## Project introduction

### scenario.views.publish-homepage — Publishing an explicitly configured project introduction

- GIVEN site identity schema 1 in `docsite/site.json` includes a valid `homepage` object
- WHEN the site builds
- THEN the root page renders the configured introduction, features, workflow and quickstart with the site's title and description metadata
- AND its primary Spec navigation resolves to the registered entry Module's canonical page, with local links respecting the configured base URL
- AND Protocol and repository links appear only when their corresponding site identity options are enabled
- BUT the introduction does not join any Module collection, add a graph node or registered-page manifest entry, or grant agent context

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

## Independent Protocol documentation

### scenario.views.protocol-docs-tab — Enabling the optional Protocol documentation collection

- GIVEN `docsite/site.json` sets optional boolean `protocolDocs` to true
- WHEN the site builds
- THEN a Spec Protocol navbar tab publishes the `protocol/` chapters under `/protocol/` with their own chapter sidebar and local search index, independent of any project Spec registry
- BUT missing enabled content or a broken chapter link fails the site build

The collection requires no project Spec metadata or registry membership, and its pages do not
appear in the software architecture graph or registered Spec manifest. Omitting the option disables
this collection; scaffolding a consumer project does not enable or copy it. The adapter renders
inline `mermaid` fences using Docusaurus's Mermaid theme in both Protocol and registered Spec
pages; both retain accessible titles and descriptions.

These generated views are human navigation, not agent context grants. The publication Tool may read
multiple registered collections deterministically; an agent still receives one host-bound target
snapshot.

## Main routing view

Consumer-visible scaffold and publication lifecycle behavior remains on `module.views`. Select
`module.views` for registry loading, page materialization, link rewriting, sidebars, graph
construction, diagram staging or build-manifest validation.

Production builds keep their Docusaurus-generated modules separate from the development preview.
Building the site does not clear the preview's `.docusaurus` directory. Both views still derive
from the current registered sources and independently verify their publication inputs.
