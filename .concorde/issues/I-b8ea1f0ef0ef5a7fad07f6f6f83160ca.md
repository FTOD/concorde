# I-b8ea1f0ef0ef5a7fad07f6f6f83160ca

```json
{
  "schema_version": 4,
  "id": "I-b8ea1f0ef0ef5a7fad07f6f6f83160ca",
  "status": "open",
  "reports": [
    {
      "id": "sha256:48f7d280e66913b3b1c3fa375f1f477881a308df386c8fafee89847f8f546fc9",
      "created_at": "2026-10-13T20:24:35.150549+00:00",
      "report": {
        "report_key": "spec-panel/module.views/2",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "Candidate cleanup precedes the admission that protects sources",
        "description": "The production build deletes the candidate before source/output admission. Unconditional failure cleanup can also delete it after admission has refused all mutation.\n\nSuggested repair: Complete source/output admission before the first deletion. Gate failure cleanup on successful admission and ownership of the candidate for this invocation. Align the ordered build procedure and build-site scenario with that order.",
        "impact": "An implementation following the ordered build procedure can delete a registered source before detecting its overlap with the candidate directory, or delete it during cleanup after admission refuses it.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/spec-tooling/views/pipeline.md at Promotion, line 502 by the design criterion of the Protocol's Evaluating a Spec; the Specs read: “Every command loads before it clears or writes anything.” The buildSite sequence instead says “It deletes `docsite/.generated/candidate`” before “It runs `preparePublication` in `build` mode.” It also says “On any failure, `buildSite()` deletes the candidate and rethrows.”\n\nThe panel's chair merged r2.2, r3.1 and verified: Verified that requireScoped checks only configuration readability, while loadScopedRegistry performs source/output admission. High because the main build procedure conflicts with an explicit safety rule that a careful reader can find. Preferred-fix preserves that existing rule.",
        "owner_target_id": "module.views",
        "evidence": [
          {
            "path": "specs/concorde/spec-tooling/views/pipeline.md",
            "description": "Promotion, cited by the design finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.views",
        "context_id": "sha256:01a9df9628d7d7a1f6b71425e7ea1c59f4d7ac51d895d9e83cec9f58727bcbcc",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
