```concorde-document
{
  "id": "document.views.ua-graph",
  "owner": "module.views",
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

The exporter never scans the filesystem for undeclared content. Fresh skeleton structure comes
from registered Module identities, their `parent` and `uses` relationships, their registered
documents and their entities' declared file listings (directory prefixes expanded per the Protocol's
implementation context, never a broader directory walk). Overlay additionally admits the existing
graph for node reuse and the unlisted-file layer defined below. The target file is the first existing path
in the installed manifest's ordered `graph_paths`, defaulting to `.ua/knowledge-graph.json` when
neither exists yet.

## Local serialized graph contract

The UA graph export command admits the JSON schema below. It uses JSON Schema `type`,
`properties`, `required`, `items` and `minLength`; unspecified properties are admitted and
preserved outside exporter ownership. This is the exporter's local admission contract, not a
claim that the independent viewer validates every field. Node and layer IDs are unique within
their respective arrays. Edge duplicates and unresolved endpoints are not rejected by admission.
Optional node `tags` is an array of strings. Other extension fields, including `filePath`, are
not shape-checked; only a nonempty string `filePath` participates in reuse. Missing `layers` and
`tour` normalize to empty arrays; tour entries are unrestricted JSON values.

```concorde-contract
{
  "id": "contract.views.ua-overlay-input",
  "version": 1,
  "schema": {
    "type": "object",
    "required": [
      "version",
      "project",
      "nodes",
      "edges"
    ],
    "properties": {
      "version": {
        "type": "string"
      },
      "project": {
        "type": "object"
      },
      "nodes": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "id",
            "type"
          ],
          "properties": {
            "id": {
              "type": "string",
              "minLength": 1
            },
            "type": {
              "type": "string",
              "minLength": 1
            },
            "tags": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          }
        }
      },
      "edges": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "source",
            "target",
            "type"
          ],
          "properties": {
            "source": {
              "type": "string",
              "minLength": 1
            },
            "target": {
              "type": "string",
              "minLength": 1
            },
            "type": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "layers": {
        "type": "array",
        "items": {
          "type": "object",
          "required": [
            "id"
          ],
          "properties": {
            "id": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "tour": {
        "type": "array"
      }
    }
  },
  "semantics": "Existing graph input for skeleton overlay, subject to local unique-ID, path safety, reserved ownership and generated-ID collision rules. Extension fields outside ownership preserve their JSON values.",
  "example": {
    "version": "1.0.0",
    "project": {
      "name": "Example"
    },
    "nodes": [
      {
        "id": "scan:readme",
        "type": "document",
        "filePath": "README.md"
      }
    ],
    "edges": [],
    "layers": [],
    "tour": []
  }
}
```
```concorde-contract-binding
{
  "id": "contract.views.ua-overlay-input",
  "version": 1,
  "role": "required",
  "peer": "external:ua-graph-producer",
  "selection_condition": "When overlaying an existing graph produced outside Concorde.",
  "relied_upon_guarantees": [
    "[Canonical agreement](#contract.views.ua-overlay-input) defines the exchanged value for this operation."
  ],
  "obligations": [
    "Validate the input and preserve fields outside exporter ownership; reject invalid graphs without writes."
  ]
}
```


New skeletons have `version: "1.0.0"`, `tour: []`, and a `project` object with `name` equal to
the registry project ID, `languages: []`, `frameworks: []`, `description` equal to
`Skeleton graph deterministically exported by Concorde from the project's explicit Spec registry.`,
`analyzedAt` equal to creation time in UTC `YYYY-MM-DDTHH:MM:SSZ`, and `gitCommitHash` equal to
the current Git HEAD or an empty string if unavailable. Creation time and Git HEAD initialize
metadata once; overlays preserve them, so determinism means fixed derivation inputs and metadata,
not identical metadata from independent first exports at different times.

Generated record fields and values are as follows. IDs concatenate literal prefixes and exact
registry IDs or project-relative POSIX paths without hashing or escaping.

| Record | Generated fields |
| --- | --- |
| Module node | `id: "module:<target-id>"`, `type: "module"`, `name`: Module title, `summary`: first prose paragraph of its local module.md Purpose with trimmed lines joined by spaces (empty if absent), `tags: ["concorde-ua-graph", "module"]`, `complexity: "moderate"` |
| Document node | `id: "document:<path>"`, `type: "document"`, `name`: path basename, `filePath`: path, `summary`: registered document ID, `tags: ["concorde-ua-graph", "document"]` |
| Bound-file node | ID prefix `document:` for `.md`, `config:` for `.json`, `.yml`, `.yaml` or `.toml`, otherwise `file:`, followed by path; `type`: prefix without colon, `name`: basename, `filePath`: path, `summary`: path, `tags`: `concorde-ua-graph`, type, and `pending` when its selected entity declares that exact entry pending |
| Module layer | `id: "layer:<target-id>"`, `name`: Module title, `description`: Purpose summary through its first `. ` sentence boundary, or all of it if none, `nodeIds`: sorted distinct member node IDs |
| Unlisted layer | `id: "layer:unlisted"`, `name: "Not listed by any Module"`, `description: "File-level nodes from the Understand Anything graph that no Module lists as an implementation file."`, `nodeIds`: sorted distinct selected unclaimed file-like node IDs |

Documents are resolved before implementation files, with one generated record per ID. Thus a
bound Markdown file already generated as a registered document retains that document's summary.
Shared implementation paths use the first registered listing Module's node selection and pending state.
Spec documents always use their sole owner; references never alter their layer or implementation status. Each generated
edge has `source`, `target`, `type`, `direction: "forward"` and numeric `weight`; only the rows
with descriptions below include `description`. There is no generated edge ID.

| Relationship | Source → target | Type, weight, description |
| --- | --- | --- |
| Composition | parent Module → child Module | `contains`, `1.0`, `composes` |
| Dependency | consuming Module → used Module | `depends_on`, `0.8`, local dependency responsibility (fallback `uses`) |
| Document ownership | document → sole owner Module | `documents`, `0.7`, `owned by <target-id>` |
| Explicit context reference | selecting Module → referenced Module or document | `references`, `0.6`, `module` or `document` |
| Implementation listing | listing Module → bound file | `contains`, `0.9`, `<entity-id>: <entity-title>` for that Module's most-specific owning entity |
| Additional file lister | file → each lister after the first | `related`, `0.5`, `also listed by <target-id>` |

Overlay reuse considers surviving foreign nodes after the ownership removal below, matches the
exact `filePath` string, and selects the lexicographically smallest node ID among matching types.
Document-like means type exactly `document`; file-like means type in `file`, `config`, `document`,
`pipeline`, `resource`, `schema`. Reuse retains the entire foreign node unchanged. If no eligible
node exists, generation uses the rules above. A surviving foreign node or layer whose ID collides
with a newly generated node or layer causes rejection, even if its other fields resemble the
generated record. During overlay only, the exporter creates `layer:unlisted` when at least one
surviving file-like path is neither a registered document nor a bound implementation path; it
selects one node per such path using the same reuse order. Existing foreign layers remain under
the declared preservation rules even if they also refer to those nodes.

Serialization orders nodes and layers by ID and edges by `(source, target, type)` using a stable
sort, preserving equal-key edge order. Generated fields use the order shown above; top-level
generated order is `version`, `project`, `nodes`, `edges`, `layers`, `tour`. JSON uses two-space
indentation, literal Unicode and a final newline. Existing object-field order and extension values
are retained; normalization of absent layers/tour occurs once. Check compares these serialized
UTF-8 bytes, including formatting, against the existing file; a missing file is drift and is not
created by `--check`.

## Exporting a skeleton

### scenario.views.ua-graph-skeleton — Exporting derives a skeleton graph when none exists

- GIVEN a project with an explicit Spec registry and no existing raw UA graph at either manifest
  path
- WHEN `ua-graph` runs
- THEN it writes `.ua/knowledge-graph.json` with one node per registered Module, `contains` edges
  for composition, `depends_on` edges for `uses`, `documents` edges to sole document owners, explicit `references` edges without recursive expansion, and
  `contains` edges from each Module to the files its entities bind
- AND it writes one layer per Module whose registry `files` are nonempty, whose members are the
  files for which that Module is the first registered lister together with the documents that
  Module solely owns, and no `layer:unlisted`

## Overlaying an existing graph

Exporter ownership is determined by the selectors in the following scenario, not by a record of
which tool originally created each element. The `concorde-ua-graph` tag, the named layer namespace,
and edges incident to removed exporter nodes or currently registered Module node IDs are reserved
for Concorde's overlay. An admitted graph may contain elements created by another tool within this
scope; those elements are replaced too. Preservation applies to elements outside this scope. This
defines the existing independent export behavior and adds no docsite graph functionality.

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
  "module" node kind) is left untouched when that ID is neither a removed node ID nor a currently
  registered Module ID; edges naming it are preserved only when neither endpoint is in the
  declared ownership scope, so an edge to a currently registered Module node is replaced
- AND a Module's bound file reuses an existing node's ID when the UA graph already has a
  file-like node at that `filePath`, instead of creating a duplicate
- AND a Module's registered document likewise reuses an existing document-like node's ID at that
  `filePath` instead of creating a duplicate, and joins the layer of its sole owner
  when that Module has nonempty registry `files`; otherwise it remains outside generated
  layers, in both fresh export and overlay, and never joins `layer:unlisted`
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
  has a foreign node or layer ID that collides with an exported node or layer ID
- WHEN `ua-graph` runs, with or without `--check`
- THEN it fails with an error naming the existing file
- AND it does not write any change to that file

These exporter boundaries are Module-wide requirements; see
[req.views.ua-graph-registry-only](module.md#req.views.ua-graph-registry-only) and
[req.views.ua-graph-idempotent](module.md#req.views.ua-graph-idempotent) in `module.md`.

Context references are distinct graph edges and never acquire contains/depends_on meaning. A
referenced document stays in its owner's layer; neither its implementation files nor its owner's
references are imported. The current exporter still uses the schema-3 registry model and must
migrate this derivation before its output can satisfy Profile 12. Existing external overlay
admission remains contract version 1: the new edge type fits its open string type vocabulary.
