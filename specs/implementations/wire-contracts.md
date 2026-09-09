```concorde-document
{
  "id": "document.specs.implementations.wire-contracts",
  "targets": [
    "implementation.wire-contracts"
  ],
  "main_visible": false
}
```

# Wire Contracts implementation

This Implementation Spec binds the exact files below. It is reused by `module.wire-contracts`.

## Responsibility

Admit versioned structured values, offline schemas and safe project paths. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `src/concorde/host/contract_shapes.py`
- `src/concorde/host/contracts.py`
- `src/concorde/host/typed_data.py`
- `src/concorde/host/wire_shapes.py`
- `src/concorde/specification/schema.py`
- `tests/concorde/host/unit/test_typed_data.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/contracts.py` | Declares Module/Implementation registry, context, review and topology value shapes. |
| `src/concorde/host/contract_shapes.py` | Provides common capability request/result shapes without importing capability modules. |
| `src/concorde/host/typed_data.py` | Admits typed envelopes, canonical JSON, artifact identity and safe project paths. |
| `src/concorde/host/wire_shapes.py` | Defines reusable primitive schema constructors and typed references. |
| `src/concorde/specification/schema.py` | Checks the supported offline schema subset and example values without remote references. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
