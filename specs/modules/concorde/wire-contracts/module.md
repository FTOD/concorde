```concorde-document
{
  "id": "document.specs.modules.concorde.wire-contracts.module",
  "targets": [
    "module.wire-contracts"
  ],
  "main_visible": true
}
```

# Wire contracts

Admit versioned structured values, offline schemas and safe project paths.

## Features

### feature.wire-contracts.provide

Wire contracts. TypedValue envelopes identify a type, version and data. Unknown fields, unsupported identities and malformed values fail admission. File-path helpers reject traversal and aliases. Schema validation is deterministic and offline; a validation error never grants a different context or fallback authority.

## Interfaces

### api.wire.validate

TypedValue envelopes identify a type, version and data. Unknown fields, unsupported identities and malformed values fail admission. File-path helpers reject traversal and aliases. Schema validation is deterministic and offline; a validation error never grants a different context or fallback authority.

The [complete interface contract](interfaces.md) defines call shapes, values, effects and errors.

## Architecture

The [internal architecture](architecture.md) describes this Module's domain and the promises it relies on. The explicitly registered collection is complete; no dependency link imports another Module Spec.

## Implementation relationship

The registry identifies reusable Implementation Specs separately. Only a code-writing agent reads those Specs and bound files. Planning, task authoring and business decisions rely on this Module collection alone.
