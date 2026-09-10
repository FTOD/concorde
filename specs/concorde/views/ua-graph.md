```concorde-document
{
  "id": "document.views.ua-graph",
  "targets": [
    "module.views"
  ],
  "main_visible": true
}
```
# UA graph exporter

This deterministic Tool exports or overlays a skeleton Understand Anything knowledge graph from the
project's explicit Spec registry. It is a developer tool, not an agent Capability or a new Skill,
and it launches no model cognition.

```bash
python3 -m concorde --project-root . ua-graph [--check]
```

| Argument | Contract |
| --- | --- |
| `--project-root PATH` | Project directory, default `.`; the registry must load |
| `--check` | Report whether the exported graph is current without writing |
| `--allow-primary-worktree` | Required to write outside an isolated linked worktree |

The exporter never scans the filesystem for undeclared content. Every node, edge and layer it adds
comes from registered Module identities, their `parent` and `uses` relationships, their registered
documents and their entities' declared file listings (directory prefixes expanded per the Protocol's
implementation context, never a broader directory walk). The target file is the first existing path
in the installed manifest's ordered `graph_paths`, defaulting to `.ua/knowledge-graph.json` when
neither exists yet.

## Exporting a skeleton

### scenario.views.ua-graph-skeleton — Exporting derives a skeleton graph when none exists

- GIVEN a project with an explicit Spec registry and no existing raw UA graph at either manifest
  path
- WHEN `ua-graph` runs
- THEN it writes `.ua/knowledge-graph.json` with one node per registered Module, `contains` edges
  for composition, `depends_on` edges for `uses`, `documents` edges for registered documents, and
  `contains` edges from each Module to the files its entities bind
- AND it writes one layer per Module whose registry `files` are nonempty, whose members are the
  files that Module's entities bind together with the documents that Module is the first registered
  target for, and no `layer:unlisted`

## Overlaying an existing graph

### scenario.views.ua-graph-overlay — Re-exporting overlays and replaces only Concorde's own elements

- GIVEN an existing raw UA graph, produced by the real Understand Anything tool or by a prior export
- WHEN `ua-graph` runs
- THEN it removes only the nodes tagged `concorde-ua-graph`, the layers named `layer:module.*` or
  `layer:unlisted`, the `layer:<id>` belonging to each removed Module node (including Module IDs
  without a `module.` prefix), and the edges whose source or target is one of those removed node IDs or a
  `module:<id>` ID for a currently registered Module, then adds a freshly derived set of those same
  kinds of elements
- AND every other node, edge, layer, and the graph's `project`, `version`, `tour` and extension
  fields retain their JSON values; whitespace and array ordering may be normalized
- AND a foreign node whose own ID happens to start with `module:` (for example a real scan's own
  "module" node kind), and every edge naming it, are left untouched when that ID is neither a
  removed node ID nor a currently registered Module ID
- AND a Module's bound file reuses an existing node's ID when the UA graph already has a
  file-like node at that `filePath`, instead of creating a duplicate
- AND a Module's registered document likewise reuses an existing document-like node's ID at that
  `filePath` instead of creating a duplicate, and joins the layer of the first Module registered
  for it rather than `layer:unlisted`
- AND running the export again against its own prior output produces byte-identical output

## Files shared by several Modules

### scenario.views.ua-graph-shared-file — A shared file gets one layer and a related edge to the rest

- GIVEN one implementation file that several Modules' entities list
- WHEN `ua-graph` runs
- THEN every listing Module still gets its own `contains` edge to that file's node, from its own
  entity
- AND the file's node joins only the layer of the Module registered first for that file
- AND every other listing Module gets one additional `related` edge from that file's node naming
  it as also listed by that Module

## Checking freshness

### scenario.views.ua-graph-check — `--check` reports drift from the current registry without writing

- GIVEN a previously exported or overlaid graph and a registry that has since changed
- WHEN `ua-graph --check` runs
- THEN it recomputes the same derivation and compares it to the file on disk
- AND a match returns success and a difference returns an `invalid` finding, in both cases without
  writing

## Rejecting an unsupported existing graph

### scenario.views.ua-graph-invalid-input — A malformed existing graph is rejected without writing

- GIVEN an existing file at the target path that is not a JSON object, is reached through a
  symlink, is a directory, lacks a string `version`, an object `project`, or array `nodes` and
  `edges`, contains malformed node, edge or layer records or duplicate node or layer IDs, or
  has a foreign node ID that collides with an exported node ID
- WHEN `ua-graph` runs, with or without `--check`
- THEN it fails with an error naming the existing file
- AND it does not write any change to that file

These exporter boundaries are Module-wide requirements; see
[req.views.ua-graph-registry-only](module.md#req.views.ua-graph-registry-only) and
[req.views.ua-graph-idempotent](module.md#req.views.ua-graph-idempotent) in `module.md`.
