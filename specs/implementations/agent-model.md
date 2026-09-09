```concorde-document
{
  "id": "document.implementation.agent-model",
  "targets": [
    "implementation.agent-model"
  ],
  "main_visible": false
}
```

# Agent and Harness model implementation

`implementation.agent-model` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.harness`.

## Responsibility

Realize `Agent = spec.md + Harness + Constraints` as frozen Python records, the closed Harness catalog, the effect-declaration vocabulary and the reproducible `AgentBinding` resolved against the current build.

## Bound files

- `src/concorde/host/agent_model.py`
- `src/concorde/host/effects.py`
- `src/concorde/host/harness.py`
- `src/concorde/host/roles.py`
- `tests/concorde/host/unit/test_agent_model.py`
- `tests/concorde/specification/test_agent_binding.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/harness.py` | Defines `Harness`, `LoopPolicy` and the three registered Harnesses with deterministic digests; imports only effects and the standard library. |
| `src/concorde/host/effects.py` | Defines `EffectDeclaration`, the maximum-authority vocabulary shared by Harnesses, Agents and the permission compiler. |
| `src/concorde/host/agent_model.py` | Defines `Agent`, `Constraints` and `AgentBinding`; loads the `agents/` inventory; `resolve_agent` verifies Spec digest, build manifest, registered Harness, capability and type references and narrowed effects and limits. |
| `src/concorde/host/roles.py` | Derived read-only projection of the Agent inventory onto the former `Role` shape for compatibility importers. |
| `tests/concorde/host/unit/test_agent_model.py`, `tests/concorde/specification/test_agent_binding.py` | Exercise binding resolution, digests, widening rejection and stale builds. |

## Implementation interfaces, dependencies and constraints

`harness(...)` normalizes unique tuple fields and hashes the complete configuration except its own digest; `resolve_agent` fails closed with `BuildError` codes `stale_build`, `unknown_agent` and `invalid_agent_binding`. Dependencies are the build manifest and rendered instructions produced by the Distribution build, and the exported type identities of the typed-value contracts. `agent_model` never imports `build` at module scope to avoid an import cycle with `roles`.

The `Harness.skills` tuple remains in the record shape and is empty for every registered Harness. The Harness Module no longer admits Skills into a Harness, so removing that field and its digest participation is pending implementation work; it changes every Harness digest and therefore every Agent binding, which requires a rebuild and fresh admission.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Check catalog uniqueness, missing Spec or Harness rejection, context/result subset checks, effect widening rejection, effective loop narrowing, binding digest stability and stale-build refusal.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
