# I-14afc69e0e045b158e1bde17a5aae5fe

```json
{
  "schema_version": 4,
  "id": "I-14afc69e0e045b158e1bde17a5aae5fe",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:4914cccd68f265d8f1d44f986433d4fcf483976a518e0c181b55bf93dd98f573",
      "created_at": "2026-10-13T20:34:04.637003+00:00",
      "report": {
        "report_key": "spec-panel/module.workers/4",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The resumed-cost requirement drops the decreasing-total exception",
        "description": "The precise cost requirement and contract omit the decreasing-total fallback stated by the accounting algorithm.\n\nSuggested repair: State in the requirement and round-trace semantics that subtraction applies only to a known restoring version whose reported total is at least the previous total. Otherwise count the report whole, and align the resumed-cost scenario.",
        "impact": "Following the requirement for a decreasing reported total produces negative round cost and can increase the remaining budget.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/worker-harness/workers/launch.md at req.workers.round-own-cost, line 1103 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The requirement records reported cost \"less, for a resumed round on a Claude Code version that restores session totals, the cost that the session's previous round reported\". Limits instead counts the report whole \"when the reported cost is below the session's previous total, since then nothing was restored\". The round-trace semantics and resumed-cost scenario also omit this exception.\n\nThe panel's chair merged r2.3, r3.5 and verified: Verified the disagreement among mechanics, requirement, contract and scenario. Medium for the reset-total edge case; obvious-fix because the existing mechanics explicitly supply the missing exception.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "req.workers.round-own-cost, cited by the obligations finding"
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
        "phase": "spec-panel"
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
      "created_at": "2026-10-29T09:25:26.052198+00:00"
    }
  ]
}
```
