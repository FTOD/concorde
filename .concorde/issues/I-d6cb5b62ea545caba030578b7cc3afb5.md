# I-d6cb5b62ea545caba030578b7cc3afb5

```json
{
  "schema_version": 3,
  "id": "I-d6cb5b62ea545caba030578b7cc3afb5",
  "status": "open",
  "reports": [
    {
      "id": "sha256:d604e08991467f35af21ce470e6c6449279cdf14da82bd80d88c8c84f3ff975a",
      "created_at": "2026-10-01T06:13:09.292523+00:00",
      "report": {
        "report_key": "module.workers/6",
        "tier": "preferred-fix",
        "type": "bug",
        "subtype": null,
        "title": "Pre-launch configuration refusals lack a canonical error-link contract",
        "description": "Workers names its pre-launch configuration refusals but does not define the resolver's error-link actor, reasons and cause rules. The consumer expects a component link, while the published Workers error table covers only runs.\n\nSuggested repair: Add a resolver failure contract covering all configuration, map and backend refusal codes, including level, actor, reason, detail, causes and caller wrapping. Make clear that resolution fails before creation of a worker run or run record, and align it with Operations' worker_model_unavailable rule.\n\nOther Modules concerned: module.operations, module.tracing",
        "impact": "The configuration reader and its callers cannot derive a complete, consistent resolver error link from Workers' selected specification.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/execution/workers/module.md at resolving-the-backend, line 324 by the interfaces criterion of the Protocol's Evaluating a Spec; the Specs read: module.md says backend_missing occurs before Workers is called and is a cause of the step's error. It also names config_missing, config_invalid, model_not_enabled, model_unresolved, model_map_missing, model_map_invalid and model_unmapped. launch.md's Errors section applies to worker runs and defines none of those resolver links. Operations' workers.md expects \"the `component` link of Workers' model configuration, with its code and the file\".\n\nThe panel's chair merged r1.1 and verified: Narrowed r1.1: successful resolution inputs and values are already explained, and Operations does specify caller-side wrapping. The remaining gap is Workers' canonical resolver error contract, not complete absence of all error guidance.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/execution/workers/module.md",
            "description": "resolving-the-backend, cited by the interfaces finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:d9d26b9c3b118a1ec71a8cb21310fcb039173ad3cfece95db1c14e2faee0ef23",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    }
  ],
  "dispositions": []
}
```
