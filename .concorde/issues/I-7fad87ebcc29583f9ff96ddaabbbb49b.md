# I-7fad87ebcc29583f9ff96ddaabbbb49b

```json
{
  "schema_version": 4,
  "id": "I-7fad87ebcc29583f9ff96ddaabbbb49b",
  "status": "open",
  "reports": [
    {
      "id": "sha256:4c7cf51d05c514292394b7569b70f1447dc53b0218b5dfece1695afe69b177c6",
      "created_at": "2026-10-06T20:17:35.542180+00:00",
      "report": {
        "report_key": "spec-panel/module.project-review/5",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Filtered report ordering contradicts the report contract",
        "description": "The narrowed scenario requires argument order while the report contract requires registry order. Its single-Module setup cannot exercise the multi-Module ordering claim.\n\nSuggested repair: Retain the canonical report contract's registry order and revise the scenario accordingly. Exercise ordering with at least two selected Modules supplied in reverse registry order, separately from the single-Module verdict-scope case.",
        "impact": "An implementer and an acceptance-test author can require opposite output orders for the same filtered invocation.",
        "basis": "project_review run r-20261006T201155-project_review-dee010b9 judged specs/concorde/method/project-review/scenarios.md at scenario.project-review.narrowed, line 72 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The scenario says “when `--modules` names Modules out of the registry's order, the result lists them in that order”. The report contract says “modules has one item per covered Module in the registry's order.”\n\nThe panel's chair merged r1.5, r2.4 and verified: Verified the scenario and contract.project-review.report at line 1881. The scenario's setup selects Module B alone, so it also cannot demonstrate its ordering assertion. This is distinct from the earlier filtered-verdict Issue, which concerns which owners count. Medium severity reflects filtered multi-Module usage; preferred-fix applies because aligning with the canonical report contract is the strongest repair.",
        "owner_target_id": "module.project-review",
        "evidence": [
          {
            "path": "specs/concorde/method/project-review/scenarios.md",
            "description": "scenario.project-review.narrowed, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261006T201155-project_review-dee010b9",
        "agent": "operation",
        "operation": "project_review",
        "phase": "spec-panel",
        "target_id": "module.project-review",
        "context_id": "sha256:6ad3677af15f07309512a1abd3628bae74ad989aa51a6c1df9201f11dba948a3",
        "change_id": "project-review",
        "head": "19986279fe528539e7fa404fbb12ff27d342cf61"
      }
    }
  ],
  "dispositions": []
}
```
