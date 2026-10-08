# I-d6e13c726dcf57828aaac134bcc50deb

```json
{
  "schema_version": 4,
  "id": "I-d6e13c726dcf57828aaac134bcc50deb",
  "status": "open",
  "reports": [
    {
      "id": "sha256:ae930053b6a105cab3dfa07844f6b9488588c799a97e904b6a7ed433b587286d",
      "created_at": "2026-10-08T09:39:14.030646+00:00",
      "report": {
        "report_key": "code-review/module.workers/5",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Interrupted rounds lose their standard error",
        "description": "An externally interrupted round never persists its captured standard error. The process is killed and the interruption is recorded, but the output buffers are abandoned as the exception propagates.\n\nSuggested repair: Drain and persist each round's stderr during interruption cleanup before propagating the interruption, for example through a per-round output sink or a partial outcome carried by the interruption path. Extend the interruption test to emit and verify stderr before cancellation.",
        "impact": "An interrupted worker loses the standard error it emitted before cancellation, making the recorded failure harder to diagnose and leaving the round without its promised stderr.log.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/worker_harness/workers.py:475-491, src/concorde/worker_harness/workers.py:916-919, src/concorde/worker_harness/workers.py:748-752 against req.workers.stderr-per-round and reported a violation: _launch kills the process group in finally around process.wait(), but joining readers and returning their collected output occur after that finally. An interruption propagates past those statements. The sole normal call to _keep_stderr follows the successful return of _launch, so it is skipped; finish() closes running round nodes without saving their buffered stderr.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/workers.py",
            "description": "lines 475-491, shown by the violation finding"
          },
          {
            "path": "src/concorde/worker_harness/workers.py",
            "description": "lines 916-919, shown by the violation finding"
          },
          {
            "path": "src/concorde/worker_harness/workers.py",
            "description": "lines 748-752, shown by the violation finding"
          },
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "defines req.workers.stderr-per-round, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.workers",
        "context_id": "sha256:25bf3ca79f4b812d672ebebd9c10145532654c754fdee7567f552ea2f5639d06",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
