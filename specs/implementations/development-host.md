```concorde-document
{
  "id": "document.implementation.development-host",
  "targets": [
    "implementation.development-host"
  ],
  "main_visible": false
}
```

# Development host implementation

`implementation.development-host` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.development`.

## Responsibility

Realize capability admission and dispatch, the global discovery loop, the development graph with its bounded repair edge, topology preparation and application, review evidence and candidate readiness.

## Bound files

- `src/concorde/host/__init__.py`
- `src/concorde/host/capability_host.py`
- `src/concorde/host/capability_service.py`
- `src/concorde/host/configuration.py`
- `src/concorde/host/review.py`
- `tests/concorde/host/__init__.py`
- `tests/concorde/host/acceptance/__init__.py`
- `tests/concorde/host/contract/__init__.py`
- `tests/concorde/host/contract/test_structured_results.py`
- `tests/concorde/host/integration/__init__.py`
- `tests/concorde/host/unit/__init__.py`
- `tests/concorde/host/unit/test_capability_modules.py`
- `tests/concorde/host/unit/test_run_capability.py`
- `tests/concorde/specification/test_review.py`
- `tests/concorde/support/operation_json.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/capability_host.py` | Routes and binds Module tasks, runs the coordinator over resolved discovery contexts, composes stage graphs, prepares and applies topology, admits implementation documents only for writers, and checks all shared implementation users. |
| `src/concorde/host/capability_service.py` | Admits schema-3 invocations and dispatches the named entry. |
| `src/concorde/host/review.py` | Runs separate read-only Module contract reviews and stores version-bound per-consumer evidence. |
| `src/concorde/host/configuration.py` | Loads and validates integration settings without treating caller configuration as authority. |
| `tests/concorde/host/` contract and unit suites, `tests/concorde/specification/test_review.py`, `tests/concorde/support/operation_json.py` | Exercise structured results, routing versus grants, review gates and repair with explicit process doubles. |

## Implementation interfaces, dependencies and constraints

The capability service and CLI accept schema-3 invocations and dispatch the admitted entry; the host binds Module contexts, Agent bindings, permissions and stage results, records candidate progress in the worktree lifecycle and stores review artifacts. Dependencies are the Harness services for context, binding, permissions and execution, the Spec registry and validator, the file-transaction helper, the build freshness check and the worktree lifecycle.

Two boundaries recorded by the Module Specs are not yet realized in code. `capability_host.py` still contains the invocation-binding mechanics that the Harness Module specifies in its host document, namely the freeze, compile, render, launch, execute and validate sequence of `Invocation.stage` and `MainInvocation.stage`; extracting them into a Harness-owned realization is pending. Only the development loop is a LangGraph `StateGraph`; the discovery loop, topology flow, lifecycle capabilities and the reflections composition still run as plain Python control flow and must move onto `StateGraph` composition to satisfy the Harness Module's control-flow requirement.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Host, structured-result and scoped-protocol tests cover routing hints versus grants, stage output identity, stale task or context, authoring authority, implementation-only writes, shared-consumer finalization, bounded review repairs and readiness gates.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
