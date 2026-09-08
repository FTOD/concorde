```concorde-document
{
  "id": "document.publication.behavior",
  "targets": ["domain.docsite"],
  "main_visible": true
}
```

# Spec publication

This subdomain of [Developer view and feedback](../developer-view/ontology.md) turns registered project knowledge into a documentation site. Readers enter through
a Domain main Spec, explore its architecture and follow links to the detail they need. Source Specs
remain authoritative; published pages and diagrams are derived views.

## Architecture overview

The embedded **Spec publication** System overview shows the Domain boundary and its external relationships. Publication connects registered Spec and diagram sources to the build tools and the readers outside the publication boundary.

## Ontology

| Category | Entities | Relationships |
| --- | --- | --- |
| Authored knowledge | Domain, target, main Spec, topic/shared document, diagram source | A target explicitly registers its sources; ontology.md identifies a Domain main Spec |
| Published views | Page, route, sidebar, architecture diagram, relationship graph | Pages project source membership; Domain nodes link to their main pages; views show declared relationships |
| Evidence | Source digest, diagram receipt, build manifest | Evidence binds a complete candidate to exact source and artifact bytes |
| Participants | Author, publication service, Archify, Docusaurus, reader | Authors maintain sources; tools render them; readers navigate the result |

## Operating principles

This Domain scopes a human publication of explicitly registered architecture knowledge. Source
Markdown, registered diagram JSON and the target registry are authored inputs; generated pages,
sidebars, rendered diagrams and relationship graph JSON are derived views. A Page represents one target's membership of one Markdown document. A Route
is stable under title edits and contains target identity plus a digest of its source path. A Build
manifest binds route inventory to exact source bytes. A Relationship view separates Domain nesting,
component composition, scope participation and required/provided contract edges.
Every source displays its `concorde-document` identity, exact referencing targets and main visibility.
A shared physical truth produces one target-specific Page/Route for each declared membership without
copying or reinterpreting its content.

The Publication Service scaffolds a project-local Docusaurus site using a reviewed proposal. Its
Spec publication Module reads only explicitly registered documents, validates membership, rewrites
local navigation and materializes pages. Optional Markdown frontmatter and arbitrary topic filenames are accepted; each Domain
has one local ontology.md main Spec and a declared System overview. The two independent sidebar trees must not reinterpret Domain as a component kind. A
component shared by several scopes retains one identity. All documents belonging to a target remain
visible under Target Spec or Shared Specs as its complete resolved collection. Publication validates
that document declarations and reverse registry memberships agree.

The publisher may read the registry and many collections because it is a deterministic human-view
Tool. Navigation does not define an agent's cognitive permissions. Graph selection links to the target's
registered collection; traversing an edge never changes an agent invocation's admitted context membership.

Only declared diagram sources are rendered. Their declared kind/title must match their source, and
rendering failures stop publication. Unregistered nearby Markdown and diagram files are not discovered
as authority. A local link to an unregistered document is a publication error. A source change during
the build invalidates the candidate. Only a complete candidate with current source identity and all
expected routes is atomically promoted. Failed builds preserve the previous successful output.

## Further detail

The [Publication service](../services/publication-boundary.md) defines the publishing interface;
[Spec publication](../modules/spec-publication.md) describes page, route, navigation and build APIs.

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
