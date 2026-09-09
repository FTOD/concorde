```concorde-document
{
  "id": "document.specs.implementations.managed-runtime",
  "targets": [
    "implementation.managed-runtime"
  ],
  "main_visible": false
}
```

# Managed Runtime implementation

This Implementation Spec binds the exact files below. It is reused by `module.managed-runtime`.

## Responsibility

Provision and verify the pinned Python and viewer runtime used by installed integrations. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `src/concorde/distribution/managed_runtime.py`
- `tests/concorde/support/managed_runtime.py`
- `viewer/README.md`
- `viewer/package-lock.json`
- `viewer/package.json`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/distribution/managed_runtime.py` | Plans, stages and verifies the locked Python and viewer runtimes with recoverable receipts. |
| `viewer/` | Pins the official viewer package input independently of graph content. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
