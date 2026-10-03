# I-8cb9eeb6947b5fa7b79980d3e1bcceb7

```json
{
  "schema_version": 4,
  "id": "I-8cb9eeb6947b5fa7b79980d3e1bcceb7",
  "status": "open",
  "reports": [
    {
      "id": "sha256:088baaadea3bf89e12e9c9fc546b7bb2e2b8e4c7ed391d98c5616dfb417b3626",
      "created_at": "2026-10-03T05:04:30.308181+00:00",
      "report": {
        "report_key": "tasks-review-record-transaction-overpromise",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "Tasks promises a concurrent unlocked record change is never overwritten, which compare-then-rename cannot guarantee",
        "description": "req.tasks.record-transactions (requirements.md:20-27) says a concurrent change is 'never overwritten', and module.md:738-745 extends this to a process that did not take the task lock. update (store.py:580-610) compares bytes and then os.replace's; a write between the comparison and the rename is overwritten, which the Kernel's file transaction contract also excludes. Every supported writer holds the task lock, so this is only reachable by a hand edit. Fix: align the wording with the Kernel's precondition that writers hold the lock.",
        "impact": "No practical harm; the promise is stronger than any mechanism provides.",
        "basis": "Finding of the module.tasks reviewer in code_review run r-20261003T043108-code_review-b638d3d3, verified against the code and Specs by the task session of task parts-review.",
        "owner_target_id": "module.tasks",
        "evidence": [
          {
            "path": "specs/concorde/coordination/tasks/requirements.md",
            "description": "lines 20-27: never overwritten"
          },
          {
            "path": "specs/concorde/coordination/tasks/module.md",
            "description": "lines 738-745: unlocked writers"
          },
          {
            "path": "src/concorde/coordination/tasks/store.py",
            "description": "lines 580-610: compare then replace"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-922a9064-3893-4b8e-a7ac-c7ae4168c025",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.tasks",
        "context_id": "sha256:1d5cfc2a2a7ba74b163c0a7da2044601cb98d3bb39fa931e4f515946b2ee70f4",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": []
}
```
