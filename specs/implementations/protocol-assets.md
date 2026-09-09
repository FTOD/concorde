```concorde-document
{
  "id": "document.implementation.protocol-assets",
  "targets": [
    "implementation.protocol-assets"
  ],
  "main_visible": false
}
```
# Protocol Assets implementation

`implementation.protocol-assets` follows Spec Protocol 2.1.0 and binds the exact files below. It is used by `module.distribution`.

## Responsibility

Adapt the independent specification standard into packaged rule assets while retaining a distinct Framework execution profile.

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
| `prompts/protocol/principles.md` | Includes the independent Protocol principles and the Framework execution profile. |
| `prompts/protocol/framework-profile.md` | Defines phase-specific context, impact checks, execution and delivery behavior. |
| `prompts/protocol/kinds/` | Includes the independent Module and Implementation chapters for runtime distribution. |
| `protocol/manifest.json` | Pins the exported rule version and exact generated asset digests. |

## Implementation interfaces, dependencies and constraints

The principles and kind adapters consume exact independent chapter/template inputs. The Framework profile adds runtime context, permission, review and delivery rules without redefining Protocol identity or membership. The manifest records accepted version and generated rule digests; it is a package compatibility asset, not a bound Protocol chapter. This revision requires the Framework authoring recommendation to use inline Mermaid and remove its old renderer-specific recipe; the independent Protocol remains unchanged. Implementation of that asset migration must rebuild projections and explicitly reconcile the accepted manifest binding.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Build and package checks must cover include provenance, exact principles/kind/template exports, manifest digest agreement and propagation of a changed Framework rule into both integrations. Reading the built rule bundle must expose the independent Protocol and the separate execution profile without making Protocol chapters project Specs.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
