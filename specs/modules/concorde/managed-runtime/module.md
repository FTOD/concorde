```concorde-document
{
  "id": "document.specs.modules.concorde.managed-runtime.module",
  "targets": [
    "module.managed-runtime"
  ],
  "main_visible": true
}
```

# Managed runtime

Provision and verify the pinned Python and viewer runtime used by installed integrations.

## Features

### feature.managed-runtime.provide

Managed runtime. load_runtime_spec reads locked requirements. plan_runtime describes provisioning state. provision_runtime stages versioned, hash-bound inputs and records verified receipts. A failed acquisition does not replace a previously valid runtime or accept a partial installation.

## Interfaces

### api.runtime.provision

load_runtime_spec reads locked requirements. plan_runtime describes provisioning state. provision_runtime stages versioned, hash-bound inputs and records verified receipts. A failed acquisition does not replace a previously valid runtime or accept a partial installation.

The [complete interface contract](interfaces.md) defines call shapes, values, effects and errors.

## Architecture

The [internal architecture](architecture.md) describes this Module's domain and the promises it relies on. The explicitly registered collection is complete; no dependency link imports another Module Spec.

## Implementation relationship

The registry identifies reusable Implementation Specs separately. Only a code-writing agent reads those Specs and bound files. Planning, task authoring and business decisions rely on this Module collection alone.
