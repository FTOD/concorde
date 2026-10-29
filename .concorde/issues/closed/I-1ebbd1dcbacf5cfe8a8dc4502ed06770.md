# I-1ebbd1dcbacf5cfe8a8dc4502ed06770

```json
{
  "schema_version": 4,
  "id": "I-1ebbd1dcbacf5cfe8a8dc4502ed06770",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:1caca57ecafdbccdfdc7369df1eb849e60309f0a2e71f9dadd26dfb6c9f6561f",
      "created_at": "2026-10-29T08:23:36.879302+00:00",
      "report": {
        "report_key": "code-review/module.workers/1",
        "tier": "obvious-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "WorkerRequest defaults to Claude Code instead of pi",
        "description": "WorkerRequest sets backend=\"claude\" when its caller omits the field, despite the specified pi default. Direct callers therefore launch the wrong backend without explicitly selecting Claude Code.\n\nSuggested repair: Default WorkerRequest.backend to \"pi\". Make Claude-specific test fixtures explicitly select \"claude\", and add a test of an otherwise complete request with backend omitted.",
        "impact": "A caller relying on the default runs a different agent program or fails because Claude Code is unavailable, even when pi is installed.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 (module review) judged src/concorde/worker_harness/workers.py:318 against specs/concorde/worker-harness/workers/launch.md#inputs and reported a violation: The Inputs table describes backend as \"pi when nothing chooses one\", while WorkerRequest declares `backend: str = \"claude\"`. The runtime dispatches using this request field.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/workers.py",
            "description": "line 318, shown by the violation finding"
          },
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "defines specs/concorde/worker-harness/workers/launch.md#inputs, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.workers",
        "context_id": "sha256:4051c3c641bbb697fb0adc635a874c6a7b3170e921ff20f9df55ac58cf1b348e",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task worker-harness-high, merged into the primary branch at a4ec3dcd16e9bc532b8f0e733029053cdbde5fa6.",
      "evidence": [
        "merge commit a4ec3dcd16e9bc532b8f0e733029053cdbde5fa6",
        "task worker-harness-high"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-29T09:25:23.905986+00:00"
    }
  ]
}
```
