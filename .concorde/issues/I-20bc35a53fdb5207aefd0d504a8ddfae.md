# I-20bc35a53fdb5207aefd0d504a8ddfae

```json
{
  "schema_version": 4,
  "id": "I-20bc35a53fdb5207aefd0d504a8ddfae",
  "status": "open",
  "reports": [
    {
      "id": "sha256:6397ff5997679ef732effbe9ed578526d019050b61d86a606af50636233f21a6",
      "created_at": "2026-10-13T19:08:45.976171+00:00",
      "report": {
        "report_key": "spec-panel/module.main-session/6",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Requirement explanations introduce additional duties and limits",
        "description": "Several explanations introduce guidance duties or limits outside the requirement statements, sometimes with an ambiguous actor. Some cited duties are already specified in scenarios, but the primary-worktree restriction, plan placement and binding validation remain outside explicit guidance-content obligations.\n\nSuggested repair: Put the primary-worktree restriction and its exceptions in one guidance-content statement. Give plan placement and binding validation explicit guidance-content obligations. Review the primary-merge verification and commit prose similarly. Where a scenario already defines an instruction, link to it rather than duplicate it, and keep the guidance as the obligated actor.",
        "impact": "A guidance author or conformance check can satisfy the stated obligations while omitting the primary-worktree limit, plan placement, or binding validation. Switching between guidance and session subjects also obscures whether the prose requires guidance content or runtime behavior.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/coordination/main-session/requirements.md at req.main-session.tasks-own-changes, line 14 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: After the tasks-own-changes statement: “Besides such a change, only these changes are made in the primary worktree”. Other examples are “The session keeps the plan where `delivery` does not commit it” under task-session-plan-review and “It checks the binding with Spec core's `concorde spec-validation` and commits the file and the binding together” under task-session-binds-new-files.\n\nThe panel's chair merged r1.3, r1.4, r2.7 and verified: Merged the same document-wide pattern. Verified that update-merge already requires restarting ended sessions in its scenario, plan-review already covers renewed acceptance in its scenario, and file preparation already covers joint commits. Those are not missing promises. The retained gaps concern instructions and limits left only in explanatory prose. Medium severity reflects secondary actions and conformance ambiguity; promoting existing intent while linking already-defined duties is the preferred repair.",
        "owner_target_id": "module.main-session",
        "evidence": [
          {
            "path": "specs/concorde/coordination/main-session/requirements.md",
            "description": "req.main-session.tasks-own-changes, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.main-session",
        "context_id": "sha256:0ed80b308ac0561e75e38d2d2d74254612f902c574b52e3def9f4f3208531000",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
