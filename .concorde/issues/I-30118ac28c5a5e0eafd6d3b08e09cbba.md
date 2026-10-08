# I-30118ac28c5a5e0eafd6d3b08e09cbba

```json
{
  "schema_version": 4,
  "id": "I-30118ac28c5a5e0eafd6d3b08e09cbba",
  "status": "open",
  "reports": [
    {
      "id": "sha256:bb66b9aaef436d002841c955159509f1feec3861a90120b7c037c4d26627ceef",
      "created_at": "2026-10-08T08:15:00.640965+00:00",
      "report": {
        "report_key": "spec-panel/module.issues/5",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Missing-tier ordering can override severity ordering",
        "description": "The requirement combines missing severity and missing tier into a global last-place rule. That loses the same-severity qualification for missing tiers and conflicts with severity-first ordering.\n\nSuggested repair: State separately that missing severity follows all known severities and missing tier follows known tiers only within the same severity group. Preserve the chronological and identity tie-breakers of list_issues.",
        "impact": "A legacy critical Issue without a tier can sort below a low-severity tiered Issue under one reading, whereas the interface keeps it in the critical group.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/issues/requirements.md at req.issues.list-by-severity, line 250 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The requirement ends its ordering list with \"Issues without a severity or tier after every one with it.\" The list_issues contract instead places \"every row without a severity after those with one and every row without a tier after those of its severity with one\". Version-2 records may lack tier and severity independently.\n\nThe panel's chair merged r1.5, r2.7, r3.4 and verified: Verified both ordering rules and the legacy-record exceptions. Medium because this affects legacy records with missing tier. Obvious-fix because the canonical interface supplies the precise missing qualification.",
        "owner_target_id": "module.issues",
        "evidence": [
          {
            "path": "specs/concorde/issues/requirements.md",
            "description": "req.issues.list-by-severity, cited by the obligations finding"
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
