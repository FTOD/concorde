# I-4f98b23fbccb582491cdd97fcf8ed64d

```json
{
  "schema_version": 4,
  "id": "I-4f98b23fbccb582491cdd97fcf8ed64d",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9eaacab94a54b81791223e02aa755bb30a1b4b6cc10f5453db30ea0850c8e2fe",
      "created_at": "2026-10-13T18:09:25.786014+00:00",
      "report": {
        "report_key": "code-review/module.distribution/9",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Tool-change notification promises contradict each other",
        "description": "The requirement promises deduplication across all tool sets notified since the last listing, while the call contract specifies deduplication only against the most recently notified set. These prescribe contradictory behavior when an earlier tool set returns.\n\nSuggested repair: Choose one policy and align both documents. Prefer retaining a set of notified digests until tools/list resets it to satisfy the requirement's explicit once-per-set promise; add an A-B-A test before any new listing.",
        "impact": "There is no implementation that satisfies both promises for an A-B-A sequence before the next tools/list; a repair or regression test needs a decision about the intended notification policy.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged specs/concorde/distribution/requirements.md:531-536, specs/concorde/distribution/contracts.md:397-404, src/concorde/distribution/project_mcp/calls.py:284-289 against req.distribution.mcp-tools-changed and reported a spec-challenge: requirements.md requires notification 'once for each set of tools it has not told the session of since that listing'. contracts.md instead requires notification whenever the digest differs from the listed digest and the single last-notified digest. With listed digest L and successive answers A, B, A, the requirement forbids the third notification while the contract requires it. Calls.call implements the contract by retaining only self.notified.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/requirements.md",
            "description": "lines 531-536, shown by the spec-challenge finding"
          },
          {
            "path": "specs/concorde/distribution/contracts.md",
            "description": "lines 397-404, shown by the spec-challenge finding"
          },
          {
            "path": "src/concorde/distribution/project_mcp/calls.py",
            "description": "lines 284-289, shown by the spec-challenge finding"
          },
          {
            "path": "specs/concorde/distribution/requirements.md",
            "description": "defines req.distribution.mcp-tools-changed, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.distribution",
        "context_id": "sha256:b3e4b9a1d6a5c7edf7f6b97c306c506e0236cbfd38f99b33935a579437ac47ba",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
