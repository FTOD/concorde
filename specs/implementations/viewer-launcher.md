```concorde-document
{
  "id": "document.specs.implementations.viewer-launcher",
  "targets": [
    "implementation.viewer-launcher"
  ],
  "main_visible": false
}
```

# Viewer Launcher implementation

`implementation.viewer-launcher` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.viewer`.

## Responsibility

Realize the deterministic admission and process launch boundary for the existing raw graph viewer.

## Bound files

- `scripts/run-viewer.py`
- `tests/concorde/distribution/unit/test_viewer_launcher.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `scripts/run-viewer.py` | Admits an existing raw graph and verified runtime, launches the official viewer and returns its process outcome without installing or rewriting project data. |

## Implementation interfaces, dependencies and constraints

The launcher parses project/port/no-open options, reads the installed manifest/receipt, selects the first existing raw graph and launches the pinned viewer entrypoint. Dependencies are the installed official viewer, Node runtime and safe filesystem/process operations. It does not create graphs or provision dependencies. The first existing graph is authoritative for admission; an invalid file cannot select a later path. Child flags and working directory follow the request, and exit/interruption/preflight failures preserve their distinct status contract.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Viewer-launcher tests cover ordered selection, invalid first graph, symlinks, missing or mismatched runtime, port bounds, child arguments/cwd, propagated exit codes and interruption. Mock launch success must not be described as proof that graph contents match current source.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
