```concorde-document
{
  "id": "document.specs.implementations.agent-execution",
  "targets": [
    "implementation.agent-execution"
  ],
  "main_visible": false
}
```

# Agent Execution implementation

This Implementation Spec binds the exact files below. It is reused by `module.agent-execution`.

## Responsibility

Execute separately bound Agent invocations through their Harness and admit typed results. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `src/concorde/host/agent_executor.py`
- `src/concorde/host/agent_runtime.py`
- `src/concorde/host/harness.py`
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
| `src/concorde/host/harness.py` | Defines the resources and compatibility contracts available to an invocation. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
