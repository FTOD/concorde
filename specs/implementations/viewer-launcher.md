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

This Implementation Spec binds the exact files below. It is reused by `module.viewer`.

## Responsibility

Open an existing Understand Anything code graph with the verified installed viewer. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `scripts/run-viewer.py`
- `tests/concorde/distribution/unit/test_viewer_launcher.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `scripts/run-viewer.py` | Admits an existing raw graph and verified runtime, launches the official viewer and returns its process outcome without installing or rewriting project data. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
