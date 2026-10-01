# I-c45e5bd967ca5ac8ac2f2e2bf56816ff

```json
{
  "schema_version": 3,
  "id": "I-c45e5bd967ca5ac8ac2f2e2bf56816ff",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9461d0215a4214efbee41195bdbe4a5c57de9f343188e650dc25f12ee63e6363",
      "created_at": "2026-10-01T06:13:09.013441+00:00",
      "report": {
        "report_key": "module.workers/1",
        "tier": "preferred-fix",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "The shared brief blocks Spec reviewers on reportable gaps",
        "description": "The shared missing-promise fallback includes review-spec and review-architecture, contradicting their Operation's instruction to report gaps and continue whenever review is possible.\n\nSuggested repair: Explicitly defer review-spec and review-architecture gap reporting to Spec review: report missing promises or context as findings and continue, reserving blocked for inability to participate at all.\n\nOther Modules concerned: module.spec-review",
        "impact": "An otherwise viable review can stop before reporting its findings, and a panel can stop before the chair.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/execution/workers/module.md at the-brief, line 282 by the consistency criterion of the Protocol's Evaluating a Spec; the Specs read: Workers says: \"every other worker returns `blocked`\" after exceptions for review-code, understand and code-to-spec. Spec review's module.md, 'What a worker sees', says a reviewer lacking a provider document \"reports a `context` finding naming it and goes on\" and \"ends `blocked` only when it cannot review at all\".\n\nThe panel's chair merged r2.1, r3.3, a1.1, a2.1 and verified: Verified both instructions in their owning entries. Merged five reports of the same conflict. Preferred repair preserves Spec review's established reporting policy.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/execution/workers/module.md",
            "description": "the-brief, cited by the consistency finding"
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
