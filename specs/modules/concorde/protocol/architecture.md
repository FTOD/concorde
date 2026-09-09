```concorde-document
{
  "id": "document.specs.modules.concorde.protocol.architecture",
  "targets": [
    "module.protocol"
  ],
  "main_visible": true
}
```

# Architecture

Consumers exchange registered Markdown Specs and registry schema 2. A project accepts Protocol 2.0.0 by version and digest. Module Specs describe observable features, usage interfaces and internal domains. Implementation Specs bind reusable realizations to exact files.

## Internal domain

Define the Module/Implementation specification standard and evolve its explicitly bound revision. Inputs, results, state/effects and failure behavior are defined in this collection's feature and interface contracts. Private implementation files are described separately by their authoritative Implementation Specs.

## Dependencies

No internal Module dependency is required by this boundary. External inputs and interfaces are specified locally.
