# I-7e9f5ccf20ee5ae58dd2e5e63eebdee9

```json
{
  "schema_version": 4,
  "id": "I-7e9f5ccf20ee5ae58dd2e5e63eebdee9",
  "status": "open",
  "reports": [
    {
      "id": "sha256:11affa4428c155a652045e4783c8b9c02a055c2910b487de137fda6bec3bb1a7",
      "created_at": "2026-10-03T05:05:45.706376+00:00",
      "report": {
        "report_key": "module.understanding/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Reject duplicate plan-review finding identities",
        "description": "The host accepts multiple current findings with the same id. Subsequent iteration validation treats these distinct findings as the same answer target, so accepting or settling one can also settle another without its own answer.\n\nSuggested repair: Reject duplicate finding ids with inconsistent_review before publishing a report, listing each duplicate without rewriting the reviewer's findings. Add a regression test proving that two distinct findings named F1 cannot become an ok previous iteration.",
        "impact": "An ok review can contain distinct problems that callers cannot address independently. In the next iteration, one answer and one response can silently stand for both problems, undermining the promised discussion of every finding.",
        "basis": "code_review run r-20261003T045929-code_review-a21d3726 (module review) judged src/concorde/method/understanding/plan_review.py:62-88, src/concorde/method/understanding/plan_review.py:240-253, src/concorde/method/understanding/plan_review.py:439-479 against contract.understanding.plan-review and reported a defect: The contract assigns each finding \"a run-local id\" and requires answers and responses for every previous finding. FINDING_SCHEMA checks only the ^F[0-9]+$ pattern. inconsistencies() checks previous links and bound Modules but never duplicate current ids; iteration_problems() counts answers by id, so one answer to F1 satisfies both entries when two previous findings share F1.",
        "owner_target_id": "module.understanding",
        "evidence": [
          {
            "path": "src/concorde/method/understanding/plan_review.py",
            "description": "lines 62-88, shown by the defect finding"
          },
          {
            "path": "src/concorde/method/understanding/plan_review.py",
            "description": "lines 240-253, shown by the defect finding"
          },
          {
            "path": "src/concorde/method/understanding/plan_review.py",
            "description": "lines 439-479, shown by the defect finding"
          },
          {
            "path": "specs/concorde/method/understanding/contracts.md",
            "description": "defines contract.understanding.plan-review, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T045929-code_review-a21d3726",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.understanding",
        "context_id": "sha256:dd26e79dc22ce5e4c04246eb96cd41ba3f2fb74412dee6be699ec971931ab0ea",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": []
}
```
