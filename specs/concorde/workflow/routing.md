```concorde-document
{
  "id": "document.workflow.routing",
  "targets": [
    "domain.workflow"
  ],
  "main_visible": true
}
```

# Main routing for Agent orchestration


The main coordinator may expand this Domain after `domain.concorde` identifies an Agent orchestration task. It
selects `service.spec-context` for target registration, Protocol binding, context resolution and
Spec structural validation; `service.workflow-host` for Agent and Harness binding, capability
admission, Graph routing, AI/human feedback transitions and lifecycle state; and `service.reflections` for Reflection selection,
investigation or disposition. It selects `module.registry` for the in-process registry API,
`module.wire-contracts` for TypedValue/schema validation, `module.file-transactions` for atomic file
replacement, `module.agent-execution` for Harness-backed invocation and native model execution,
`module.permissions` for policy compilation, `module.package-assets` for capability projection, and
`module.spec-publication` for orchestration-facing publication integration. Module IDs are selectable
from this routing view but their Specs remain unavailable to the main coordinator.
