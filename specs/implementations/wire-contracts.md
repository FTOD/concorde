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

`implementation.wire-contracts` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.wire-contracts`.

## Responsibility

Realize versioned value schemas, canonical encoding, safe paths and the supported offline interface-schema evaluator.

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

## Implementation interfaces, dependencies and constraints

contracts and contract_shapes declare the closed transport records; wire_shapes supplies reusable constructors; typed_data constructs/validates values and artifact references. The schema evaluator admits only its documented offline vocabulary and local definitions. Dependencies are standard JSON, hashing, regex and filesystem primitives. Canonical JSON encodes stable bytes but is separate from TypedValue and business validation. Snapshot diagram fields remain compatible empty arrays for inline Markdown diagrams; legacy external diagram fields cannot authorize paths or imply new membership.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Typed-data/schema cases cover wrong type/version, duplicate keys, non-finite numbers, unknown fields, safe-path aliases, stale artifact bytes, local versus remote references and schema/example mismatch. Exported schema validation and contextual value admission need separate assertions because JSON schema export omits internal path/context rules.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
