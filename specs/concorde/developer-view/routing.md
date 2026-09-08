```concorde-document
{
  "id": "document.developer-view.routing",
  "targets": [
    "domain.developer-view"
  ],
  "main_visible": true
}
```

# Main routing for Developer view and feedback

Select `domain.docsite` for the Spec publication part of developer views: docsite pages and
navigation, declared diagram rendering, the Spec relationship graph, build identity or publication
failures. That child Domain supplies the publication Service and Module routing facts.

Select `service.viewer` for the Understand Anything viewer interface: launch flags, selecting an
existing raw graph, admitting the installed runtime, forwarding to the official viewer or handling
launch failures. Select `module.managed-runtime` for provisioning or verifying the viewer package
and its runtime dependencies; its implementation remains unavailable to Main discovery.

Select `service.workflow-host` for Studio execution views and for interpreting developer feedback
as a question or authorized task,
preserving intent and constraints, and routing it to the proper execution path. Developer requests
about the substantive behavior of another Domain are routed using that Domain's own responsibilities;
this view and feedback scope does not take ownership of every change discovered through a view.

For execution, checks, reviews or recovery after routing, select `domain.workflow`. For installation
ownership, upgrade plans or consumer configuration, select `domain.installation`. Their IDs identify
related scopes, not implicit access to their remaining Specs.
