```concorde-document
{
  "id": "document.specs.implementations.registry",
  "targets": [
    "implementation.registry"
  ],
  "main_visible": false
}
```

# Registry implementation

This Implementation Spec binds the exact files below. It is reused by `module.registry`.

## Responsibility

Admit Module and Implementation identities, resolve document collections and look up exact file ownership and reuse. The implementation realizes these Module contracts through the interfaces and internal responsibilities stated here; missing product behavior must be resolved in the Module Spec.

## Bound files

- `src/concorde/specification/repository.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/specification/repository.py` | Separately indexes Module and Implementation descriptors, explicit documents, unique file owners and reverse users. Module selection never follows an implementation reference to read its body. |

## Implementation contract

Preserve the public inputs, results, effects and errors of the using Modules. Keep file ownership unique and use explicit dependency interfaces. Source files implement behavior; tests exercise that behavior and authored runtime assets configure its execution. Maintain this Spec when internal responsibilities change, without silently changing a Module contract.

The repository stores Module and Implementation descriptors separately, rejects duplicate file owners and derives reverse usage. Module document lookup never follows uses or implementation references. File grants are explicit, including pending files, and never broaden by recursively scanning a directory.

## Verification and shared changes

Run the relevant unit and integration tests for the changed interfaces. The Framework derives every using Module from the registry and checks its contract independently. Changes to any file, this Spec or the binding invalidate affected implementation evidence. Do not edit another Module Spec through this implementation grant.
