# I-e9c504f48b815a62aefa27ccd9bebd2c

```json
{
  "schema_version": 4,
  "id": "I-e9c504f48b815a62aefa27ccd9bebd2c",
  "status": "open",
  "reports": [
    {
      "id": "sha256:abcff563c03ac4ae55cf726b216f48461ef7a1bc6f0a98c960b543041a2d2a67",
      "created_at": "2026-10-08T09:36:40.237438+00:00",
      "report": {
        "report_key": "spec-panel/module.workers/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Retry requirement omits the guard against replaying changed work",
        "description": "The retry requirement and decision table omit the procedure's session-or-unchanged-worktree condition. A clean audit permits changes inside rw and therefore does not supply the missing condition.\n\nSuggested repair: Add the existing session-or-unchanged-worktree condition to req.workers.transient-retried and the retry row of the Rounds table. Add a scenario where a transient failure leaves permitted changes but no session identifier, confirming that the run ends without retrying.",
        "impact": "An implementer following the requirement or decision table would restart a sessionless worker over permitted changes, although the retry procedure excludes that case. Restarting from the brief could replay work without its session history.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/worker-harness/workers/launch.md at req.workers.transient-retried, line 913 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: req.workers.transient-retried requires a retry when the process ends with a transient model-service error, the audit is clean, no valid result was returned and retries remain. The Retries procedure additionally requires: “The round named a session to continue, or the worktree has no change since the snapshot.” The first row of the Rounds table also omits this guard. The Audit table explicitly permits “a changed or new file whose level is `rw`”.\n\nThe panel's chair merged r1.1, r2.1, r3.1 and verified: Verified the requirement, ordered Rounds table, retry eligibility list and audit definition. All three reports describe the same omission. Medium severity reflects a transient-failure edge case; preferred-fix applies because restoring the existing procedural guard is the clearest repair without changing the intended retry policy. No earlier Issue covers this guard.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "req.workers.transient-retried, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.workers",
        "context_id": "sha256:25bf3ca79f4b812d672ebebd9c10145532654c754fdee7567f552ea2f5639d06",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
