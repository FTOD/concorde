# I-879bed9a38fd5aa9b91beab3c8e9ce79

```json
{
  "schema_version": 4,
  "id": "I-879bed9a38fd5aa9b91beab3c8e9ce79",
  "status": "open",
  "reports": [
    {
      "id": "sha256:f9fc0b2e180cedab7f8c1662eba8e69d78256ff2001cc197c893ebd629f4408f",
      "created_at": "2026-10-29T08:12:24.739139+00:00",
      "report": {
        "report_key": "spec-panel/module.understanding/10",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Require existing relied-upon promises in the new-promise scenario",
        "description": "The scenario guarantees sufficiency from a known destination for a new promise without establishing that the Specs state the existing promises the change relies on.\n\nSuggested repair: Add a GIVEN condition that the bound Specs state every existing promise the change relies on.",
        "impact": "A test or implementation could accept an insufficient Spec simply because it identifies where to specify the addition.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 judged specs/concorde/method/understanding/scenarios.md at scenario.understanding.new-promise by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The premises establish a goal adding a promise and that the Spec \"already says which of its documents states such promises\". The outcome says \"a sufficient assessment\". The assessment semantics also require \"every existing promise the change relies on\".\n\nThe panel's chair merged r2.1 and verified: Verified the scenario against the entry and assessment semantics. This blocking edge-case omission has an obvious repair that preserves the scenario's intended known-placement case.",
        "owner_target_id": "module.understanding",
        "evidence": [
          {
            "path": "specs/concorde/method/understanding/scenarios.md",
            "description": "scenario.understanding.new-promise, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.understanding",
        "context_id": "sha256:0d0670996a16adb7d10fc01249f107def79b08caa3b4a75147f1baab19afd1af",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
