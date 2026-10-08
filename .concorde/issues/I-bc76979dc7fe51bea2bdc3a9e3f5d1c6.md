# I-bc76979dc7fe51bea2bdc3a9e3f5d1c6

```json
{
  "schema_version": 4,
  "id": "I-bc76979dc7fe51bea2bdc3a9e3f5d1c6",
  "status": "open",
  "reports": [
    {
      "id": "sha256:bb96e93840d27bd0ca9ecb62d38906016981ea331b839f7e231e71637142dbc6",
      "created_at": "2026-10-08T07:52:10.152403+00:00",
      "report": {
        "report_key": "spec-panel/module.execution/6",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Checkout cleanup and residual reporting share one requirement",
        "description": "One SHALL statement joins checkout cleanup and reporting unsuccessful cleanup, which have independent observable outcomes. Its absolute removal wording also obscures the explicitly supported case where leftovers remain.\n\nSuggested repair: Give cleanup and failure reporting separate requirement identities. Require the documented removal procedure before result publication in the first, allowing its documented failure outcome. Require checkout-not-removed evidence describing the removal outcome, leftovers and recovery in the second, preserving unchanged result status.",
        "impact": "Cleanup and residual reporting cannot be evaluated as separate requirement units, and supported cleanup failures appear to violate an unconditional promise of successful removal.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/execution/requirements.md at req.execution.checkout-removed, line 250 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “Whatever ended an unbound run's steps, the runner SHALL remove the run's checkout before it writes the run's result, and name in that result whatever of the checkout it could not remove.” runner.md's Unbound checkout step 5 specifies Git removal, direct cleanup after refusal, and checkout-not-removed evidence without changing result status.\n\nThe panel's chair merged r1.6, r2.3, r3.5 and verified: Verified the combined statement and the explicit cleanup-failure behavior in runner.md and scenario.execution.unbound-checkout-removed. Medium severity because this affects a cleanup failure case. Obvious-fix because separating the two obligations and retaining the already specified fallback and evidence behavior requires no new policy.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "specs/concorde/execution/requirements.md",
            "description": "req.execution.checkout-removed, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.execution",
        "context_id": "sha256:0a3bf4281201b623510ea306359717d9cdd4a2c521a0bee0940eb6449eaefa39",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
