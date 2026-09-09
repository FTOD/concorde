```concorde-document
{
  "id": "document.concorde.spec-protocol",
  "targets": [
    "module.protocol"
  ],
  "main_visible": true
}
```

# Spec Protocol

Define the Module/Implementation specification standard and evolve its explicitly bound revision.

## Features

### feature.concorde.evolve-protocol

Evolve the Spec Protocol. Consumers exchange registered Markdown Specs and registry schema 2. A project accepts Protocol 2.0.0 by version and digest. Module Specs describe observable features, usage interfaces and internal domains. Implementation Specs bind reusable realizations to exact files.

### feature.protocol.describe-model

Describe Module and Implementation Specs. Consumers exchange registered Markdown Specs and registry schema 2. A project accepts Protocol 2.0.0 by version and digest. Module Specs describe observable features, usage interfaces and internal domains. Implementation Specs bind reusable realizations to exact files.

## Interfaces

### interface.protocol.use

Consumers exchange registered Markdown Specs and registry schema 2. A project accepts Protocol 2.0.0 by version and digest. Module Specs describe observable features, usage interfaces and internal domains. Implementation Specs bind reusable realizations to exact files.

## Architecture

The [internal architecture](architecture.md) describes this Module's domain and the promises it relies on. The explicitly registered collection is complete; no dependency link imports another Module Spec.

## Implementation relationship

The registry identifies reusable Implementation Specs separately. Only a code-writing agent reads those Specs and bound files. Planning, task authoring and business decisions rely on this Module collection alone.
