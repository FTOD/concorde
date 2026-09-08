```concorde-document
{
  "id": "document.publication.routing",
  "targets": [
    "domain.docsite"
  ],
  "main_visible": true
}
```

# Main routing for Spec publication


The main coordinator selects `service.publication` for consumer-facing docsite proposal, build and
publication outcomes. It selects `module.spec-publication` for the in-process registry-to-pages,
sidebar, graph, diagram and build-manifest API. The Module ID is visible here so work can be routed;
its remaining target collection stays private to the fresh target worker.

Understand Anything launch and the general feedback path belong to the parent
`domain.developer-view`, which supplies the viewer and workflow-host routing facts.
