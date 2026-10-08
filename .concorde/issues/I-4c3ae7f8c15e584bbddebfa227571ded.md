# I-4c3ae7f8c15e584bbddebfa227571ded

```json
{
  "schema_version": 4,
  "id": "I-4c3ae7f8c15e584bbddebfa227571ded",
  "status": "open",
  "reports": [
    {
      "id": "sha256:39b2b13d69f019fb928b1ce7ae1e9eb2b05315fa2235cf8b1f59a0d5aaf91bba",
      "created_at": "2026-10-08T03:16:45.405500+00:00",
      "report": {
        "report_key": "spec-panel/module.adoption/4",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "New-child surveys conflict with the base-metadata failure rule",
        "description": "The scenario permits surveying a child created since the workspace base commit, although its metadata is absent at that commit and the error contract requires failure in that case.\n\nSuggested repair: Define the treatment of a surveyed Module absent at the base commit. If new children may be surveyed, distinguish legitimate absence from unreadable or corrupt existing metadata. Align the survey procedure, error table and scenario with that decision.",
        "impact": "An implementer cannot determine whether surveying a newly scaffolded child proceeds or fails before worker launch.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 judged specs/concorde/method/adoption/scenarios.md at scenario.adoption.survey-after-scaffold, line 64 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The scenario says the scaffold “created `module.checkout` and `module.inventory`” and then promises that “a survey of `module.checkout`, to which no scaffold wrote, runs as usual in the same worktree.” contracts.md's `specs_unloadable` row requires failure when “the surveyed Module's entry metadata at the workspace's base commit cannot be read.”\n\nThe panel's chair merged r1.2, r2.3, r3.3 and verified: Verified the scenario's newly created child and the unconditional base-metadata failure in the error table and survey step table. Medium severity for the nested-survey case. Decision-needed because the Specs must choose how legitimate absence at the base differs from a metadata read failure.",
        "owner_target_id": "module.adoption",
        "evidence": [
          {
            "path": "specs/concorde/method/adoption/scenarios.md",
            "description": "scenario.adoption.survey-after-scaffold, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.adoption",
        "context_id": "sha256:419d153fe4bca21c25de5e5fdb0218f7b6c5b667170c6bb3a6e7cf45ffeaea5d",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
