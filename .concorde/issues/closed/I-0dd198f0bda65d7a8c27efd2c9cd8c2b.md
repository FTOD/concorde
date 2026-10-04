# I-0dd198f0bda65d7a8c27efd2c9cd8c2b

```json
{
  "schema_version": 4,
  "id": "I-0dd198f0bda65d7a8c27efd2c9cd8c2b",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:758ead0decf8584d1ac3e48c4d716468d4a0ebd140b55599f8e32d818d0a6344",
      "created_at": "2026-10-03T04:12:13.983955+00:00",
      "report": {
        "report_key": "module.workers/13",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Timeout and process failures discard an already-returned worker result",
        "description": "Failure precedence is applied before preserving a valid worker result, causing the run record to lose worker claims on timeout or process-limit paths.\n\nSuggested repair: Validate and retain any available worker result independently of the host verdict, then apply the specified timeout/process/audit precedence without treating the retained claim as success.",
        "impact": "If a valid structured result is emitted before a process hangs until timeout or reports a limit, the trace drops the result instead of retaining it separately from the host's failing verdict.",
        "basis": "code_review run r-20261003T035159-code_review-dc0efdcc (module review) judged src/concorde/worker_harness/workers.py:769-819 against req.workers.claims-apart and reported a violation: After audit, workers.py returns immediately for timeout and concluded.failure. Only later does it validate concluded.result and assign `record[\"worker_result\"] = result`. The run-trace contract defines worker_result as the last worker result verbatim.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/workers.py",
            "description": "lines 769-819, shown by the violation finding"
          },
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "defines req.workers.claims-apart, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T035159-code_review-dc0efdcc",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:d1680f8965bc4bd9a8d84ee00426acbf1fdc230cad735073abffd34139c83164",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    },
    {
      "id": "sha256:6f756f6de7671e4170c70cd6a7d75ad9bce15bb887bd64dcbe5edb7cb1431dcd",
      "created_at": "2026-10-03T04:19:30.594712+00:00",
      "report": {
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Timeout and process failures discard an already-returned worker result",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/workers.py",
            "description": "lines 769-819, shown by the violation finding"
          },
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "defines req.workers.claims-apart, the finding's basis"
          }
        ],
        "issue_id": "I-0dd198f0bda65d7a8c27efd2c9cd8c2b",
        "expected_revision": "sha256:1ba7797103b8800472afbf61dd046d009c0a3b133579db05d8d43f82f7fec9c1",
        "report_key": "verify/module.workers/13",
        "tier": "obvious-fix",
        "severity": "low",
        "description": "On a timed-out round or a process failure, run_worker returns before validating concluded.result, so a valid worker result the stream already held is not kept as worker_result.",
        "impact": "Only when the worker produced its result and the process then timed out or failed; the run fails either way and only the claim is missing from the record. Low.",
        "basis": "Verified against src/concorde/worker_harness/workers.py:770-819 and the worker_result semantics of contract.workers.worker-run-trace."
      },
      "source": {
        "invocation_id": "cli-7549aff4-1d32-4e97-9daf-1b0effd368df",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:1d5cfc2a2a7ba74b163c0a7da2044601cb98d3bb39fa931e4f515946b2ee70f4",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-open-worker-harness, merged into the primary branch at 29fd888f6ba4e29480b0d2429561b42e6c5b200c.",
      "evidence": [
        "merge commit 29fd888f6ba4e29480b0d2429561b42e6c5b200c",
        "task fix-open-worker-harness"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-04T02:58:09.780511+00:00"
    }
  ]
}
```
