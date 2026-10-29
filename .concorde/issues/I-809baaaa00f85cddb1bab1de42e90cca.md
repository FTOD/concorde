# I-809baaaa00f85cddb1bab1de42e90cca

```json
{
  "schema_version": 4,
  "id": "I-809baaaa00f85cddb1bab1de42e90cca",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9bc45d5f49c7028404ed88afc67f52d3d2145e66b6e9dada26b1eeef31ad9e08",
      "created_at": "2026-10-29T08:04:30.739293+00:00",
      "report": {
        "report_key": "code-review/module.tasks/2",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "A report can message the former main after a concurrent rebind",
        "description": "report follows the main session before taking the task lock, but uses that result after rereading a potentially rebound record. It discards the stale result only when its followed name equals the new recorded name, not when the session being followed changed.\n\nSuggested repair: Bind each follow result to the original main and main_session, and discard or recompute it if either changed before recording the report. Test a rebind to a different session during following.",
        "impact": "A report can be routed to the former main agent rather than the newly assigned main, and its decision-log explanation incorrectly attributes the former session chain to the new main.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 (module review) judged src/concorde/coordination/tasks/store.py:1218-1275 against req.tasks.report-followed and reported a defect: `found = follow(load_unended(...))` precedes `with task_locked(...)`. After rereading and updating the record, the sole freshness check is `found[\"main\"] == record[\"main\"]`; otherwise `addressee = found[\"main\"]` remains in use.",
        "owner_target_id": "module.tasks",
        "evidence": [
          {
            "path": "src/concorde/coordination/tasks/store.py",
            "description": "lines 1218-1275, shown by the defect finding"
          },
          {
            "path": "specs/concorde/coordination/tasks/requirements.md",
            "description": "defines req.tasks.report-followed, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.tasks",
        "context_id": "sha256:2b7f0da75454f187c11f567f3c5c280336e8c9373bb7ab776edb8c7810547650",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
