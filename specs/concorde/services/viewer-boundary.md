```concorde-document
{
  "id": "document.viewer.boundary",
  "targets": [
    "service.viewer"
  ],
  "main_visible": true
}
```

# Understand Anything viewer service

## feature.viewer.launch

This deterministic service opens an existing raw Understand Anything knowledge graph with the
installer-owned official viewer. Its entry is `scripts/run-viewer.py` in the Framework package.
It is a developer tool, not an agent Capability or a new Skill, and it launches no model cognition.

```bash
python3 .concorde/framework/scripts/run-viewer.py --project-root . --no-open
```

| Argument | Contract |
| --- | --- |
| `--project-root PATH` | Project directory, default `.`; it must exist and must not itself be a symlink |
| `--port N` | Optional integer from 0 through 65535, forwarded to the official viewer |
| `--no-open` | Optional flag forwarded to the official viewer to suppress its browser opening |

The launcher verifies the installed Framework manifest, runtime marker and official viewer package
identity. It selects the first existing raw graph in the manifest's ordered graph_paths list:
`.understand-anything/knowledge-graph.json`, then `.ua/knowledge-graph.json` in the current package.
An invalid first existing graph fails; it does not silently switch to the other graph.

The graph must be a regular JSON object with a string version, object project, and arrays nodes and
edges. Symlinks in the graph path are rejected. A Concorde explore/result envelope is not raw viewer
input and is rejected. The launcher does not verify graph-to-code freshness, graph semantics or
agreement with the Spec; it does not generate or rewrite the graph.

After admission, the launcher checks Node.js >=18 and runs Node with the installed entrypoint and
project directory, forwarding the optional flags. The child runs from the project directory. The
launcher prints which graph it selected and returns the child exit code. Keyboard interruption
returns 130. Invalid launch state or an OS failure reports `CONCORDE VIEWER FAILED` on stderr and
returns 3 before accepting a launch; invalid CLI syntax or a port outside the range exits through
argparse with code 2. No dependency resolution or network acquisition occurs in the launcher.

## Required installed-runtime contract

The project contains `.concorde/framework/concorde.json`. Its runtime.venv is `.concorde/.venv`, and
its viewer declaration supplies package, version, install_relative, entrypoint and graph_paths.
Relative runtime paths cannot be absolute, contain `..`, or contain backslashes. Relevant installed
paths must not be symlinks, and the viewer entrypoint must exist as a file.

The runtime marker `.concorde/.venv/.concorde-runtime.json` has schema_version 2, owner concorde,
viewer_version matching the manifest and viewer_entrypoint matching the declared entrypoint.
The viewer package.json must match the declared package name and version. These startup checks
verify recorded identity; installation is responsible for verifying the downloaded artifact.

The current package pins the official Egonex-AI/Understand-Anything viewer at 2.9.0 and installs it
under `share/concorde/understand-anything-viewer` inside the managed runtime. Its entrypoint is
`node_modules/understand-anything-viewer/bin/viewer.mjs`. The Installation service and managed-runtime
Module supply this state through the reviewed install path. Missing or stale state requires that
installation path to repair it; launch does not provision a replacement runtime itself.

## Relationships and routing

This service participates in Developer view and feedback. Its user-facing contract is owned here;
`module.managed-runtime` supplies viewer provisioning under the Installation service's ownership.
Changes to viewer launch or graph admission select this service. Changes to runtime acquisition,
package verification or recovery select that Module through an admitted Domain routing view.
No graph or viewer action grants an agent access to another target's implementation.
