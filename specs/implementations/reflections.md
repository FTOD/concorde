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

This Implementation Spec binds the exact files below. It is reused by `module.reflections`.

## Responsibility

Retain, investigate and resolve explicitly attributed project feedback and persistent gaps. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

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

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
