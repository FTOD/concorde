# I-330deb19ef745bcea12fdd1bf4df478e

```json
{
  "schema_version": 4,
  "id": "I-330deb19ef745bcea12fdd1bf4df478e",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:26a6e4269a5cce19b6e3c535ab44b7aff6ef3740b50a73b23c19b749b381c29b",
      "created_at": "2026-10-13T20:33:54.702611+00:00",
      "report": {
        "report_key": "code-review/module.workers/1",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Submodule changes are missed or misreported by the write audit",
        "description": "The audit treats a submodule directory as an absent file rather than measuring the files and Git state within it. It consequently cannot enforce the promised file-level audit for submodules.\n\nSuggested repair: Snapshot and audit initialized submodules recursively, prefixing their file paths with their worktree-relative locations and checking their Git state. Add cases for permitted edits, forbidden edits, and deletions in both clean and already-dirty submodules.",
        "impact": "Changes outside rw inside an already-dirty submodule can pass a clean audit, while permitted edits in a previously clean submodule can fail as fictitious deletions.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/worker_harness/audit.py:35-42, src/concorde/worker_harness/audit.py:82-98, src/concorde/worker_harness/audit.py:125-136 against req.workers.audit-every-round and reported a violation: snapshot() measures only paths returned by the outer repository's status. For a dirty submodule, Git reports its directory; _digest() returns None for any path that is not a file. audit() skips an entry whenever old == new, so an already-dirty submodule remains None on both sides even when its files change. A newly dirty submodule instead appears as '(deleted)'. The Spec requires comparison of changed files against rw and identification of deletions.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/audit.py",
            "description": "lines 35-42, shown by the violation finding"
          },
          {
            "path": "src/concorde/worker_harness/audit.py",
            "description": "lines 82-98, shown by the violation finding"
          },
          {
            "path": "src/concorde/worker_harness/audit.py",
            "description": "lines 125-136, shown by the violation finding"
          },
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "defines req.workers.audit-every-round, the finding's basis"
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
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task r4-workers, merged into the primary branch at 09e1c3e2a9f42f99c425a2fd8e012715d67a6bd6.",
      "evidence": [
        "merge commit 09e1c3e2a9f42f99c425a2fd8e012715d67a6bd6",
        "task r4-workers"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-23T09:01:56.656617+00:00"
    }
  ]
}
```
