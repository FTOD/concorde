```concorde-document
{
  "id": "document.workflow.lifecycle",
  "targets": [
    "domain.workflow"
  ],
  "main_visible": true
}
```

# Agent orchestration

This Domain defines how Agents are assembled and how their invocations, capabilities and feedback
are coordinated. **Agent = `spec.md` + Harness + Constraints/Permissions.** An Agent Graph defines
collaboration and control structure; an Agent Loop defines feedback-driven execution. The stable
registry ID `domain.workflow` and existing `workflow/` paths remain compatibility identifiers.

## Architecture overview

The embedded **Agent orchestration** System overview shows Python Agent definitions binding Agent
Specs and Harnesses, project context entering a Graph, and separate invocations using model clients.
AI review and human feedback enter a control loop that determines the next Graph transition.
The diagram describes the required design; implementation conformance requires checking the
bindings and control paths, not just matching node names.

## Ontology

| Entity | Meaning and relationships |
| --- | --- |
| Agent Spec | The authored `spec.md` defining one Agent’s responsibilities, goals, behavior and completion contract |
| Agent definition | One Python module binding the Agent Spec, Harness and Constraints/Permissions |
| Agent invocation | A particular task execution with admitted context, effective policy, state and identity |
| Harness | The environment integrating available Capabilities, Tools, Skills, models, context, control loops and system resources |
| Capability | Functionality available for Agent use or composition through an explicit contract |
| Agent Graph | A structure coordinating invocations, capability calls and control decisions with explicit transitions |
| Agent Loop | Decision, action, observation and feedback repeated under bounded completion and recovery conditions |
| AI feedback | A model-produced assessment or review bound to a particular task or result |
| Human feedback | Clarification, correction, acceptance, rejection or cancellation that affects an authorized transition |
| Candidate and evidence | Retained work, checks and reviews that bind progress to exact inputs and results |
| Gap and Reflection | A missing promise blocking dependent work, or a separately retained problem requiring disposition |

[Agents and Harnesses](agents-and-harnesses.md) defines A1–A4: responsibility Specs, Python bindings,
Harness composition, capability references and enforced invocation boundaries.
[Agent Graphs, Agent Loops and feedback](agent-graphs-and-loops.md) defines G1–G4: directed
coordination, local and cross-agent loops, AI/human feedback and resumable evidence.

## Operating principles

A routed task binds intended behavior and constraints to a selected target. Its project context
contains only admitted Target Spec, Shared Specs and declared artifacts. The Agent responsibility
Spec and Harness configuration are separate binding inputs; their presence does not add other
project knowledge. The effective Harness is restricted by the Agent definition and trusted host
policy. Installed resources do not automatically become callable tools or loaded Skills.

The Graph declares the Agent responsible for each cognitive decision and the state transferred at
each handoff. AI assessment can identify missing information; AI review can select an admitted repair
path. Human feedback can clarify intent, choose a branch or authorize a specific transition. Required
human acceptance cannot be inferred from model output or silence. Changed goals or authority require
fresh admission, and unchanged blockers do not trigger endless retries.

Every invocation is attributable to its Agent definition, Harness, task, context and permissions.
Graph and loop completion remain separate from delivery. Resumption preserves authorized state and
evidence but starts fresh invocations; raw predecessor transcripts are not an implicit context channel.
A missing contract remains **Spec incomplete** for the affected task and grants no additional access.

## Graphs and supporting capabilities

| Graph or supporting behavior | Coordination and completion |
| --- | --- |
| [Query and routing](query-and-routing.md) | Coordinate target selection, bounded readers and synthesis into an answer |
| [Topology evolution](topology.md) | Coordinate design, human acceptance and target-local authors before an atomic application |
| [Development](development.md) | Coordinate authoring, assessment, planning, implementation and review with explicit revision loops |
| [Review and gaps](review-and-gaps.md) | Return actionable AI feedback or missing-information findings without changing reviewer authority |
| [Reflections](reflections.md) | Select investigation or development after the applicable human disposition |
| [Delivery](delivery.md) | A separately authorized deterministic capability that verifies integration and merges a selected candidate |

The [capability registry](../services/capability-registry.md) describes the existing host adapter and
its exact global/lifecycle/stage inventory. Those classes and role labels are compatibility facts,
not substitutes for the Agent and Harness contracts. [Main routing](routing.md) assigns the component
responsibilities. Installation, initialization and configuration retain their own deterministic
contracts in the Installation Domain.

## Participating components


```concorde-participants
[
  {
    "target_id": "service.spec-context",
    "kind": "service",
    "responsibility": "Resolve registered target context and validate Spec structure for Agent invocations.",
    "selection_condition": "Select when orchestration needs target selection, context resolution, Protocol binding, or Spec validation.",
    "relied_upon_promises": [
      "Each non-implementation worker receives exactly one complete registered target collection plus its pinned global rules."
    ]
  },
  {
    "target_id": "service.workflow-host",
    "kind": "service",
    "responsibility": "Resolve Agent and Harness bindings, admit capability calls, and coordinate Graph and feedback-loop transitions.",
    "selection_condition": "Select for capability routing, agent-stage orchestration, worktree changes, checks, or delivery behavior.",
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
    "selection_condition": "Select when a capability or internal handoff needs deterministic data admission.",
    "relied_upon_promises": [
      "Unknown fields, incompatible type identities, unsupported versions, and unsafe project paths are rejected."
    ]
  },
  {
    "target_id": "module.file-transactions",
    "kind": "module",
    "responsibility": "Apply exact authorized file replacements with current before-digests and rollback.",
    "selection_condition": "Select when an orchestration transition persists documents, worktree state, proposals, or other approved files.",
    "relied_upon_promises": [
      "A stale or invalid multi-file change leaves or restores the complete pre-change state."
    ]
  },
  {
    "target_id": "module.agent-execution",
    "kind": "module",
    "responsibility": "Execute admitted Agent invocations through Harness model integrations and attest their completion envelopes.",
    "selection_condition": "Select when an Agent invocation requires model cognition.",
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
    "responsibility": "Render prompts, Skills, roles and Protocol assets by a deterministic build and validate the package.",
    "selection_condition": "Select for capability inventory, dependencies, projected wrappers, or exported schemas.",
    "relied_upon_promises": [
      "Rendered Skills preserve the canonical launcher and typed capability boundary, and the host refuses stale builds."
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
