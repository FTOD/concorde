```concorde-document
{
  "id": "document.implementation.studio",
  "targets": [
    "implementation.studio"
  ],
  "main_visible": false
}
```

# Studio implementation

`implementation.studio` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.harness`.

## Responsibility

Realize the LangGraph Studio adapter that exposes Concorde's capabilities as graphs over the same `CapabilityHost`, typed request validation and permission checks that CLI and Skill invocations use.

## Bound files

- `scripts/development/STUDIO.md`
- `scripts/development/studio.py`
- `src/concorde/host/studio.py`
- `src/concorde/host/studio_client.py`
- `tests/concorde/host/integration/test_studio_server.py`
- `tests/concorde/host/unit/test_studio.py`
- `tests/concorde/host/unit/test_studio_client.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/studio.py` | Builds one Studio graph per public capability bound to server-owned project and package roots; streams admission, policy and stage events. |
| `src/concorde/host/studio_client.py` | Submits invocations to a running Studio server and returns the unchanged result envelope. |
| `scripts/development/studio.py`, `scripts/development/STUDIO.md` | Source-checkout entry module named by `generated/langgraph.json` and its setup and debugging guide. |
| `tests/concorde/host/unit/test_studio.py`, `tests/concorde/host/unit/test_studio_client.py`, `tests/concorde/host/integration/test_studio_server.py` | Exercise workspace binding, replay, event capture and transport failures. |

## Implementation interfaces, dependencies and constraints

`build_studio_graph(capability, project_root, package_root, *, executor=None)` accepts only public capability names, rechecks the invocation on every run including resumed checkpoints, and forwards execution through `run_capability`. Dependencies are the Development host, typed-value decoding and the native executor. Requests cannot supply hosts, roots or permissions; replay does not waive effect preconditions.

Each Studio graph is currently a two-node validate and execute wrapper around `run_capability`; the real control flow of most capabilities runs inside the host as Python calls, and only the development loop is itself a `StateGraph`. The Harness Module requires every capability's control flow to be a LangGraph graph that Studio exposes directly. Migrating the discovery loop, topology flow, reflection triage, lifecycle capabilities and the recursive `AgentRuntime` onto `StateGraph` composition, and pointing `generated/langgraph.json` at those graphs, is pending implementation work.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Studio tests must verify that observations and replay preserve the normal invocation, permission and workspace contract, that a different workspace is rejected, and that events never become model input.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
