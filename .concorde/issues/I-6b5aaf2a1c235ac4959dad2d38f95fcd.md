# I-6b5aaf2a1c235ac4959dad2d38f95fcd

```json
{
  "schema_version": 4,
  "id": "I-6b5aaf2a1c235ac4959dad2d38f95fcd",
  "status": "open",
  "reports": [
    {
      "id": "sha256:ecb9fb563a98f5a05d411bec06922f59c73a17c8b1be54f65363efecf94103ef",
      "created_at": "2026-10-08T08:14:59.585349+00:00",
      "report": {
        "report_key": "spec-panel/module.issues/1",
        "tier": "obvious-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "The entry assigns command reports to the wrong reporting Module",
        "description": "The entry assigns all command-recorded reports to the root Module, contradicting the ordinary owner-based attribution and caller-supplied provenance rules.\n\nSuggested repair: Replace the unconditional attribution with a link to the provenance contract. Explain that command-supplied provenance uses the named owner, uses the root for a null owner where available, and preserves caller-supplied reporting Module with --provenance.",
        "impact": "A reader implementing ordinary reporting or filtering by reporting Module can assign reports to the wrong Module and obtain incorrect listings.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/issues/module.md at concept.issue-report, line 112 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: module.md says, \"For a command-recorded report, the reporting Module is the root Module.\" interface.md's Provenance section instead says, \"Otherwise, the report command sets the reporting Module to the report's owner.\" scenario.issues.command-report expects \"the owner as reporting Module\", and scenario.issues.command-report-provenance expects exactly the supplied provenance.\n\nThe panel's chair merged r1.1, r2.1, r3.1 and verified: Verified the entry against the provenance table, command behavior and both scenarios. High because attribution affects normal reporting; obvious-fix because the canonical interface and scenarios consistently establish the repair.",
        "owner_target_id": "module.issues",
        "evidence": [
          {
            "path": "specs/concorde/issues/module.md",
            "description": "concept.issue-report, cited by the obligations finding"
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
