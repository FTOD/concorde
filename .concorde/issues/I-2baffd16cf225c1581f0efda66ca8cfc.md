# I-2baffd16cf225c1581f0efda66ca8cfc

```json
{
  "schema_version": 4,
  "id": "I-2baffd16cf225c1581f0efda66ca8cfc",
  "status": "open",
  "reports": [
    {
      "id": "sha256:5774e23dbe6e56144e20770e40aab55b75384a7f008666b2312e6da1fcdf238f",
      "created_at": "2026-10-08T07:16:51.349889+00:00",
      "report": {
        "report_key": "spec-panel/module.checks/2",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "Align the overview's freshness interval with the service procedure",
        "description": "The entry describes one measurement interval around all checks of a Module, while the precise service procedure describes one interval around each check. These descriptions promise different freshness guarantees.\n\nSuggested repair: Align the overview prose and workflow with the service's per-check sequence: measure, run one check, measure again, compare, and only then proceed. Explain that this does not establish one shared revision for all checks, and add a scenario covering a change between checks.",
        "impact": "A reader following the overview implements a different freshness window from the precise service procedure. A change between two checks can invalidate the Module-wide interval while escaping both per-check comparisons.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/execution/checks/module.md at One call of the check service, line 209 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The entry says “For each Module” the service “measures the inputs”, “runs each check in the boundary”, then “measures again”. The diagram has `logs -> boundary: \"next check\"` and `logs -> after: \"last check of the Module\"`. In service.md, step 5 instead begins “For each kept check, the service computes its measured digest”, with remeasurement in step 7.\n\nThe panel's chair merged r1.6, r2.1, r3.7 and verified: Verified both the entry's prose and workflow against service.md steps 5–7. High severity because the disagreement affects the main evidence guarantee, though the precise procedure provides a way out. Preferred-fix because aligning the overview with that explicit procedure repairs the inconsistency without inventing a broader guarantee.",
        "owner_target_id": "module.checks",
        "evidence": [
          {
            "path": "specs/concorde/execution/checks/module.md",
            "description": "One call of the check service, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.checks",
        "context_id": "sha256:922b60d46218c71ca9ae9bdbd2f9817333e2b02167de201b7428210220ee3461",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
