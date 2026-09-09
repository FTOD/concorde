```concorde-document
{
  "id": "document.implementation.agent-execution",
  "targets": [
    "implementation.agent-execution"
  ],
  "main_visible": false
}
```
# Agent Execution implementation

`implementation.agent-execution` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.harness`.

## Responsibility

Realize single native launches, explicit recursive scheduling and typed completion admission using separate execution and Harness primitives.

## Bound files

- `src/concorde/host/agent_executor.py`
- `src/concorde/host/agent_runtime.py`
- `src/concorde/host/native_agent.py`
- `tests/concorde/host/unit/test_agent_executor.py`
- `tests/concorde/host/unit/test_agent_runtime.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/agent_executor.py` | Verifies native launch bindings and completion envelopes around a synchronous model process. |
| `src/concorde/host/agent_runtime.py` | Controls recursive invocations, feedback, cancellation and shared limits. |
| `src/concorde/host/native_agent.py` | Adapts a bound Agent loop to the selected native model integration. |

## Implementation interfaces, dependencies and constraints

AgentProcessExecutor consumes a LaunchSpecification and produces completion plus receipt or a classified execution failure. AgentRuntime uses immutable nodes, grants and frames; NativeAgentAdapter converts each model-driven decision through the same executor. Dependencies are the permission compiler/finalizer, typed-value admission and package binding resolution. Each child gets a fresh invocation/context, cumulative feedback contains only direct typed returns, and shared limits cannot reset. Callback injection is trusted host configuration with an explicit identity; callbacks must honor the remaining deadline.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Exercise launch/context/policy/receipt mismatches, nonzero exit, malformed completion, timeout and cancellation in the executor tests. Runtime tests cover A-to-B-to-C and self-edges, denied delegation before resolution, stale context, shared budgets and cancellation propagation. Process doubles establish boundary mechanics, not model semantic quality.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
