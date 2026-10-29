# I-bb8a8dd49fec56c49f1e70fecb94dc8a

```json
{
  "schema_version": 4,
  "id": "I-bb8a8dd49fec56c49f1e70fecb94dc8a",
  "status": "open",
  "reports": [
    {
      "id": "sha256:2cea32d07a79a0e413c208dae1a6dff1f51f790d76fc54be488ec3cd62979c9b",
      "created_at": "2026-10-29T07:51:51.103068+00:00",
      "report": {
        "report_key": "spec-panel/module.project-review/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Do not claim standing Issues cover unexamined deterministic changes",
        "description": "The refusal rationale claims standing Issues already give every outcome when all worker identities are unchanged. Deterministic inputs, such as a newly tracked unbound file, can change without changing any worker identity.\n\nSuggested repair: Preserve the explicitly chosen refusal policy but correct its rationale. Warn that deterministic inputs are not covered by the identity comparison and that --full is needed to examine them when every worker part would skip. Add the new-unbound-file example.",
        "impact": "A caller can mistake nothing_to_review for evidence that deterministic problems are unchanged, despite those parts not running.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 judged specs/concorde/method/project-review/module.md at Why it is built this way by the design criterion of the Protocol's Evaluating a Spec; the Specs read: “The Issues that stand already give every outcome of such a run.” req.project-review.nothing-to-review explicitly says: “A refused run runs no check and finds no uncovered scenario and no unowned file.”\n\nThe panel's chair merged r1.2 and verified: Compared the identity table, refusal requirement, and rationale. The refusal itself is explicit, so it need not be redesigned; correcting the unsupported assurance is the preferred repair. Medium because it misleads callers in a repeat-run edge case.",
        "owner_target_id": "module.project-review",
        "evidence": [
          {
            "path": "specs/concorde/method/project-review/module.md",
            "description": "Why it is built this way, cited by the design finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.project-review",
        "context_id": "sha256:ca5dd807ee000814acb91d27308500f4f266abf3f038b37eb495b389b2f8e110",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
