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

`implementation.workflow-host` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.workflows`.

## Responsibility

Realize capability admission, routing, stage binding, evidence persistence and development/readiness coordination.

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

## Implementation interfaces, dependencies and constraints

The capability service/CLI accept schema-3 invocations and dispatch the admitted entry; the host binds Module contexts, Agent definitions, permissions and stage results. Review runs in fresh read-only contexts and records input-bound findings. Dependencies are repository/context services, typed contracts, execution, permission and build services, plus candidate lifecycle state. A shared implementation change expands impact through the reverse index but creates separate consumer checks rather than a combined cognitive context. Studio uses the same host and result envelope; replay does not waive effect preconditions.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Host, structured-result and scoped-protocol tests cover routing hints versus grants, stage output identity, stale task/context, authoring authority, implementation-only writes, shared-consumer finalization and bounded review repairs. Studio tests verify that observations and replay preserve the normal invocation and workspace contract.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
