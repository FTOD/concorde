# How Specs become a documentation site

This Domain scopes a human publication of explicitly registered architecture knowledge. Source
Markdown and the target registry are authoritative; generated pages, sidebars, diagrams and graph
JSON are derived views. A Page represents one target's membership of one Markdown document. A Route
is stable under title edits and contains target identity plus a digest of its source path. A Build
manifest binds route inventory to exact source bytes. A Relationship view separates Domain nesting,
component composition, scope participation and required/provided contract edges.

The Publication Service scaffolds a project-local Docusaurus site using a reviewed proposal. Its
Spec publication Module reads only explicitly registered documents, validates membership, rewrites
local navigation and materializes pages. Arbitrary filenames and optional Markdown frontmatter are
accepted. The two independent sidebar trees must not reinterpret Domain as a component kind. A
component shared by several scopes retains one identity. All documents belonging to a target remain
visible as its complete collection.

The publisher may read the registry and many collections because it is a deterministic human-view
Tool. Navigation does not define an agent's cognitive permissions. Graph selection links to the target's
registered collection; traversing an edge never changes Operation context membership.

Only declared diagram sources are rendered. Their declared kind/title must match their source, and
rendering failures stop publication. Unregistered nearby Markdown and diagram files are not discovered
as authority. A local link to an unregistered document is a publication error. A source change during
the build invalidates the candidate. Only a complete candidate with current source identity and all
expected routes is atomically promoted. Failed builds preserve the previous successful output.

## Main routing view

The main coordinator selects `service.publication` for consumer-facing docsite proposal, build and
publication outcomes. It selects `module.spec-publication` for the in-process registry-to-pages,
sidebar, graph, diagram and build-manifest API. The Module ID is visible here so work can be routed;
its Module Spec remains private to the fresh target worker.

## Participating components

```concorde-participants
[
  {
    "target_id": "service.publication",
    "kind": "service",
    "responsibility": "Produce and promote the consumer-facing documentation site from registered sources.",
    "selection_condition": "Select for docsite proposals, content inspection, builds, publication outcomes, or failures.",
    "relied_upon_promises": [
      "Only a complete candidate bound to current registered source bytes is promoted."
    ]
  },
  {
    "target_id": "module.spec-publication",
    "kind": "module",
    "responsibility": "Transform registry targets into pages, navigation, relationship data, diagrams, and build manifests.",
    "selection_condition": "Select for in-process publication parsing, routing, graph construction, or candidate verification.",
    "relied_upon_promises": [
      "Unregistered Markdown and undeclared diagrams never become published authority."
    ]
  }
]
```
