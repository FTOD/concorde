# I-96aaf5e7bb7a52b0b3fe1a23bb69bee1

```json
{
  "schema_version": 4,
  "id": "I-96aaf5e7bb7a52b0b3fe1a23bb69bee1",
  "status": "open",
  "reports": [
    {
      "id": "sha256:08db6873f7d34aed8ee6b1c014195015197c8198f9cec4a43548a7f3c75eaf90",
      "created_at": "2026-10-13T20:33:56.852553+00:00",
      "report": {
        "report_key": "code-review/module.workers/5",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Progress can omit the current tool throughout a long-running call",
        "description": "Throttled progress updates are dropped rather than deferred. The latest tool call is not guaranteed to reach status.json while that call is running.\n\nSuggested repair: Coalesce throttled actions and flush the pending latest action when the one-second interval expires, with synchronization and cancellation at finish. Test a call arriving inside the throttle interval followed by no further events.",
        "impact": "During a long-running tool call, observers can see the previous tool or null for minutes, precisely when the progress file is needed to show what the worker is doing.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/worker_harness/progress.py:54-73 against req.workers.progress and reported a violation: Progress.action() updates last_action in memory but writes only if at least one second has elapsed since _last_action_write. Every phase write resets that timestamp, and there is no delayed flush. A tool call immediately after phase('worker'), or immediately after another action write, can therefore remain unpublished until another event or phase change.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/progress.py",
            "description": "lines 54-73, shown by the violation finding"
          },
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "defines req.workers.progress, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.workers",
        "context_id": "sha256:d26f3cb0c72a7d5a7397818fed5c878790107966ca3a23d67fd3db829894a593",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
