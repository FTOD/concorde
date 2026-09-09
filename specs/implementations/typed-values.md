```concorde-document
{
  "id": "document.implementation.typed-values",
  "targets": [
    "implementation.typed-values"
  ],
  "main_visible": false
}
```

# Typed values implementation

`implementation.typed-values` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.spec`, `module.harness`.

## Responsibility

Realize versioned value schemas, canonical encoding, artifact references, safe project paths, the offline interface-schema evaluator and the constrained front-matter parser that every boundary of the Framework uses.

## Bound files

- `src/concorde/frontmatter.py`
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
| `src/concorde/host/typed_data.py` | Admits typed envelopes, canonical JSON, artifact identity and safe project paths. |
| `src/concorde/host/wire_shapes.py` | Defines reusable primitive schema constructors and typed references. |
| `src/concorde/host/contract_shapes.py` | Provides common capability request and result shapes without importing capability modules. |
| `src/concorde/host/contracts.py` | Declares the closed catalog of registry, context, review, topology and stage value shapes and exports their identities. |
| `src/concorde/specification/schema.py` | Checks the supported offline schema subset and example values without remote references. |
| `src/concorde/frontmatter.py` | Parses the constrained YAML front matter of Skills, Agent Specs, Reflection records and Spec documents. |

## Implementation interfaces, dependencies and constraints

`typed`, `validate_typed`, `json_schema`, `decode`, `canonical`, `artifact`, `verify_artifacts`, `safe_path` and `checked_path` are the public helpers; `admit` and `validate` form the schema evaluator; `parse_document` parses front matter. The schema evaluator admits only its documented offline vocabulary and local definitions. Dependencies are standard JSON, hashing, regex and filesystem primitives. Canonical JSON encodes stable bytes but is separate from TypedValue and business validation. The type catalog in `contracts.py` is cross-cutting by design: every capability declares its own request and response shapes, while internal handoff, review and topology types are declared once here.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Typed-data and schema cases cover wrong type or version, duplicate keys, non-finite numbers, unknown fields, safe-path aliases, stale artifact bytes, local versus remote references and schema or example mismatch. Exported schema validation and contextual value admission need separate assertions because JSON schema export omits internal path and context rules.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
