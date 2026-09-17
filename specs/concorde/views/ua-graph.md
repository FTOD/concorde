# UA graph generation

Use the deterministic exporter to derive declared structure only, or the native analysis bridge
to combine Protocol, project Specs and project code in Understand Anything's full analysis flow.
Both produce graph data for the existing Viewer, independently of starting it. These are developer
tools, not Framework agent Capabilities or new Skills. The exporter launches no model cognition;
the native analysis bridge explicitly starts an external model-backed host.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Entity](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Composition](../spec/registry.md#terminology) | Defined in Registry. |
| [Use](../spec/registry.md#terminology) | Defined in Registry. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Implementation binding](../spec/registry.md#terminology) | Defined in Registry. |
| [Implementation context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Capability](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Skill](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worktree](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Invocation

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

## Overlaying an existing graph

Exporter ownership is determined by the [overlay scenario](scenarios.md#scenario.views.ua-graph-overlay), not by a record of
which tool originally created each element. The `concorde-ua-graph` tag, the named layer namespace,
and edges incident to removed exporter nodes or currently registered Module node IDs are reserved
for Concorde's overlay. An admitted graph may contain elements created by another tool within this
scope; those elements are replaced too. Preservation applies to elements outside this scope. This
defines the existing independent export behavior and adds no docsite graph functionality.

## Native analysis

For a graph that explains actual implementation alongside declared structure, run:

```bash
python3 scripts/concorde.py ua-analyze \
  --ua-plugin-root /absolute/path/to/understand-anything-plugin \
  --allow-primary-worktree
```

In an installed project, use `python3 .concorde/framework/scripts/concorde.py` instead.
The analysis plugin is separate from the Viewer package. The first adapter supports the installed,
already-built Understand Anything 2.9.6 Claude plugin, a POSIX host, Node.js 22 or newer, and a
working authenticated Claude CLI. It neither installs these dependencies nor bypasses host
permissions. Configure required native permissions beforehand; a denial in a noninteractive run
is a failure, not permission to switch hosts or escalate privileges. Use `--claude` for a different
Claude executable path and `--model` to select its model; otherwise the native host chooses its
configured default. `--timeout` bounds the host run in seconds; `--language` selects output
language, defaulting to English. No Viewer is started automatically.

Add `--prepare-only` to inspect the input package without invoking a model. Preparation still
checks the local runtime and plugin and writes its own run artifacts; it neither creates nor
overwrites the project's saved graph. Its result says **prepared**, not **analysis complete**.

The bridge first derives a separate UA-native seed and complete per-Module Spec context indexes.
The indexes retain reading/metadata pairs, ownership, inclusion provenance and exact-byte digests;
workers read original sources rather than a replacement summary. Code is supplied independently
through the project workspace. UA retains its scanner, exclusions, batching, agents, architecture
analysis, guided tour, validation and save steps. The prompt asks its orchestrator to pass Spec
context to those agents and carry the seed through assembly before architecture and tour work.
There is no second Concorde overlay after analysis. Declared module structure stays identifiable,
while summaries and code observations can be enriched, including discrepancies from declarations.
Unbound project code remains eligible for native scanning.

The initial adapter always requests a full analysis. This avoids incorrectly treating an unchanged
Git commit as proof that Specs, Protocol or dirty working files have not changed. The invocation
accepts native scan-size and ignore-file confirmations, including generation of a starter ignore
file when absent; review existing ignore rules before launching. This does not authorize dependency
installation, source edits or permission bypasses. The bridge directs writes to UA artifacts and
its completion report, but these instructions are not a sandbox: the native host still has its
normal developer-session permissions and project hooks. Do not run it concurrently with another
UA process or source editing session. It never redirects a linked worktree to the primary checkout.

Each run retains its input package, prompt, host logs and receipt under `.concorde/runs/`. Success
requires a completed native run, valid output, preserved declared structure and unchanged inputs.
It is not proof that AI interpretations are correct or that every source was read. On failure,
UA may have saved partial graph or metadata files; the bridge reports failure and leaves them
inspectable rather than silently overwriting possible user edits. A copy of the previous graph,
when present, is retained for deliberate recovery; it is not a backup of every UA artifact.
A timeout or interruption kills the native process group before releasing the bridge's run lock.
After an abrupt bridge crash, verify no native process is active before removing a stale lock and
retrying. See the [native analysis contract](contracts.md#ua-native-analysis-contract) for exact
admission, artifacts and output checks.

## Precise specifications

The Views Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
