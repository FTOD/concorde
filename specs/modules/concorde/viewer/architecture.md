```concorde-document
{
  "id": "document.specs.modules.concorde.viewer.architecture",
  "targets": [
    "module.viewer"
  ],
  "main_visible": true
}
```

# Architecture

scripts/run-viewer.py accepts a project root, optional port and no-open flag. It checks the ordered raw graph inputs and runtime identity, then launches the official viewer and returns its exit code. It does not generate the graph, install dependencies or establish that code agrees with its Spec.

## Internal domain

Open an existing Understand Anything code graph with the verified installed viewer. Inputs, results, state/effects and failure behavior are defined in this collection's feature and interface contracts. Private implementation files are described separately by their authoritative Implementation Specs.

## Relied-upon Module promises

Each declaration below is local contract content. It grants no access to the provider's remaining Spec or implementation.

```concorde-dependencies
[
  {
    "target_id": "module.managed-runtime",
    "responsibility": "Provision and verify the pinned Python and viewer runtime used by installed integrations.",
    "selection_condition": "Select when the task concerns managed runtime.",
    "relied_upon_promises": [
      "load_runtime_spec reads locked requirements. plan_runtime describes provisioning state. provision_runtime stages versioned, hash-bound inputs and records verified receipts. A failed acquisition does not replace a previously valid runtime or accept a partial installation."
    ]
  }
]
```
