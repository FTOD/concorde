```concorde-document
{
  "id": "document.specs.implementations.agent-definitions",
  "targets": [
    "implementation.agent-definitions"
  ],
  "main_visible": false
}
```

# Agent Definitions implementation

This Implementation Spec binds the exact files below. It is reused by `module.workflows`, `module.spec-context`.

## Responsibility

Route tasks and coordinate specification, planning, coding, review, topology changes and delivery. Resolve complete Module contracts, bind code-writing implementation context and validate explicit Spec structure. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `agents/code_reviewer/__init__.py`
- `agents/code_reviewer/spec.md`
- `agents/context_assessor/__init__.py`
- `agents/context_assessor/spec.md`
- `agents/coordinator/__init__.py`
- `agents/coordinator/spec.md`
- `agents/implementation_worker/__init__.py`
- `agents/implementation_worker/spec.md`
- `agents/planner/__init__.py`
- `agents/planner/spec.md`
- `agents/reader/__init__.py`
- `agents/reader/spec.md`
- `agents/spec_author/__init__.py`
- `agents/spec_author/spec.md`
- `agents/spec_reviewer/__init__.py`
- `agents/spec_reviewer/spec.md`
- `agents/task_author/__init__.py`
- `agents/task_author/spec.md`
- `tests/concorde/fixtures/build/golden/agents/code-reviewer.md`
- `tests/concorde/fixtures/build/golden/agents/context-assessor.md`
- `tests/concorde/fixtures/build/golden/agents/coordinator.md`
- `tests/concorde/fixtures/build/golden/agents/implementation-worker.md`
- `tests/concorde/fixtures/build/golden/agents/planner.md`
- `tests/concorde/fixtures/build/golden/agents/reader.md`
- `tests/concorde/fixtures/build/golden/agents/spec-author.md`
- `tests/concorde/fixtures/build/golden/agents/spec-reviewer.md`
- `tests/concorde/fixtures/build/golden/agents/task-author.md`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `agents/*/__init__.py` | Binds each Agent responsibility file to its Harness, capability references, data types and effects. |
| `agents/*/spec.md` | Defines executable Agent role instructions. These are implementation assets, not additional Module or Implementation Spec targets. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
