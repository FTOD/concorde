```concorde-document
{
  "id": "document.specs.implementations.worktree-lifecycle",
  "targets": [
    "implementation.worktree-lifecycle"
  ],
  "main_visible": false
}
```

# Worktree Lifecycle implementation

This Implementation Spec binds the exact files below. It is reused by `module.workflows`, `module.installation`, `module.permissions`.

## Responsibility

Route tasks and coordinate specification, planning, coding, review, topology changes and delivery. Install, initialize, configure and upgrade Concorde while preserving user-owned content. Compile declared effects and host authority into reproducible execution permissions. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `src/concorde/host/change_worktree.py`
- `src/concorde/host/session_handoff.py`
- `src/concorde/host/worktree.py`
- `src/concorde/host/worktree_affinity.py`
- `src/concorde/host/worktree_delivery.py`
- `src/concorde/lifecycle/__init__.py`
- `src/concorde/lifecycle/delivery.py`
- `tests/concorde/host/unit/test_session_handoff.py`
- `tests/concorde/host/unit/test_worktree_affinity.py`
- `tests/concorde/host/unit/test_worktree_boundary.py`
- `tests/concorde/lifecycle/__init__.py`
- `tests/concorde/lifecycle/contract/__init__.py`
- `tests/concorde/lifecycle/integration/__init__.py`
- `tests/concorde/lifecycle/integration/test_implementation_delivery.py`
- `tests/concorde/specification/test_worktree_lifecycle.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/change_worktree.py` | Persists candidate identity, component progress, gaps and worktree inventory. |
| `src/concorde/host/worktree_delivery.py` | Checks actual integration and coordinates destination updates and cleanup. |
| `src/concorde/host/worktree.py` | Inspects the current Git worktree identity and applies the declared isolation requirement. |
| `src/concorde/host/session_handoff.py` | Builds complete localized handoff information for a required new session. |
| `src/concorde/host/worktree_affinity.py` | Checks source-checkout instruction ownership without treating equal bytes as shared worktree identity. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

Worktree identity inspection, candidate state, session handoffs and delivery share these files. Workflows, Installation and Permissions use the same binding. Any change must check all three Module views; one consumer's passing result is not enough.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
