# I-31ff3dc0baf25f8e966204bfc2a0bdca

```json
{
  "schema_version": 4,
  "id": "I-31ff3dc0baf25f8e966204bfc2a0bdca",
  "status": "open",
  "reports": [
    {
      "id": "sha256:f6f8c0490da1aa98d12666509766833301d17de3d78bb693240e767bc17204eb",
      "created_at": "2026-10-08T07:33:39.426949+00:00",
      "report": {
        "report_key": "spec-panel/module.delivery/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The atomicity requirement omits its documented failure exceptions",
        "description": "The canonical failure requirement promises unconditional restoration and complete changed-path reporting. The entry expressly supports failures of both operations, leaving the requirement inconsistent with the detailed recovery policy.\n\nSuggested repair: State the established restoration attempts and their failure outcomes in the canonical obligations. Preserve the dependency on restoring the tree before restoring its additional index state, require reports of failed restorations, and permit an explicit measurement-failure report when changed paths cannot be determined. Qualify corresponding overview promises and add observable recovery-failure scenarios.",
        "impact": "A reader cannot assess recovery consistently: the requirement guarantees complete restoration and path enumeration even when the documented recovery procedure cannot provide them.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/method/delivery/requirements.md at req.delivery.atomic, line 120 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “When staging or the commit fails, Delivery SHALL restore the index to the state the readiness examined, leave the worktree as it is, and name in the run's summary and error every worktree path whose mode or content is no longer what the readiness examined.” The entry instead says “They then say the index is not as the readiness examined it” and “When the worktree cannot be measured again, the run's summary and detail say so.”\n\nThe panel's chair merged r1.2, r2.2, r3.2 and verified: Verified that module.md explicitly handles failed tree restoration, partial flag or intent-to-add restoration, and failed remeasurement, while the canonical requirement has none of these qualifications. Medium severity covers recovery edge cases. Preferred-fix aligns the requirement with the already described recovery policy.",
        "owner_target_id": "module.delivery",
        "evidence": [
          {
            "path": "specs/concorde/method/delivery/requirements.md",
            "description": "req.delivery.atomic, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.delivery",
        "context_id": "sha256:b7f339a7d9a3c47d381807c63ba70da0bf47aa10ace6491f903f9d104d8d4af5",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
