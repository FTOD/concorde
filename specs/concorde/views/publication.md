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
