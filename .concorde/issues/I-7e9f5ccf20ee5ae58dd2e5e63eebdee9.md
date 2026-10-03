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
    },
    {
      "id": "sha256:cedcba55e163bfc78940b866e2684888a444b726946eb13ec34ba135879afa86",
      "created_at": "2026-10-03T05:19:20.508060+00:00",
      "report": {
        "issue_id": "I-7e9f5ccf20ee5ae58dd2e5e63eebdee9",
        "report_key": "verify/module.understanding/2",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "owner_target_id": "module.understanding",
        "title": "plan_review accepts duplicate finding ids from its reviewer",
        "description": "FINDING_SCHEMA checks only the F<n> pattern and inconsistencies() never checks that the reviewer's current finding ids are distinct. When a reviewer emits two findings named F1, the next iteration's iteration_problems() and inconsistencies() count answers and responses per id, so one answer and one response to F1 pass for both findings. The obvious fix is to reject duplicate ids as an inconsistent review.",
        "impact": "Reachable only when the reviewer misbehaves by repeating an id; then one of two findings can be settled without its own answer. The plan is reviewed afresh in the next iteration, so the problem is likely to resurface.",
        "basis": "contract.understanding.plan-review (each finding has a run-local id; every finding of the previous iteration answered exactly once).",
        "evidence": [
          {
            "path": "src/concorde/method/understanding/plan_review.py",
            "description": "FINDING_SCHEMA, iteration_problems, inconsistencies"
          }
        ],
        "expected_revision": "sha256:38a2d56e453fb1924a6fda0673ea3597dff9e1937624eb24b25307068eedbd0d"
      },
      "source": {
        "invocation_id": "cli-e02e908f-eb4a-4897-bfe4-830fe2b21df7",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.understanding",
        "context_id": "sha256:1d5cfc2a2a7ba74b163c0a7da2044601cb98d3bb39fa931e4f515946b2ee70f4",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": []
}
```
