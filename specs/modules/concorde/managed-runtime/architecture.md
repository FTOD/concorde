```concorde-document
{
  "id": "document.specs.modules.concorde.managed-runtime.architecture",
  "targets": [
    "module.managed-runtime"
  ],
  "main_visible": true
}
```

# Architecture

load_runtime_spec reads locked requirements. plan_runtime describes provisioning state. provision_runtime stages versioned, hash-bound inputs and records verified receipts. A failed acquisition does not replace a previously valid runtime or accept a partial installation.

## Internal domain

Provision and verify the pinned Python and viewer runtime used by installed integrations. Inputs, results, state/effects and failure behavior are defined in this collection's feature and interface contracts. Private implementation files are described separately by their authoritative Implementation Specs.

## Dependencies

No internal Module dependency is required by this boundary. External inputs and interfaces are specified locally.
