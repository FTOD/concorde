```concorde-document
{
  "id": "document.specs.implementations.workflow-host",
  "targets": [
    "implementation.workflow-host"
  ],
  "main_visible": false
}
```

# Workflow Host implementation

This Implementation Spec binds the exact files below. It is reused by `module.workflows`.

## Responsibility

Route tasks and coordinate specification, planning, coding, review, topology changes and delivery. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `scripts/development/STUDIO.md`
- `scripts/development/studio.py`
- `src/concorde/host/__init__.py`
- `src/concorde/host/agent_model.py`
- `src/concorde/host/capability_host.py`
- `src/concorde/host/capability_service.py`
- `src/concorde/host/cli.py`
- `src/concorde/host/configuration.py`
- `src/concorde/host/review.py`
- `src/concorde/host/roles.py`
- `src/concorde/host/studio.py`
- `src/concorde/host/studio_client.py`
- `tests/concorde/host/__init__.py`
- `tests/concorde/host/acceptance/__init__.py`
- `tests/concorde/host/contract/__init__.py`
- `tests/concorde/host/contract/test_structured_results.py`
- `tests/concorde/host/integration/__init__.py`
- `tests/concorde/host/integration/test_studio_server.py`
- `tests/concorde/host/unit/__init__.py`
- `tests/concorde/host/unit/test_agent_model.py`
- `tests/concorde/host/unit/test_capability_modules.py`
- `tests/concorde/host/unit/test_run_capability.py`
- `tests/concorde/host/unit/test_studio.py`
- `tests/concorde/host/unit/test_studio_client.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/capability_host.py` | Routes and binds Module tasks, admits implementation documents only for writers, applies proposals and checks all shared implementation users. |
| `src/concorde/host/review.py` | Runs separate read-only Module contract reviews and stores version-bound per-consumer evidence. |
| `src/concorde/host/agent_model.py` | Resolves responsibility instructions, Harness definitions, capabilities and effective limits into Agent bindings. |
| `src/concorde/host/configuration.py` | Loads and validates integration settings without treating caller configuration as authority. |
| `src/concorde/host/studio.py` | Presents execution state and forwards explicit requests through the same host interfaces. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

The host resolves stage context, enforces phase-specific grants, preserves task constraints and records exact stage evidence. Implementation digests include Implementation Spec documents and bindings. Checks and code reviews expand shared implementation impact as separate Module invocations, never as one combined Spec context.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
