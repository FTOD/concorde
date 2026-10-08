# I-693b8b3bc8d05f2ca9d32c03bf6bc8db

```json
{
  "schema_version": 4,
  "id": "I-693b8b3bc8d05f2ca9d32c03bf6bc8db",
  "status": "open",
  "reports": [
    {
      "id": "sha256:bfb1916a4ff739e14157cc11d3dc2c0ca85befe993e8f0c459af5b46f0dfe411",
      "created_at": "2026-10-08T08:15:01.419505+00:00",
      "report": {
        "report_key": "spec-panel/module.issues/8",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Duplicate-record repair assumes comparable histories",
        "description": "The only prescribed repair for doubled records assumes that one copy extends the other. The diagnosis covers divergent valid copies too, but supplies no applicable repair or stopping instruction for them.\n\nSuggested repair: Limit the keep-the-extension repair to comparable histories. For divergent histories, require preserving both copies and define an escalation or reconciliation process, including who decides the canonical history without losing accepted observations.",
        "impact": "When both copies extend a common history differently, the operator cannot select either using the promised repair. Arbitrarily choosing one would discard observations or dispositions.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/issues/interface.md at Bookkeeping command, line 640 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: For an Issue recorded in both folders, the check promises an error naming \"both paths and the repair\". It prescribes \"keep the record whose reports and dispositions begin with the other's\" and remove the other with git rm. The record validity rules do not require two individually valid copies to have comparable histories.\n\nThe panel's chair merged r2.9 and verified: Verified the repair text, record validity rules and doubled-record check scenario. Medium because divergent duplicate records are an exceptional repair case. Decision-needed because the Specs do not establish who reconciles divergent histories or what canonical history should result.",
        "owner_target_id": "module.issues",
        "evidence": [
          {
            "path": "specs/concorde/issues/interface.md",
            "description": "Bookkeeping command, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.issues",
        "context_id": "sha256:985a655511357d2b9a8f9c799ecb1ace344be22b1cebfc16804d474ab231d869",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
