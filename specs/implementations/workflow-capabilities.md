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

`implementation.workflow-capabilities` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.workflows`.

## Responsibility

Realize the public global/lifecycle adapters and private stage graphs as explicit capability declarations.

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

## Implementation interfaces, dependencies and constraints

Each capability module declares its request/response types, effect ceiling, Agent references, dependencies and graph entry. Public Skills map only to declared global/lifecycle entries; stage modules are reachable through admitted host composition. Dependencies are the workflow host, registered Agent definitions and typed contract constructors. Graph edges preserve task/constraints, bind stage artifacts and propagate non-success instead of accepting missing output. The initializer and authoring routes use inline Markdown Mermaid, retaining empty separate diagram arrays at the wire boundary.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Capability-module and structured-result cases cover unique registrations, supported public entry inventory, private-stage rejection, missing dependency/type declarations, incompatible handoffs and explicit review/authoring skips. Graph behavior must terminate on a gap or execution failure and respect bounded repair policy.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
