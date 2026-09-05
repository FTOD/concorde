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
