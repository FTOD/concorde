```concorde-document
{
  "id": "document.specs.implementations.permissions",
  "targets": [
    "implementation.permissions"
  ],
  "main_visible": false
}
```

# Permissions implementation

This Implementation Spec binds the exact files below. It is reused by `module.permissions`.

## Responsibility

Compile declared effects and host authority into reproducible execution permissions. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `src/concorde/host/permissions.py`
- `tests/concorde/host/unit/test_permissions.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/permissions.py` | Intersects effects with exact host-provided paths and renders reproducible native enforcement. Implementation Spec documents are writable only in a code-writing grant; Module Specs are excluded. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
