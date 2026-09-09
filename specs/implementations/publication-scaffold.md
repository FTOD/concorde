```concorde-document
{
  "id": "document.specs.implementations.publication-scaffold",
  "targets": [
    "implementation.publication-scaffold"
  ],
  "main_visible": false
}
```

# Publication Scaffold implementation

This Implementation Spec binds the exact files below. It is reused by `module.publication`.

## Responsibility

Create navigable documentation and diagrams from registered Module and Implementation Specs. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `src/concorde/autodocs/__init__.py`
- `src/concorde/autodocs/docsite_scaffold.py`
- `src/concorde/autodocs/docsite_template.py`
- `tests/concorde/autodocs/__init__.py`
- `tests/concorde/autodocs/integration/__init__.py`
- `tests/concorde/autodocs/integration/test_docsite_scaffold.py`
- `tests/concorde/autodocs/unit/__init__.py`
- `tests/concorde/autodocs/unit/test_docsite_template.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/autodocs/` | Produces exact docsite scaffold proposals and deploys the current Module/Implementation publishing template without reading code to infer architecture. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
