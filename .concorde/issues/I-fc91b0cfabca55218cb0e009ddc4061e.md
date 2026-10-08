# I-fc91b0cfabca55218cb0e009ddc4061e

```json
{
  "schema_version": 4,
  "id": "I-fc91b0cfabca55218cb0e009ddc4061e",
  "status": "open",
  "reports": [
    {
      "id": "sha256:ee5f5166284d10931bc3541f15a2eb11198b44721ba7da6e2395ec861fa932f6",
      "created_at": "2026-10-08T08:48:34.627317+00:00",
      "report": {
        "report_key": "spec-panel/module.spec-review/3",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Several requirements combine independently decidable obligations",
        "description": "Several requirements combine independently decidable obligations under one SHALL. The finding-path requirement is the clearest instance, combining retry, rejection, rejection evidence and preservation of other findings.\n\nSuggested repair: Give the independent actions separate requirement identities, preserving ordering, eligibility and failure conditions. Also separate blank-earlier normalization from nonblank validation, and no-Issues retention from disclosure, without duplicating existing canonical obligations.",
        "impact": "Retry, rejection, preservation, normalization, validation and disclosure can fail independently but cannot be assessed as separate obligations under their current identities.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/method/spec-review/requirements.md at req.spec-review.finding-path, line 77 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"The Operation SHALL resume a worker whose findings name a path that is not one of the workspace once, with those paths to correct, and then report no finding whose path still does not hold, listing it as rejected with the reason and still reporting every other finding of that worker.\" req.spec-review.blank-earlier also combines blank normalization with checking other references; req.spec-review.reports-issues combines retaining findings without Issues with disclosing that they were not recorded.\n\nThe panel's chair merged r1.4, r2.3, r3.4 and verified: Verified all three cited requirements. These are independent actions, not merely conditions of a single promise. Medium severity reflects the assessment and implementation ambiguity; obvious-fix follows the Protocol's explicit requirement to separate joined obligations while preserving their meaning.",
        "owner_target_id": "module.spec-review",
        "evidence": [
          {
            "path": "specs/concorde/method/spec-review/requirements.md",
            "description": "req.spec-review.finding-path, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec-review",
        "context_id": "sha256:4a1a46c4aec1a2e9ff732fb154c43ba4102165335de958b0848f3292eba777e5",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
