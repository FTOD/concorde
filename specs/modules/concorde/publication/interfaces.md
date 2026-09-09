```concorde-document
{
  "id": "document.publication.boundary",
  "targets": [
    "module.publication"
  ],
  "main_visible": true
}
```

# Publication service

## feature.publication.publish

The deterministic `concorde docsite --propose` command creates a scaffold proposal using optional
--title, --repository, --url, --base-url and --github-pages. `--apply --proposal PATH` applies the
accepted project-relative JSON proposal under the host's worktree policy. Proposal application checks
before-digests, owns only scaffold files and restores originals on failure; project Specs are inputs.
For a Module, its unique local `module.md` is the source entry, independent of
collection order; an Implementation Spec uses its first registered document as its entry.

The resulting project-local site runs `npm run validate` and `npm run build`. Profile 9 publication
consumes .concorde/config.json and its explicit registry, not recursive filename discovery. Every
registered physical document publishes exactly one canonical page, at a readable route derived from
its source path: `/specs/<source path with a leading specs/ root removed and .md dropped>`
(a project whose Specs are not entirely rooted at specs/ keeps full paths). The primary sidebar
mirrors the registered documents' own directory hierarchy with file-name entries, from registered
documents only, never directory scanning. A secondary sidebar presents the Module composition tree and a separate Implementation Spec list. Every Module opens its module.md; Implementation pages list bound files and using Modules. The relationship graph distinguishes composes, uses, implemented_by and required-interface edges.
A shared physical document publishes once, at its one canonical page, showing every declared
membership; the secondary by-target sidebar still lists it under each referencing target. Every
membership's legacy `/specs/<target-id>/<source-path-hash>` route is preserved as a redirect to the
document's canonical page, so previously published links keep resolving.

The build manifest has schema_version 16, sourceDigest and a pages array of sourcePath, route,
contentDigest, the referencing target ids and the legacy alias routes kept as redirects.
architecture-graph.json has schema_version 1, sourceDigest, nodes and typed edges.
Each candidate validates exact source identity, route inventory and legacy redirect coverage before
atomic promotion. Changes during generation or missing pages invalidate the candidate and preserve
the previous build.
Declared diagrams are validated/rendered from exact registry sources. Every Module declares one
architecture with recipe system-overview; Archify renders it with showcase checks and the site
embeds it on module.md. Other diagram filenames remain explicit declarations. Profile 9 diagram
builds replace only generated/diagrams/ and preserve the Framework's generated rules, roles and docs.
The project provides its pinned Archify skill and Node dependencies before publication; initialization
does not silently download build tools.
Local links resolve only registered document membership; unknown or ambiguous links fail validation.

These generated views are human navigation, not agent context grants. The publication Tool may
read multiple registered collections deterministically; an agent still receives one host-bound target
snapshot. Legacy Profile 7 publication readers remain isolated diagnostics and do not admit agent work.

## Main routing view

Consumer-visible scaffold and publication lifecycle behavior remains on `module.publication`.
Select `module.publication` for registry loading, page materialization, link rewriting, sidebars,
graph construction, diagram staging or build-manifest validation. Its stable ID is exposed for
routing; the coordinator must explicitly admit its complete Module collection before reading it.

Production builds keep their Docusaurus-generated modules separate from the development preview.
Building the site does not clear the preview's .docusaurus directory. Both views still derive from
the current registered sources and independently verify their publication inputs.
