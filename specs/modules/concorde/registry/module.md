```concorde-document
{
  "id": "document.specs.modules.concorde.registry.module",
  "targets": [
    "module.registry"
  ],
  "main_visible": true
}
```

# Spec registry

Admit Module and Implementation identities, resolve document collections and look up exact file ownership and reuse.

## Features

### feature.registry.provide

Spec registry. SpecRepository reads registry schema 2. select returns a Module descriptor. Implementation records form a separate index, file_implementations maps each declared file to one owner, and implementation_users maps each Implementation Spec to all using Modules. Lookups never follow a relationship to read another Spec body.

## Interfaces

### api.registry.select

SpecRepository reads registry schema 2. select returns a Module descriptor. Implementation records form a separate index, file_implementations maps each declared file to one owner, and implementation_users maps each Implementation Spec to all using Modules. Lookups never follow a relationship to read another Spec body.

The [complete interface contract](interfaces.md) defines call shapes, values, effects and errors.

## Architecture

The [internal architecture](architecture.md) describes this Module's domain and the promises it relies on. The explicitly registered collection is complete; no dependency link imports another Module Spec.

## Implementation relationship

The registry identifies reusable Implementation Specs separately. Only a code-writing agent reads those Specs and bound files. Planning, task authoring and business decisions rely on this Module collection alone.
