```concorde-document
{
  "id": "document.specs.modules.concorde.registry.architecture",
  "targets": [
    "module.registry"
  ],
  "main_visible": true
}
```

# Architecture

SpecRepository reads registry schema 2. select returns a Module descriptor. Implementation records form a separate index, file_implementations maps each declared file to one owner, and implementation_users maps each Implementation Spec to all using Modules. Lookups never follow a relationship to read another Spec body.

## Internal domain

Admit Module and Implementation identities, resolve document collections and look up exact file ownership and reuse. Inputs, results, state/effects and failure behavior are defined in this collection's feature and interface contracts. Private implementation files are described separately by their authoritative Implementation Specs.

## Relied-upon Module promises

Each declaration below is local contract content. It grants no access to the provider's remaining Spec or implementation.

```concorde-dependencies
[
  {
    "target_id": "module.wire-contracts",
    "responsibility": "Admit versioned structured values, offline schemas and safe project paths.",
    "selection_condition": "Select when the task concerns wire contracts.",
    "relied_upon_promises": [
      "TypedValue envelopes identify a type, version and data. Unknown fields, unsupported identities and malformed values fail admission. File-path helpers reject traversal and aliases. Schema validation is deterministic and offline; a validation error never grants a different context or fallback authority."
    ]
  }
]
```
