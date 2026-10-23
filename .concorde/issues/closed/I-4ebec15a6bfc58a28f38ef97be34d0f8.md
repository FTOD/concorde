# I-4ebec15a6bfc58a28f38ef97be34d0f8

```json
{
  "schema_version": 4,
  "id": "I-4ebec15a6bfc58a28f38ef97be34d0f8",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:1a0139e76b70eafeaa6a2c8e2a001beec217b700a283a3d39f42c7d8b29362d4",
      "created_at": "2026-10-13T17:45:57.564819+00:00",
      "report": {
        "report_key": "spec-panel/module.code-review/14",
        "tier": "suggestion",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Put the citation-resume condition beside its exception",
        "description": "The resume exception refers to “those citations” before introducing them and puts its condition after the action it limits. The related explanation hides the resuming actor.\n\nSuggested repair: Place the condition immediately after “except once”: “except once when a finding's Module, basis or location does not hold, to correct every such citation.” Name the Operation as the actor in the explanatory sentence.",
        "impact": "The reader must reorder the exception to identify which citations justify the single resume.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/code-review/requirements.md at req.code-review.no-resume, line 189 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: “After a reviewer returns its result, the code review Operation SHALL NOT resume it, except once, with those citations to correct, when a finding's Module, basis or location does not hold.” The evidence-resolves explanation says, “The reviewer is therefore resumed once with every such citation to correct.”\n\nThe panel's chair merged r1.15 and verified: Verified both passages. The exception is present and its meaning is recoverable, so this is low-severity advisory wording, not a missing retry rule.",
        "owner_target_id": "module.code-review",
        "evidence": [
          {
            "path": "specs/concorde/method/code-review/requirements.md",
            "description": "req.code-review.no-resume, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.code-review",
        "context_id": "sha256:7eb19425e1277ec68204b38a48ae66ee807ec2b29bc9c5d0af8470432224d3d3",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "not-actionable",
      "note": "Suggestion-tier Issue closed by the developer's 2026-10-17 decision: reviews no longer record suggestions as Issues (task r4-review-tuning); suggestions stay in each review's run result. Reopen if it becomes a real problem.",
      "evidence": [
        ".concorde/decisions"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-23T09:22:52.170172+00:00"
    }
  ]
}
```
