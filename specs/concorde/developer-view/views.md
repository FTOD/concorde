```concorde-document
{
  "id": "document.developer-view.views",
  "targets": [
    "domain.developer-view"
  ],
  "main_visible": true
}
```

# Choosing a developer view

| View | Use it to understand | Source and limit |
| --- | --- | --- |
| Docsite | Intended behavior, responsibilities, contracts and workflows | Registered Markdown; navigation does not admit additional agent context |
| Archify diagram | Architecture, collaboration, sequence or state transitions | Explicit diagram JSON and its rendered artifact; a useful view can include internal and external relationships |
| Spec relationship graph | Domain nesting, component composition, participation and contract relationships | Registry and declared contracts; a relationship is not an access grant |
| Studio execution view | Inspect capability runs, policies and stage events | The existing orchestration host; inspection and replay retain its invocation and permission rules |
| Understand Anything viewer | The code structure represented by an existing knowledge graph | Raw Understand Anything JSON; the launcher checks input shape, not semantic accuracy or freshness against HEAD |

The first three views are delivered by the Spec publication subdomain. Studio provides an optional
execution view through the [orchestration host](../services/workflow-host-boundary.md). The code viewer is a
separate integration with the official Understand Anything package, rather than a renamed Spec
relationship graph. They answer different questions and can be used together during development.

When a view prompts a question, identify the relevant source, entity or relationship and the
observed discrepancy. Check which revision or artifact the view represents before treating it as
evidence about current behavior. A generated view cannot silently replace intended behavior in
a Spec, and an observed implementation detail is not automatically a new requirement.

The Framework's viewer launcher expects the official viewer to be installed and a raw graph to
already exist. Graph generation belongs to the upstream code-understanding workflow; starting the
viewer does not run that analysis. Its CLI, input locations and failure behavior are defined by the
[viewer service](../services/viewer-boundary.md).
