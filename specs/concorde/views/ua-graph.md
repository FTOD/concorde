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
graph for node reuse and the [unlisted-file layer contract](contracts.md#ua-graph-local-serialized-graph-contract). The target file is the first existing path
in the installed manifest's ordered `graph_paths`, defaulting to `.ua/knowledge-graph.json` when
neither exists yet.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Implementation Specs](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Overlaying an existing graph

Exporter ownership is determined by the [overlay scenario](scenarios.md#scenario.views.ua-graph-overlay), not by a record of
which tool originally created each element. The `concorde-ua-graph` tag, the named layer namespace,
and edges incident to removed exporter nodes or currently registered Module node IDs are reserved
for Concorde's overlay. An admitted graph may contain elements created by another tool within this
scope; those elements are replaced too. Preservation applies to elements outside this scope. This
defines the existing independent export behavior and adds no docsite graph functionality.

## Precise specifications

The Views Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
