```concorde-document
{
  "id": "document.developer-view.ontology",
  "targets": [
    "domain.developer-view"
  ],
  "main_visible": true
}
```

# Developer view and feedback

This Domain helps a developer understand a project, inspect its Specs and implementation views,
and turn questions or corrections into useful development work. It covers the docsite, architecture
and workflow diagrams, the Understand Anything viewer, Studio execution views, and the feedback
path into Framework Agent Graphs.
Spec publication is one part of this experience. Developer views are presentations supplied through
publication and viewer integrations. They are separate from installed Skill entries, which expose
Framework capabilities in a project's model client.

## Architecture overview

The embedded System overview shows authored Specs and code knowledge graphs becoming developer
views, followed by developer feedback and routing into the existing Agent Graphs and capabilities. The view and feedback
boundary includes the integrations that present information and interpret requests; the developer,
source project and Agent Graphs are collaborators outside that boundary.

## Ontology

| Entity | Meaning in this Domain | Relationships |
| --- | --- | --- |
| Developer | A person using the Framework to understand, specify, implement or review a project | Inspects views, supplies intent and feedback, and makes the required acceptance decisions |
| Developer view | A presentation of project knowledge for a particular reading task | Presents authored Specs, declared diagrams, code graphs or execution state |
| Docsite | Navigable pages derived from registered Specs | Opens a Domain's main Spec and links to its detailed contracts and workflows |
| Diagram | An interactive architecture, workflow or other declared view | Shows meaningful entities and relationships and identifies its source |
| Code knowledge graph | An existing raw Understand Anything graph | Supplies implementation observations to the official viewer; it does not define intended behavior |
| Understand Anything viewer | The integrated official viewer for a raw code graph | Opens the supplied graph using the installer-owned runtime |
| Feedback | A developer's question, observation or requested correction | Refers to a view or source and can be clarified into a task |
| Change request | Intent and constraints accepted for further work | Enters the appropriate Framework Graph or capability under its existing permissions and acceptance rules |

## Views and their sources

The [Spec publication subdomain](../publication/ontology.md) owns docsite preparation and publication,
including the rendering and embedding of declared diagrams. Its main pages provide an overall
understanding and its topic pages explain detailed contracts. Diagram sources remain separately
reviewable artifacts rather than becoming another authority for unrelated agent reads.

The [Understand Anything viewer](../services/viewer-boundary.md) opens a project's existing raw graph.
It complements the authored Spec view with a code view. The launcher does not generate that graph
or prove its agreement with the current code or Spec. [View selection](views.md) explains which
source each view represents and when to use it.

## Feedback and follow-through

A developer can point to a page, entity, relationship or source and explain what seems wrong or
what should change. Clarification happens through the developer's agent conversation. Once the
intent is clear and authorized, the Framework routes the request to the appropriate Graph or capability.
No separate report file is required for ordinary feedback, and a diagram click or comment does
not silently change a Spec or grant access to another target.

[Feedback](feedback.md) describes this path and the distinction between an observation and an
accepted change. The [Agent orchestration Domain](../workflow/ontology.md) owns execution, verification and
recovery. This Domain owns how developers encounter that work and provide input to it.

## Routing and dependencies

[Main routing](routing.md) selects the publication subdomain, viewer service, orchestration host or
managed runtime according to the task. The [Installation Domain](../installation/ontology.md)
provides the runtime and installed entrypoints; using the viewer does not repeat installation.

## Participating components

```concorde-participants
[
  {
    "target_id": "service.viewer",
    "kind": "service",
    "responsibility": "Open an existing Understand Anything graph through the verified local viewer integration.",
    "selection_condition": "Select for viewer launch, raw graph input, runtime admission, CLI behavior or launch failures.",
    "relied_upon_promises": [
      "Viewer launch checks installed runtime identity and raw graph shape without downloading dependencies or rewriting Specs."
    ]
  },
  {
    "target_id": "service.workflow-host",
    "kind": "service",
    "responsibility": "Turn developer questions and clarified feedback into bounded task routing and Graph requests.",
    "selection_condition": "Select for feedback intent, routing, task constraints, or the transition from a developer decision to agent work.",
    "relied_upon_promises": [
      "A routed request preserves developer intent and constraints; a view or comment never independently grants mutation authority."
    ]
  },
  {
    "target_id": "module.managed-runtime",
    "kind": "module",
    "responsibility": "Provision the pinned official viewer runtime used by developer-facing code views.",
    "selection_condition": "Select for viewer package identity, dependencies, provisioning, verification or installation recovery.",
    "relied_upon_promises": [
      "Viewer provisioning uses versioned and hash-bound package inputs and does not accept a partial runtime as complete."
    ]
  }
]
```
