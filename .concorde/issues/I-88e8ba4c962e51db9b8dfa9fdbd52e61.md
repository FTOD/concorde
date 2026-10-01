# I-88e8ba4c962e51db9b8dfa9fdbd52e61

```json
{
  "schema_version": 3,
  "id": "I-88e8ba4c962e51db9b8dfa9fdbd52e61",
  "status": "open",
  "reports": [
    {
      "id": "sha256:396fec6b7def9f2375e073b9aa8d39eec2019f7cc7b19990658f3158d0b38603",
      "created_at": "2026-10-01T06:13:09.349697+00:00",
      "report": {
        "report_key": "module.workers/7",
        "tier": "decision-needed",
        "type": "bug",
        "subtype": null,
        "title": "Whole-configuration map checking has no defined invocation policy",
        "description": "The scenario introduces whole-configuration map validation without specifying its entry point, invocation policy or error code.\n\nSuggested repair: Decide whether this is launch-time validation or a separate check, then define its caller, timing, aggregate refusal code and result. If no such behavior is intended, remove the scenario.\n\nOther Modules concerned: module.operations",
        "impact": "An implementer must invent when the aggregate map check runs, how it is invoked and which refusal it returns.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/execution/workers/scenarios.md at scenario.workers.model-map-checked, line 447 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"WHEN the whole configuration is checked against the map\" and \"THEN one refusal names every model and backend the map lacks, with the workers that would take them\". The entry describes resolving the map for the requested worker and whole-configuration validation of structure, catalog names, limits and reasoning vocabulary.\n\nThe panel's chair merged r1.2 and verified: Verified the aggregate scenario against the entry, contracts and Operations' worker sequence. Choosing whether this check gates launches or is a separate operation changes observable admission behavior.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/execution/workers/scenarios.md",
            "description": "scenario.workers.model-map-checked, cited by the obligations finding"
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
