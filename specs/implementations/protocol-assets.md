```concorde-document
{
  "id": "document.specs.implementations.protocol-assets",
  "targets": [
    "implementation.protocol-assets"
  ],
  "main_visible": false
}
```

# Protocol Assets implementation

This Implementation Spec binds the exact files below. It is reused by `module.protocol`.

## Responsibility

Define the Module/Implementation specification standard and evolve its explicitly bound revision. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `prompts/protocol/framework-profile.md`
- `prompts/protocol/kinds/implementation.md`
- `prompts/protocol/kinds/module.md`
- `prompts/protocol/principles.md`
- `protocol/manifest.json`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `prompts/protocol/principles.md` | Defines the Module, internal domain and reusable Implementation Spec semantics. |
| `prompts/protocol/framework-profile.md` | Defines phase-specific context, impact checks, execution and delivery behavior. |
| `prompts/protocol/kinds/` | Supplies the separate Module and Implementation instruction definitions. |
| `protocol/manifest.json` | Pins the exported rule version and exact generated asset digests. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
