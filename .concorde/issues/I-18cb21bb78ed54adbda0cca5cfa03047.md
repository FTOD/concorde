# I-18cb21bb78ed54adbda0cca5cfa03047

```json
{
  "schema_version": 4,
  "id": "I-18cb21bb78ed54adbda0cca5cfa03047",
  "status": "open",
  "reports": [
    {
      "id": "sha256:3e3bed3ba559c4289e03cd022669b22c950fa4497f0b57912d791ce1f7549df3",
      "created_at": "2026-10-08T08:19:51.011055+00:00",
      "report": {
        "report_key": "spec-panel/module.kernel/2",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "Include the unfinished-merge guard in the normal example",
        "description": "The representative write-and-commit interaction omits the unfinished-merge marker guard required elsewhere in the same entry.\n\nSuggested repair: After acquiring the merge lock, have the example read the marker before changing files. Proceed only when it is absent; otherwise explain the refusal with the marker account or unreadable-file error and link the canonical contract.",
        "impact": "A consumer following the normal example can commit while a crashed merge remains undecided.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/kernel/module.md at Purpose, line 61 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: The example says “While it holds the merge lock, the part applies a file transaction below the primary worktree” and “The part then commits the file.” Later the entry says “Every other part that commits on the primary branch reads the marker while it holds the merge lock” and refuses when it is present or unreadable.\n\nThe panel's chair merged r3.3 and verified: Verified that the example contains no marker check and that the later marker explanation explicitly says the lock alone cannot preserve the guarantee across a crash. High severity reflects an incorrect main flow with a correction discoverable later; the existing guard supplies the preferred fix.",
        "owner_target_id": "module.kernel",
        "evidence": [
          {
            "path": "specs/concorde/kernel/module.md",
            "description": "Purpose, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.kernel",
        "context_id": "sha256:38fb97ee416d835df8b93ba25ef63df191efde71b842d7f3e68c655402335962",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
