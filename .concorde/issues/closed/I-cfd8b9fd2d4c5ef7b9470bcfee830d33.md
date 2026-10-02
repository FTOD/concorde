# I-cfd8b9fd2d4c5ef7b9470bcfee830d33

```json
{
  "schema_version": 3,
  "id": "I-cfd8b9fd2d4c5ef7b9470bcfee830d33",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:9621e56570560fd20912b5b0ece26ab575e0986cb52d6f533824d39bbbde3fe2",
      "created_at": "2026-10-01T04:49:45.227059+00:00",
      "report": {
        "report_key": "module.issues/14",
        "tier": "suggestion",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "Remove Tracing's obsolete worktree-local Issue-lock description",
        "description": "Tracing retains a worktree-local Issue-lock exception inconsistent with its own lock table and the Issues contract.\n\nSuggested repair: Remove the Issue-lock exception and state that Issue writes use the primary worktree's merge lock. Keep the unbound run and its run lock as the worktree-local case described by the Locks section.\n\nOther Modules concerned: module.issues, module.tasks",
        "impact": "A reader can infer a worktree-local Issue lock that would not serialize writes with primary-worktree merges.",
        "basis": "spec_panel run r-20261001T044130-spec_panel-5cc8e2f7 judged specs/concorde/tracing/contracts.md at layout, line 475 by the consistency criterion of the Protocol's Evaluating a Spec; the Specs read: Tracing's Layout says everything is in the primary worktree except \"the unbound runs and the Issue lock\", which are worktree-local. Its Locks table assigns every Issue write to merge.lock, agreeing with Issues' \"primary worktree's merge lock, `.concorde/locks/merge.lock`\".\n\nThe panel's chair merged a1.4 and verified: Verified Tracing's Layout and Locks sections against Issues. The correction belongs to another Module, so this report is advisory under the chair's boundary.",
        "owner_target_id": "module.tracing",
        "evidence": [
          {
            "path": "specs/concorde/tracing/contracts.md",
            "description": "layout, cited by the consistency finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T044130-spec_panel-5cc8e2f7",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.issues",
        "context_id": "sha256:6291b55fcdd800b51ef5485b3ec772ac4ef0b52e4fcc70c31492b4ad2b64c074",
        "change_id": "panel-architects",
        "head": "aa79fa2f3cacda1ac2f53dcc9dc8dce677ee824a"
      }
    },
    {
      "id": "sha256:64362624936e6f5c8dfe31897177598dd3e42d0818d1ca5ce0e82ece88702617",
      "created_at": "2026-10-01T14:47:31.855501+00:00",
      "report": {
        "report_key": "module.issues/14--severity",
        "tier": "suggestion",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "Remove Tracing's obsolete worktree-local Issue-lock description",
        "description": "Tracing retains a worktree-local Issue-lock exception inconsistent with its own lock table and the Issues contract.\n\nSuggested repair: Remove the Issue-lock exception and state that Issue writes use the primary worktree's merge lock. Keep the unbound run and its run lock as the worktree-local case described by the Locks section.\n\nOther Modules concerned: module.issues, module.tasks",
        "impact": "A reader can infer a worktree-local Issue lock that would not serialize writes with primary-worktree merges.",
        "basis": "spec_panel run r-20261001T044130-spec_panel-5cc8e2f7 judged specs/concorde/tracing/contracts.md at layout, line 475 by the consistency criterion of the Protocol's Evaluating a Spec; the Specs read: Tracing's Layout says everything is in the primary worktree except \"the unbound runs and the Issue lock\", which are worktree-local. Its Locks table assigns every Issue write to merge.lock, agreeing with Issues' \"primary worktree's merge lock, `.concorde/locks/merge.lock`\".\n\nThe panel's chair merged a1.4 and verified: Verified Tracing's Layout and Locks sections against Issues. The correction belongs to another Module, so this report is advisory under the chair's boundary. Severity medium assessed by the main agent on 2026-10-01: The obsolete text can lead an implementer to a worktree-local Issue lock that would not serialize Issue writes with merges.",
        "owner_target_id": "module.tracing",
        "evidence": [
          {
            "path": "specs/concorde/tracing/contracts.md",
            "description": "layout, cited by the consistency finding"
          }
        ],
        "severity": "medium",
        "issue_id": "I-cfd8b9fd2d4c5ef7b9470bcfee830d33",
        "expected_revision": "sha256:a8625e8751c67b633ec954483e2fc39a71b830501a188bf8dfa77838152e6a9c"
      },
      "source": {
        "invocation_id": "cli-77c8e8e7-2ec0-4f29-80d8-98d2df0d9c47",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.tracing",
        "context_id": "sha256:faf611ab5bdd47f3ab93968932072ec605e527fb468e96a4f6c20a419e8f0f8c",
        "change_id": null,
        "head": "71e16716c3515dd5e1f79bd502b776859da3857f"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-small-modules, merged into the primary branch at 2c71660ef9b2c42840e3089f6eeaa62036e57b35.",
      "evidence": [
        "merge commit 2c71660ef9b2c42840e3089f6eeaa62036e57b35",
        "task fix-small-modules"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-02T02:16:58.933446+00:00"
    }
  ]
}
```
