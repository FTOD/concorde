# I-e72a9d23c8a050f3ad92ecf3d63aae2c

```json
{
  "schema_version": 4,
  "id": "I-e72a9d23c8a050f3ad92ecf3d63aae2c",
  "status": "open",
  "reports": [
    {
      "id": "sha256:f9ce6af62051accad3cdbe604b06d9a65f226f1a9bf93e4c7f9deeb9dac0e831",
      "created_at": "2026-10-08T08:27:09.690122+00:00",
      "report": {
        "report_key": "spec-panel/module.main-session/5",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The workflow explanation drops the local-repair exception",
        "description": "The entry drops the local-repair condition from workflow escalation and therefore describes a stronger rule than the requirement and scenario.\n\nSuggested repair: State that a task session escalates a non-ok workflow result when it cannot repair it within the task, linking req.main-session.task-session-workflow-failure. Preserve the separately stated mandatory escalation of awaiting_decision results.",
        "impact": "Guidance derived from the entry would escalate locally repairable failures and unnecessarily interrupt task-local work.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/coordination/main-session/module.md at Workflows, line 659 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The entry says, “The session escalates a result that is not `ok` with the saved workflow result as `--error-file`.” req.main-session.task-session-workflow-failure limits this to a result “that is not `ok` and that it cannot repair within the task”. The task-session-workflow scenario retains the same limitation.\n\nThe panel's chair merged r1.3, r2.7, r3.6 and verified: Verified the entry, canonical requirement and workflow scenario. Medium severity because the contradiction affects recoverable workflow failures; obvious-fix because restoring the existing repairability condition resolves it without a new policy decision.",
        "owner_target_id": "module.main-session",
        "evidence": [
          {
            "path": "specs/concorde/coordination/main-session/module.md",
            "description": "Workflows, cited by the obligations finding"
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
