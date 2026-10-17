# I-e5c7493fecb15ba9b5260cfc916fdcc3

```json
{
  "schema_version": 4,
  "id": "I-e5c7493fecb15ba9b5260cfc916fdcc3",
  "status": "open",
  "reports": [
    {
      "id": "sha256:321f7e557f270c162b0e51aef314a614bb2a92fb51c45d760bdd8773942f491a",
      "created_at": "2026-10-17T04:33:43.450092+00:00",
      "report": {
        "report_key": "refused-directory-search-blocks-review",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "A refused directory search over files the grant makes readable stops a review worker",
        "description": "In project_review r-20261013T165054-project_review-b4db00b2, module.harness's reviewer2 (pi, review-spec) ran a grep over specs/concorde/worker-harness/harness/; the grant lists the three documents there individually as ro, not the directory, so pi's permission extension refused the search, and the worker ended blocked with review_search_boundary_refused because its brief tells it to stop after a refusal. The panel then ended panel_short and the Module incomplete. A search whose every match would be a readable file is not overreaching work.",
        "impact": "Any review of a Module whose documents share a folder can end incomplete by chance, wasting the panel's other workers.",
        "basis": "The rendered error chain of the run (worker_blocked caused by review_search_boundary_refused, with the grep's refusal text).",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": ".concorde/unbound/r-20261013T165054-project_review-b4db00b2/result.json",
            "description": "module.harness panel_short"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-c0ebdb8f-d818-4caf-8d22-fd844c0c48a1",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:01676642a628202edfb9e14776172def45342a8dfb5f34e6cffbd330936b2baa",
        "change_id": null,
        "head": "f0afbc0af6dd1ba8b66ec85a7945f000a5786624"
      }
    }
  ],
  "dispositions": []
}
```
