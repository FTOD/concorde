# I-fd7396da4b9a5920af25adabaec726f1

```json
{
  "schema_version": 4,
  "id": "I-fd7396da4b9a5920af25adabaec726f1",
  "status": "open",
  "reports": [
    {
      "id": "sha256:f39b236fed1fb700939e9e7467daa085e0124c269ea6e5992e0b135d9345c95e",
      "created_at": "2026-10-08T08:27:10.207038+00:00",
      "report": {
        "report_key": "spec-panel/module.main-session/7",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "Project-review guidance lacks its defining provider context",
        "description": "The scenario demands concrete project_review provider knowledge that the Module neither supplies nor selects. It gives no canonical source for the required review parts, worker identities and record behaviour.\n\nSuggested repair: Declare and select the provider that owns project_review, including its operation and review-record promises. Explain its normal invocation and purpose in the entry and link the scenario to the definitions of worker identities, skip behaviour and record handling.",
        "impact": "A guidance author cannot determine the required worker identities, review scope or review-record semantics from the selected Specs.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/coordination/main-session/scenarios.md at scenario.main-session.project-review, line 553 by the context criterion of the Protocol's Evaluating a Spec; the Specs read: The scenario requires guidance to state “which parts the review runs, with their worker ids”, that it “skips what is unchanged since a review last judged it” using a review record, and that “`--full` reviews everything again”. The Module's uses/includes declarations select no Project review provider, and the entry's Questions without a task section does not explain project_review.\n\nThe panel's chair merged r1.5, r2.5, r3.8 and verified: Verified the complete scenario, entry and provider declarations against the supplied context inventory. Medium severity because whole-project review is a secondary use; preferred-fix because selecting and explaining the existing provider is preferable to inventing or duplicating its contract.",
        "owner_target_id": "module.main-session",
        "evidence": [
          {
            "path": "specs/concorde/coordination/main-session/scenarios.md",
            "description": "scenario.main-session.project-review, cited by the context finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.main-session",
        "context_id": "sha256:c40333ef11711b6c8c620738011559fa55361a3f87596146fb95d1e0d22788ae",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
