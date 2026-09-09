```concorde-document
{
  "id": "document.specs.modules.concorde.architecture",
  "targets": [
    "module.concorde"
  ],
  "main_visible": true
}
```

# Architecture

Developers use installed concorde-* Skills and deterministic CLI entry points. Requests carry a task and constraints; results distinguish completion, missing contracts, failure and an inspectable candidate. Installation supplies the accepted rule assets; workflows coordinate work; publication and the viewer support inspection.

## Internal domain

The Framework is composed of the Modules listed below. Each has this Module as its single structural parent. Shared capabilities are siblings of their consumers. Module composition, capability use and shared implementation are separate relationships. Developer requests, project Specs, candidate changes and published views are domain concepts, not additional target kinds.

## Relied-upon Module promises

Each declaration below is local contract content. It grants no access to the provider's remaining Spec or implementation.

```concorde-dependencies
[
  {
    "target_id": "module.protocol",
    "responsibility": "Define the Module/Implementation specification standard and evolve its explicitly bound revision.",
    "selection_condition": "Select when the task concerns spec protocol.",
    "relied_upon_promises": [
      "Consumers exchange registered Markdown Specs and registry schema 2. A project accepts Protocol 2.0.0 by version and digest. Module Specs describe observable features, usage interfaces and internal domains. Implementation Specs bind reusable realizations to exact files."
    ]
  },
  {
    "target_id": "module.workflows",
    "responsibility": "Route tasks and coordinate specification, planning, coding, review, topology changes and delivery.",
    "selection_condition": "Select when the task concerns agent workflows.",
    "relied_upon_promises": [
      "The public boundary is a versioned TypedValue invocation of an installed concorde-* Skill. Global calls select the owning Module; lifecycle calls perform declared deterministic actions. A planner determines tasks from the selected Module Spec alone. Code writers additionally receive referenced Implementation Specs. Each stage reports its own completion and gaps; a completed component does not independently deliver the enclosing change."
    ]
  },
  {
    "target_id": "module.installation",
    "responsibility": "Install, initialize, configure and upgrade Concorde while preserving user-owned content.",
    "selection_condition": "Select when the task concerns installation.",
    "relied_upon_promises": [
      "The installer proposes owned file changes and applies accepted current proposals. Initialization creates a Module stub, an explicit registry and a pinned Protocol binding. Build produces assets; installation places and verifies them. Missing business facts remain explicit. Failed application or provisioning restores previously valid owned state."
    ]
  },
  {
    "target_id": "module.spec-context",
    "responsibility": "Resolve complete Module contracts, bind code-writing implementation context and validate explicit Spec structure.",
    "selection_condition": "Select when the task concerns module contexts.",
    "relied_upon_promises": [
      "resolve_context selects one Module and its complete registered documents. Feature focus never trims the collection. Non-code phases do not receive Implementation Specs or source. The implementation phase adds only the referenced Implementation Specs and exact bound files. Membership, bytes, rules and admitted stage inputs determine context identity."
    ]
  },
  {
    "target_id": "module.registry",
    "responsibility": "Admit Module and Implementation identities, resolve document collections and look up exact file ownership and reuse.",
    "selection_condition": "Select when the task concerns spec registry.",
    "relied_upon_promises": [
      "SpecRepository reads registry schema 2. select returns a Module descriptor. Implementation records form a separate index, file_implementations maps each declared file to one owner, and implementation_users maps each Implementation Spec to all using Modules. Lookups never follow a relationship to read another Spec body."
    ]
  },
  {
    "target_id": "module.wire-contracts",
    "responsibility": "Admit versioned structured values, offline schemas and safe project paths.",
    "selection_condition": "Select when the task concerns wire contracts.",
    "relied_upon_promises": [
      "TypedValue envelopes identify a type, version and data. Unknown fields, unsupported identities and malformed values fail admission. File-path helpers reject traversal and aliases. Schema validation is deterministic and offline; a validation error never grants a different context or fallback authority."
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
    "target_id": "module.agent-execution",
    "responsibility": "Execute separately bound Agent invocations through their Harness and admit typed results.",
    "selection_condition": "Select when the task concerns agent execution.",
    "relied_upon_promises": [
      "AgentProcessExecutor accepts a host-built LaunchSpecification, verifies the Agent/Harness binding and effective policy, starts the selected model integration and validates completion evidence. Exit code alone does not establish completion. Recursive invocations retain independent context, limits and typed handoffs."
    ]
  },
  {
    "target_id": "module.permissions",
    "responsibility": "Compile declared effects and host authority into reproducible execution permissions.",
    "selection_condition": "Select when the task concerns execution permissions.",
    "relied_upon_promises": [
      "compile_policy intersects role paths and caller authority. Native renderers establish the resulting read, write, command and network boundaries or reject unsupported enforcement. Only a code-writing invocation may write its bound implementation files and admitted Implementation Spec documents; Module contracts remain immutable in that phase."
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
    "target_id": "module.reflections",
    "responsibility": "Retain, investigate and resolve explicitly attributed project feedback and persistent gaps.",
    "selection_condition": "Select when the task concerns reflections.",
    "relied_upon_promises": [
      "The triage boundary selects explicit records by Module or local feature/interface identity. Status is read-only. Investigation runs in a separately bound code invocation. Verified findings and developer disposition determine further work; ordinary feedback does not automatically create a Reflection or enlarge its owner."
    ]
  },
  {
    "target_id": "module.publication",
    "responsibility": "Create navigable documentation and diagrams from registered Module and Implementation Specs.",
    "selection_condition": "Select when the task concerns spec publication.",
    "relied_upon_promises": [
      "concorde docsite proposes and applies site scaffolding. The site reads registry schema 2 and builds pages, navigation and relationship views from registered sources. Module composition, dependencies and implementation reuse are distinct edges. Each Module opens its module.md. Implementation pages expose their file bindings and using Modules. Only a complete current candidate is promoted."
    ]
  },
  {
    "target_id": "module.viewer",
    "responsibility": "Open an existing Understand Anything code graph with the verified installed viewer.",
    "selection_condition": "Select when the task concerns code viewer.",
    "relied_upon_promises": [
      "scripts/run-viewer.py accepts a project root, optional port and no-open flag. It checks the ordered raw graph inputs and runtime identity, then launches the official viewer and returns its exit code. It does not generate the graph, install dependencies or establish that code agrees with its Spec."
    ]
  }
]
```
