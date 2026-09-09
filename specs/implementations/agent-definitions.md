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

`implementation.agent-definitions` follows Spec Protocol 2.0.0 and binds the exact files below. It is reused by `module.workflows`, `module.spec-context`.

## Responsibility

Bind each named runtime responsibility asset to a canonical Python Agent record; supply the same definitions to workflow stages.

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
- `tests/concorde/fixtures/build/golden/agents/spec-author.md`
- `tests/concorde/fixtures/build/golden/agents/spec-reviewer.md`
- `tests/concorde/fixtures/build/golden/agents/task-author.md`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `agents/*/__init__.py` | Binds each Agent responsibility file to its Harness, capability references, data types and effects. |
| `agents/*/spec.md` | Defines executable Agent role instructions. These are implementation assets, not additional Module or Implementation Spec targets. |

## Implementation interfaces, dependencies and constraints

Agent definitions expose catalog records. They depend on the host Agent/Harness primitives, typed context/result contracts, and current rendered assets. A definition binds its authored spec.md, effective effects, context/result type IDs, capability references and loop limits. The coordinator consumes deterministically resolved complete source contexts and answers directly. Golden prompt files are expected build outputs used as test inputs, not additional authored rules.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Check catalog uniqueness, missing Spec/Harness rejection, context/result compatibility, direct coordinator answers and explicit recursive edges in the generic execution runtime. Build fixtures must show that changes to responsibilities alter the expected rendered body without admitting unrelated instructions; golden-byte equality alone does not prove role behavior.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
