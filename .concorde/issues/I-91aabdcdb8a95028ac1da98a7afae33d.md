# I-91aabdcdb8a95028ac1da98a7afae33d

```json
{
  "schema_version": 4,
  "id": "I-91aabdcdb8a95028ac1da98a7afae33d",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9f12906cc31579c9f881f38bb0ede17caa31edb5ba3bafa916e0d06745bca218",
      "created_at": "2026-10-03T05:54:48.892957+00:00",
      "report": {
        "report_key": "module.concorde/10",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "The README understates the number of task types",
        "description": "The README still describes six task types although the reviewed Spec defines eight.\n\nSuggested repair: Change the count to eight, or list the eight task types consistently with the root's task-type concept.",
        "impact": "The repository's Protocol overview gives readers an incorrect count of the supported task types.",
        "basis": "code_review run r-20261003T053126-code_review-bd94cc7c (module review) judged README.md:204-207 against concept.task-type and reported a defect: README.md says 'the six task types'. The root's task-type concept and its selected grants contract define eight: understand, specify, implement, test, review-spec, review-code, code-to-spec and review-architecture.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "README.md",
            "description": "lines 204-207, shown by the defect finding"
          },
          {
            "path": "specs/concorde/module.md",
            "description": "defines concept.task-type, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T053126-code_review-bd94cc7c",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.concorde",
        "context_id": "sha256:c40d93ea12b2bd9481f704a892c91cf17e7f2f15601d89343b3f1a641d4bb97a",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": []
}
```
