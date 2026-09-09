```concorde-document
{
  "id": "document.specs.implementations.workflow-capabilities",
  "targets": [
    "implementation.workflow-capabilities"
  ],
  "main_visible": false
}
```

# Workflow Capabilities implementation

This Implementation Spec binds the exact files below. It is reused by `module.workflows`.

## Responsibility

Route tasks and coordinate specification, planning, coding, review, topology changes and delivery. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `capabilities/configure.py`
- `capabilities/context_solve.py`
- `capabilities/deliver.py`
- `capabilities/dev_loop.py`
- `capabilities/implement.py`
- `capabilities/init.py`
- `capabilities/main.py`
- `capabilities/plan.py`
- `capabilities/reflections_triage.py`
- `capabilities/review.py`
- `capabilities/specify.py`
- `capabilities/tasks.py`
- `capabilities/validate.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `capabilities/` | Declares global, lifecycle and internal-stage contracts and graph composition. These callable adapters do not create additional project Spec kinds. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
