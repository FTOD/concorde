# I-8ccddc9df0295681a99a4dceebdc8db9

```json
{
  "schema_version": 4,
  "id": "I-8ccddc9df0295681a99a4dceebdc8db9",
  "status": "open",
  "reports": [
    {
      "id": "sha256:aee765e2d8a7e4f01e372715108d966f3d1aff175c7fd80e5750b580ec15c2c8",
      "created_at": "2026-10-08T09:21:22.763525+00:00",
      "report": {
        "report_key": "code-review/module.tasks/4",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Outside-worktree audit skips ended tasks whose folders are still current",
        "description": "The outside-worktree audit treats all current task folders as live tasks, including records already stored closed or failed. Such ended tasks are skipped instead of being checked for changed_outside.\n\nSuggested repair: Build the live-worktree set only from records whose stored state is not closed or failed. Add a case with an ended record still current and an existing dirty worktree.",
        "impact": "A worktree restored or left present for a task whose close has not finished moving its folder can contain uncommitted changes without blocking another merge, even though no active task accounts for those changes.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/coordination/tasks/merge.py:518-540 against req.tasks.merge-nothing-outside and reported a violation: _elsewhere constructs live from every current record except the merging task, without excluding closed or failed records. It then skips any ended record whose worktree occurs in live. Thus an ended task still in .concorde/tasks excludes its own worktree from the audit.",
        "owner_target_id": "module.tasks",
        "evidence": [
          {
            "path": "src/concorde/coordination/tasks/merge.py",
            "description": "lines 518-540, shown by the violation finding"
          },
          {
            "path": "specs/concorde/coordination/tasks/requirements.md",
            "description": "defines req.tasks.merge-nothing-outside, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.tasks",
        "context_id": "sha256:371254edb81afb6f42aa4ce6761c1921cf5475dad4c7379cdf74220829d75420",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
