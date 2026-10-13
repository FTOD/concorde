# I-3c2eca703ec05d5fbdcf01d5af7d1497

```json
{
  "schema_version": 4,
  "id": "I-3c2eca703ec05d5fbdcf01d5af7d1497",
  "status": "open",
  "reports": [
    {
      "id": "sha256:c2a390cbdbd5e7f607be3ba3e11f956e2a96fb82619f5f19a1c8067eb939089c",
      "created_at": "2026-10-13T20:34:06.846202+00:00",
      "report": {
        "report_key": "spec-panel/module.workers/8",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The model-map contract excludes standalone discovery",
        "description": "The model-map contract excludes its documented discovery reader and does not scope mandatory map refusals to worker resolution.\n\nSuggested repair: Describe resolution and advisory discovery separately. Keep mandatory refusals for resolution and state that discovery reports unavailable map information while continuing its listing.",
        "impact": "Implementers cannot satisfy both launch-only map reading and map-aware standalone discovery.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/worker-harness/workers/contracts.md at contract.workers.model-map, line 574 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The contract says \"Workers reads it only when a worker launches\". The entry's discovery output includes \"the project model names the model map already gives each candidate\", and scenario.workers.models-listed-mapped requires those names. The entry says a missing or unreadable map is reported during discovery, never refused.\n\nThe panel's chair merged r2.5 and verified: Verified the contract, discovery explanation and mapped/unmapped discovery scenarios. Medium for the secondary discovery use; preferred-fix because scoping the restriction to resolution reconciles the already promised behaviors.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/worker-harness/workers/contracts.md",
            "description": "contract.workers.model-map, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.workers",
        "context_id": "sha256:d26f3cb0c72a7d5a7397818fed5c878790107966ca3a23d67fd3db829894a593",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
