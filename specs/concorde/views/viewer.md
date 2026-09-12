```concorde-document
{
  "id": "document.views.viewer",
  "owner": "module.views",
  "main_visible": true
}
```
# Understand Anything viewer service

This deterministic service opens an existing raw Understand Anything knowledge graph with the
installer-owned official viewer. Its entry is `scripts/run-ua-graph-viewer.py` in the Framework package. It
is a developer tool, not an agent Capability or a new Skill, and it launches no model cognition.

```bash
python3 .concorde/framework/scripts/run-ua-graph-viewer.py --project-root . --no-open
```

| Argument | Contract |
| --- | --- |
| `--project-root PATH` | Project directory, default `.`; it must exist and must not itself be a symlink |
| `--port N` | Optional integer from 0 through 65535, forwarded to the official viewer |
| `--no-open` | Optional flag forwarded to the official viewer to suppress its browser opening |

## Launching the viewer

### scenario.views.viewer-launch — Launching opens the first existing raw graph with the official viewer

- GIVEN an installed Framework manifest, a verified runtime marker and at least one existing raw graph in the manifest's ordered graph_paths
- WHEN `run-ua-graph-viewer.py --project-root PATH` runs
- THEN it selects the first existing graph, validates its shape and starts the official viewer with the requested port and browser behavior
- AND it returns the child process's exit code

The launcher selects the first existing raw graph in the manifest's ordered `graph_paths` list:
`.understand-anything/knowledge-graph.json`, then `.ua/knowledge-graph.json` in the current package.
The graph must be a regular JSON object with a string version, object project, and arrays nodes and
edges. Symlinks in the graph path are rejected.

### scenario.views.viewer-invalid-first-graph — An invalid first-choice graph fails without falling back

- GIVEN the first existing graph in order is not a regular JSON object with a string version, object project and array nodes/edges, or is reached through a symlink
- WHEN the launcher runs
- THEN it fails immediately
- AND it does not fall back to a later graph in the order

### scenario.views.viewer-missing-runtime — A missing or mismatched runtime blocks launch

- GIVEN a missing, unverified or mismatched runtime marker, viewer package identity or entrypoint file
- WHEN the launcher runs
- THEN it reports `CONCORDE VIEWER FAILED` on stderr and exits 3
- AND it does so before starting any process

### scenario.views.viewer-interrupted — Keyboard interruption is reported distinctly

- GIVEN a running viewer child process
- WHEN the launch is interrupted from the keyboard
- THEN the launcher returns exit code 130

These launcher boundaries are Module-wide requirements, not outcomes of this one scenario; see
[req.views.no-graph-generation](module.md#req.views.no-graph-generation),
[req.views.no-dependency-install](module.md#req.views.no-dependency-install) and
[req.views.cli-syntax-errors](module.md#req.views.cli-syntax-errors) in `module.md`.

After admission, the launcher checks Node.js >=18 and runs Node with the installed entrypoint and
project directory, forwarding the optional flags. The child runs from the project directory. The
launcher prints which graph it selected and returns the child exit code.

## Required installed-runtime contract

The project contains `.concorde/framework/concorde.json`. Its `runtime.venv` is `.concorde/.venv`,
and its viewer declaration supplies package, version, install_relative, entrypoint and graph_paths.
Relative runtime paths cannot be absolute, contain `..`, or contain backslashes. Relevant installed
paths must not be symlinks, and the viewer entrypoint must exist as a file.

The runtime marker `.concorde/.venv/.concorde-runtime.json` has schema_version 2, owner concorde,
viewer_version matching the manifest and viewer_entrypoint matching the declared entrypoint. The
viewer package.json must match the declared package name and version. These startup checks verify
recorded identity; installation is responsible for verifying the downloaded artifact.

The current package pins the official Egonex-AI/Understand-Anything viewer at 2.9.0 and installs it
under `share/concorde/understand-anything-viewer` inside the managed runtime. Its entrypoint is
`node_modules/understand-anything-viewer/bin/viewer.mjs`. The Installation service and Managed
runtime entity supply this state through the reviewed install path. Missing or stale state
requires that installation path to repair it; launch does not provision a replacement runtime
itself.

## Relationships and routing

This service participates in Developer view and feedback. Its user-facing contract is owned here;
`module.distribution` supplies viewer provisioning under the Installation entity's ownership.
Changes to viewer launch or graph admission select this service. Changes to runtime acquisition,
package verification or recovery select `module.distribution` through an admitted Module routing
view. No graph or viewer action grants an agent access to another target's implementation. The
deterministic export of a graph skeleton this launcher can open is a separate command, described in
[ua-graph](ua-graph.md).
