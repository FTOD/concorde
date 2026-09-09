```concorde-document
{
  "id": "document.specs.implementations.reflections",
  "targets": [
    "implementation.reflections"
  ],
  "main_visible": false
}
```

# Reflections implementation

`implementation.reflections` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.reflections`.

## Responsibility

Realize report parsing, monotonic allocation, exact selection and evidence-bound triage state changes.

## Bound files

- `scripts/reflections_queue.py`
- `src/concorde/reflections/__init__.py`
- `src/concorde/reflections/config.default.json`
- `src/concorde/reflections/configuration.py`
- `src/concorde/reflections/investigation.py`
- `src/concorde/reflections/reflections.py`
- `src/concorde/reflections/scoped_triage.py`
- `src/concorde/reflections/validation.py`
- `tests/concorde/reflections/__init__.py`
- `tests/concorde/reflections/contract/__init__.py`
- `tests/concorde/reflections/integration/__init__.py`
- `tests/concorde/reflections/unit/__init__.py`
- `tests/concorde/reflections/unit/test_reflection_parser.py`
- `tests/concorde/reflections/unit/test_reflection_rules.py`
- `tests/concorde/reflections/unit/test_reflections_queue.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/reflections/` | Parses records, selects Module-local work, retains evidence and translates verified intended behavior into tasks. |
| `scripts/reflections_queue.py` | Maintains queue identity, indexes and lifecycle records. Evidence remains historical when Module attribution changes. |

## Implementation interfaces, dependencies and constraints

The parser separates immutable observation/comments from triage findings and human disposition. Queue storage uses index and bucket records; scoped_triage resolves current Module attribution, and investigation binds selected record digests and HEAD before creating a plan. Dependencies are registry identity/focus lookup, context selection and workflow composition for implementation. The record-gaps path deduplicates links to existing change history and uses the Module’s unique module.md for entry provenance. Retrying an already captured gap reuses its Reflection ID; approval does not survive a changed resolution.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Parser/queue cases cover bucket/status disagreement, monotonic IDs, preserved comments, foreign selection and explicit disposition. Scope/triage cases cover stale HEAD or record bytes, missing approval, repeated gap capture and unchanged source-gap history. No pure status or assessment case may allocate a report.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
