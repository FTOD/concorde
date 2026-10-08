# I-ee1010a8007d5e71afe4ee00caec2aae

```json
{
  "schema_version": 4,
  "id": "I-ee1010a8007d5e71afe4ee00caec2aae",
  "status": "open",
  "reports": [
    {
      "id": "sha256:428e0df37c5db5d95c014090fcd1f8b0f3b3b3aad6ca2fa8abe9979b11786094",
      "created_at": "2026-10-08T09:36:40.494547+00:00",
      "report": {
        "report_key": "spec-panel/module.workers/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Lifecycle guarantees omit their documented failure exceptions",
        "description": "The audit, transcript-retention and runtime-removal requirements omit exceptions explicitly supported by the mechanics: an unstarted worker, no session transcript, and operating-system cleanup failure. The returned-record contract repeats an unconditional removal guarantee that contradicts cleanup_failed.\n\nSuggested repair: State the documented applicability and failure handling in each lifecycle requirement: exempt unstarted-worker rounds from auditing, require transcript preservation only when a session existed, and require cleanup attempts with failures reported through req.workers.cleanup-reported. Distinguish expected transcript absence from failure to retain an expected transcript. In contracts.md, define runtime_directory as the allocated path, normally removed before return, with cleanup_failed identifying material that remains.",
        "impact": "Implementers cannot satisfy the unconditional lifecycle requirements on the documented unstarted-worker and cleanup-failure paths. Callers could also infer that temporary files and credential copies are gone even when cleanup_failed reports remaining material.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/worker-harness/workers/launch.md at req.workers.transcript-kept, line 1010 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: req.workers.transcript-kept says: “Before it removes the run's runtime directory, the host SHALL move the latest session's transcript into the run directory, also when the run was interrupted while its last round ran.” req.workers.runtime-removed requires removal unless the host is killed without a chance to act. Yet launch.md explicitly allows cleanup_failed when transcript retention or removal fails, and contracts.md permits a null transcript “when no session existed or when the host could not keep it”. Similarly, req.workers.audit-every-round requires auditing every round, while Audit allows audit null when the command could not start. At contracts.md:1406, runtime_directory is described as “removed by the time the record is returned”.\n\nThe panel's chair merged r1.2, r2.2, r2.3, r3.2 and verified: Verified all lifecycle statements against the Audit and cleanup mechanics, the run-trace and returned-record contracts, and scenario.workers.cleanup-failed. Merged the broad lifecycle report with the narrower transcript and returned-record reports so each label appears once. Medium severity reflects exceptional launch and cleanup paths. Preferred-fix reflects the need to align requirement wording and contract semantics with the already documented exceptions. This differs from the earlier Issue about best-effort trace writes and from the unavailable-audit Issue, which concerns an audit that starts but cannot complete.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "req.workers.transcript-kept, cited by the obligations finding"
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
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
