# How a specified change progresses

This Domain concerns turning intended behavior into a completed, evidenced change. It includes
Spec contexts, the Operation host, agent execution, permissions, reflection triage and file transactions.
The Operation inventory in this collection is the complete public command vocabulary.

## Business entities and responsibility

A Task is user intent for exactly one target, optionally focused on a local Feature or API. Its
constraints travel unchanged through the change attempt. A Configuration selects a supported agent
integration and enforcement mode; it is project setup, not per-stage agent authority. A Spec snapshot
freezes the selected collection plus global principles and the target kind definition. A Stage is
one fresh cognition session with a declared role. A Change attempt binds its plan and tasks to the
intent and Spec revision. A Check measures implementation and returns status plus byte identities.
A Gap is a concrete missing obligation or fact required by a stage. A Reflection is a reported
problem that may require investigation and, separately, human approval of a proposed resolution.
A Topology design is a coordinator-authored candidate registry plus target-local Spec tasks. A
Topology application is the host-private exact registry/document byte set produced only after that
design is accepted.

The context Service selects only registered local documents. The host gives that snapshot to the
agent execution Module under a permission policy compiled for the stage. Authoring returns proposed
replacement documents; the host applies only members of the selected collection. Planning first
assesses whether the task is answerable. An insufficient context stops before an attempt is created.
Tasks turn the accepted plan into explicit acceptance conditions. The implementation worker receives
that plan/tasks TypedValue plus explicitly owned code. It cannot edit Specs, registry or other code.

## Main routing view

The main coordinator may expand this Domain after `domain.concorde` identifies a workflow task. It
selects `service.spec-context` for target registration, Protocol binding, context resolution and
Spec structural validation; `service.workflow-host` for public Operation admission, routing,
agent-stage execution and lifecycle state; and `service.reflections` for Reflection selection,
investigation or disposition. It selects `module.registry` for the in-process registry API,
`module.wire-contracts` for TypedValue/schema validation, `module.file-transactions` for atomic file
replacement, `module.agent-execution` for native model-process execution,
`module.permissions` for policy compilation, `module.package-assets` for capability projection, and
`module.spec-publication` for workflow-facing publication integration. Module IDs are selectable
from this routing view but their Specs remain unavailable to the main coordinator.

## Participating components

```concorde-participants
[
  {
    "target_id": "service.spec-context",
    "kind": "service",
    "responsibility": "Resolve registered target context and validate Spec structure for workflow stages.",
    "selection_condition": "Select when a workflow needs target selection, context resolution, Protocol binding, or Spec validation.",
    "relied_upon_promises": [
      "Each non-implementation worker receives exactly one complete registered target collection plus its pinned global rules."
    ]
  },
  {
    "target_id": "service.workflow-host",
    "kind": "service",
    "responsibility": "Admit public Operations and coordinate their bounded lifecycle transitions.",
    "selection_condition": "Select for Operation routing, agent-stage orchestration, attempts, checks, or delivery behavior.",
    "relied_upon_promises": [
      "Every agent stage is a fresh invocation bound to typed input, context identity, policy, and completion evidence."
    ]
  },
  {
    "target_id": "service.reflections",
    "kind": "service",
    "responsibility": "Retain, investigate, implement, and dispose project Reflections under explicit ownership and approval.",
    "selection_condition": "Select when work concerns Reflection status, evidence, investigation, implementation, or disposition.",
    "relied_upon_promises": [
      "Reflection investigation is read-only implementation cognition and human disposition remains independent."
    ]
  },
  {
    "target_id": "module.registry",
    "kind": "module",
    "responsibility": "Admit registry metadata and select targets, focuses, documents, contracts, and implementation ownership.",
    "selection_condition": "Select for in-process registry parsing, identity lookup, membership, or ownership validation.",
    "relied_upon_promises": [
      "Registry lookup never adds ancestor, peer, participant, or implementation bodies to a target context."
    ]
  },
  {
    "target_id": "module.wire-contracts",
    "kind": "module",
    "responsibility": "Validate versioned TypedValues and JSON boundary schemas.",
    "selection_condition": "Select when an Operation or internal handoff needs deterministic data admission.",
    "relied_upon_promises": [
      "Unknown fields, incompatible type identities, unsupported versions, and unsafe project paths are rejected."
    ]
  },
  {
    "target_id": "module.file-transactions",
    "kind": "module",
    "responsibility": "Apply exact authorized file replacements with current before-digests and rollback.",
    "selection_condition": "Select when a workflow stage persists documents, attempts, proposals, or other approved files.",
    "relied_upon_promises": [
      "A stale or invalid multi-file change leaves or restores the complete pre-change state."
    ]
  },
  {
    "target_id": "module.agent-execution",
    "kind": "module",
    "responsibility": "Launch native model processes and attest their completion envelopes.",
    "selection_condition": "Select when a bounded workflow stage requires model cognition.",
    "relied_upon_promises": [
      "Launch, policy, workspace, invocation, and context identities are checked before domain output is admitted."
    ]
  },
  {
    "target_id": "module.permissions",
    "kind": "module",
    "responsibility": "Compile stage effects into native or outer sandbox grants.",
    "selection_condition": "Select when an agent launch needs exact read, write, network, or credential authority.",
    "relied_upon_promises": [
      "Runtime configuration cannot widen the host-issued semantic role paths."
    ]
  },
  {
    "target_id": "module.package-assets",
    "kind": "module",
    "responsibility": "Render and validate canonical public Operation surfaces used by the workflow.",
    "selection_condition": "Select for capability inventory, dependencies, projected wrappers, or exported schemas.",
    "relied_upon_promises": [
      "Projected public surfaces preserve the canonical executable and typed Operation boundary."
    ]
  },
  {
    "target_id": "module.spec-publication",
    "kind": "module",
    "responsibility": "Provide workflow-facing publication of registered Specs and declared diagrams.",
    "selection_condition": "Select when workflow behavior invokes or validates the documentation projection.",
    "relied_upon_promises": [
      "Published views are derived from explicit registry membership and never become agent context authority."
    ]
  }
]
```

## Conditions, states and recovery

```mermaid
stateDiagram-v2
  [*] --> Specified
  Specified --> Gap: missing information
  Gap --> Specified: explicitly author missing contract
  Specified --> Planned: context sufficient
  Planned --> Tasks: plan accepted
  Tasks --> Implemented: acceptance fulfilled
  Implemented --> Validated: checks pass on current bytes
  Validated --> Delivered: evidence current
  Implemented --> Tasks: failure needs implementation work
  Delivered --> [*]
```

Topology evolution follows a separate two-gate sequence:

```mermaid
stateDiagram-v2
  [*] --> Designed: concorde-main design-topology
  Designed --> Authoring: maintainer accepts design
  Authoring --> Gap: target-local Spec incomplete
  Authoring --> Prepared: overlay validation succeeds
  Prepared --> Applied: maintainer accepts exact artifact
  Prepared --> Stale: registry, Protocol or source bytes changed
  Applied --> [*]
```

No target author writes project files. A gap leaves the pre-design project unchanged. Prepared
artifacts contain full proposed bytes, but only their path/digest enters coordinator cognition.
Application is one host transaction with current before-digests and final repository validation.

A known prohibition is unsupported, a contradiction is conflicting, a missing runtime value is
invalid input, and tool failure is failed. None automatically means Spec incomplete. A gap names
the unresolved question, blocked step and needed contract; target and snapshot identity accompany it.
Context solving diagnoses from the exact existing collection and never expands permissions.

A Domain task may coordinate multiple components participating in that scope or its nested scopes.
The Domain planner sees only the Domain collection and derives exact component IDs from its local
`concorde-participants` declarations. Before planning, deterministic context solving rejects any
missing direct registry relationship as a Domain-owned Spec gap and reports inconsistent entries as
conflicting. Each component
receives its own explicit task, local authoring invocation and fast loop. All affected
consumer/provider contract views must agree before any component implementation begins. Component
ancestry and scope membership never grant extra reads. Successful component revisions are checked
again before Domain delivery.

Checks are trusted deterministic argv declared by project configuration, not commands invented by
an agent. Raw logs stay out of later Spec-only sessions. A stale Spec, changed task intent, modified
code, failed check or missing completion blocks delivery and preserves the attempt. Resuming a
change reuses its typed artifacts but starts a fresh agent session. The host does not copy unrelated
conversation or free-form predecessor output into context.

Reflection status is metadata-only. Investigation runs as read-only implementation with selected
record bytes and HEAD. The host preserves the original report and human comments, writes findings
and an evidence-bound plan, and enforces configured approval. Implementation gets a newly authored
behavior task through a standard loop. Human disposition remains required before closing a report;
merely observing that a problem no longer reproduces does not dismiss it.
