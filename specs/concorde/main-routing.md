```concorde-document
{
  "id": "document.concorde.main-routing",
  "targets": [
    "domain.concorde"
  ],
  "main_visible": true
}
```

# Main routing for Concorde Framework

This is the routing view for the Concorde software project. Generic coordinator behavior belongs to
the [query and routing Agent Graph](workflow/query-and-routing.md); this page supplies the project's
own stable target identities and selection conditions.


The main coordinator starts with this complete collection. It selects `domain.workflow` for tasks
about Agent definitions, Harnesses, capabilities, Agent Graphs, control loops, AI/human feedback,
Spec contexts, planning, implementation, validation, delivery or Reflections;
`domain.installation` for package, installation, initialization, configuration, upgrade or runtime
provisioning behavior; and `domain.developer-view` for developer-facing views and feedback, including
docsite, diagrams, the Spec relationship graph, Understand Anything and the transition from feedback
to a work request. That Domain routes Spec publication to its `domain.docsite` child and viewer
launch to `service.viewer`. A task that changes the universal Protocol itself remains on
`domain.concorde`, focused on `feature.concorde.evolve-protocol`. These stable IDs and selection
conditions are routing facts only; opening a child Domain requires an explicit main-context
expansion.


A document split does not create a new target or reduce context. This page remains part of
`domain.concorde`'s main-visible collection alongside its `ontology.md` and Concorde Spec Protocol description.
