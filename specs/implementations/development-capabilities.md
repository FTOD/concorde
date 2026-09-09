```concorde-document
{
  "id": "document.implementation.development-capabilities",
  "targets": [
    "implementation.development-capabilities"
  ],
  "main_visible": false
}
```

# Development capabilities implementation

`implementation.development-capabilities` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.development`.

## Responsibility

Declare the Development Module's global, lifecycle and stage capability contracts, the installed Skills that expose its public entries, and the shared Skill prompt snippets.

## Bound files

- `capabilities/context_solve.py`
- `capabilities/deliver.py`
- `capabilities/dev_loop.py`
- `capabilities/implement.py`
- `capabilities/main.py`
- `capabilities/plan.py`
- `capabilities/review.py`
- `capabilities/specify.py`
- `capabilities/tasks.py`
- `capabilities/validate.py`
- `prompts/workflow-host/dev-loop-flags.md`
- `prompts/workflow-host/gap-reporting.md`
- `prompts/workflow-host/host-bound-invocation.md`
- `prompts/workflow-host/init-request-and-no-flags.md`
- `prompts/workflow-host/invoke-capability-opener.md`
- `prompts/workflow-host/lifecycle-no-cognition.md`
- `prompts/workflow-host/loop-completion-and-reviews.md`
- `prompts/workflow-host/loop-task-request-fields.md`
- `prompts/workflow-host/main-may-inspect.md`
- `prompts/workflow-host/review-scope-and-result.md`
- `prompts/workflow-host/stdin-invocation-config-input.md`
- `prompts/workflow-host/stdin-invocation-open.md`
- `prompts/workflow-host/target-identity-opener.md`
- `prompts/workflow-host/task-request-fields.md`
- `prompts/workflow-host/worktree-handoff.md`
- `skills/concorde-deliver/SKILL.md`
- `skills/concorde-dev-loop/SKILL.md`
- `skills/concorde-main/SKILL.md`
- `skills/concorde-validate/SKILL.md`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `capabilities/main.py`, `capabilities/dev_loop.py` | Global entries: questions, routing and topology; the development loop with its declared repair policy. |
| `capabilities/validate.py`, `capabilities/deliver.py` | Deterministic lifecycle entries for candidate evidence and delivery. |
| `capabilities/specify.py`, `capabilities/review.py`, `capabilities/context_solve.py`, `capabilities/plan.py`, `capabilities/tasks.py`, `capabilities/implement.py` | Private stage contracts reachable only through declared composition. |
| `skills/concorde-main/SKILL.md`, `skills/concorde-dev-loop/SKILL.md`, `skills/concorde-validate/SKILL.md`, `skills/concorde-deliver/SKILL.md` | Installed Skill sources for the public entries above. |
| `prompts/workflow-host/` | Shared `@include` snippets used by these Skills and by the init, configure and reflections-triage Skills owned elsewhere. |

## Implementation interfaces, dependencies and constraints

Each capability module declares its request and response types, effect ceiling, Agent references, composed entries and graph entry. Public Skills map only to declared global or lifecycle entries; stage modules are reachable through admitted host composition. Dependencies are the Development host, the Harness Agent definitions and the typed contract constructors. Graph edges preserve task and constraints, bind stage artifacts and propagate non-success instead of accepting missing output. The `init`, `configure` and `reflections-triage` capability modules are owned by the Spec, Distribution and Reflections realizations respectively; the capability inventory file itself belongs to the build.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Capability-module and structured-result cases cover unique registrations, supported public entry inventory, private-stage rejection, missing dependency or type declarations, incompatible handoffs and explicit review or authoring skips. Graph behavior must terminate on a gap or execution failure and respect the bounded repair policy.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
