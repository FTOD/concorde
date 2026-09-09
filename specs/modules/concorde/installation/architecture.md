```concorde-document
{
  "id": "document.specs.modules.concorde.installation.architecture",
  "targets": [
    "module.installation"
  ],
  "main_visible": true
}
```

# Architecture

The installer proposes owned file changes and applies accepted current proposals. Initialization creates a Module stub, an explicit registry and a pinned Protocol binding. Build produces assets; installation places and verifies them. Missing business facts remain explicit. Failed application or provisioning restores previously valid owned state.

## Internal domain

A package inventory, installation proposal, owned-file receipt, integration and verified runtime describe adoption. Installation places artifacts produced by Package assets and provisions Managed runtime. Initialization delegates explicit Module/Implementation registry creation to Spec contexts. These shared capabilities remain siblings, not private installation submodules.

## Relied-upon Module promises

Each declaration below is local contract content. It grants no access to the provider's remaining Spec or implementation.

```concorde-dependencies
[
  {
    "target_id": "module.spec-context",
    "responsibility": "Resolve complete Module contracts, bind code-writing implementation context and validate explicit Spec structure.",
    "selection_condition": "Select when the task concerns module contexts.",
    "relied_upon_promises": [
      "resolve_context selects one Module and its complete registered documents. Feature focus never trims the collection. Non-code phases do not receive Implementation Specs or source. The implementation phase adds only the referenced Implementation Specs and exact bound files. Membership, bytes, rules and admitted stage inputs determine context identity."
    ]
  },
  {
    "target_id": "module.package-assets",
    "responsibility": "Build deterministic Agent, Skill, Protocol, schema and documentation assets from authored sources.",
    "selection_condition": "Select when the task concerns package assets.",
    "relied_upon_promises": [
      "build renders assets; write_build writes owned projections; check_build compares without changing the worktree. verify_fresh detects changed authoring sources. Module and Implementation kind definitions are distributed together. Generated assets are derived outputs and are never independent authoring sources."
    ]
  },
  {
    "target_id": "module.managed-runtime",
    "responsibility": "Provision and verify the pinned Python and viewer runtime used by installed integrations.",
    "selection_condition": "Select when the task concerns managed runtime.",
    "relied_upon_promises": [
      "load_runtime_spec reads locked requirements. plan_runtime describes provisioning state. provision_runtime stages versioned, hash-bound inputs and records verified receipts. A failed acquisition does not replace a previously valid runtime or accept a partial installation."
    ]
  },
  {
    "target_id": "module.file-transactions",
    "responsibility": "Apply exact multi-file changes with before-digest checks and rollback.",
    "selection_condition": "Select when the task concerns file transactions.",
    "relied_upon_promises": [
      "file_change captures a current before-digest. apply_files accepts exact allowed paths, stages changes, rechecks originals and invokes verification. A stale, invalid or failed application restores prior bytes and removes newly created files. Proposed content cannot expand the allowed set."
    ]
  },
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
