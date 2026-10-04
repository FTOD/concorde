# I-4db33d4f8ffd5d459f12b1faa653dcbe

```json
{
  "schema_version": 4,
  "id": "I-4db33d4f8ffd5d459f12b1faa653dcbe",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:5e4157b9b82f4df84bf04f6d6a853b134943e1495f282de9fd32b605349ff8ae",
      "created_at": "2026-10-03T05:42:49.881903+00:00",
      "report": {
        "report_key": "module.dogfooding/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Develop source checking crashes on repository paths containing spaces",
        "description": "The source check splits absolute Git directory paths on all whitespace. A clean primary repository whose pathname contains spaces therefore fails while unpacking the result, before its eligibility can be determined.\n\nSuggested repair: Query the two directory values separately so each response is treated as one path, check their return codes, and add install/update coverage using a source path containing spaces.",
        "impact": "A valid clean primary checkout under a path containing spaces cannot be installed or updated in develop mode; the caller gets an uncaught exception instead of the promised installation.",
        "basis": "code_review run r-20261003T053126-code_review-bd94cc7c (module review) judged src/concorde/dogfooding/develop.py:66-69, src/concorde/dogfooding/develop.py:124-129 against scenario.dogfooding.develop-install and reported a defect: develop_source parses the two absolute Git directory paths with `directories.stdout.split()` and unpacks them into `own, common`. For a repository under a path containing a space, each returned path contributes multiple tokens. `check` catches only DevelopError, so the resulting ValueError escapes.",
        "owner_target_id": "module.dogfooding",
        "evidence": [
          {
            "path": "src/concorde/dogfooding/develop.py",
            "description": "lines 66-69, shown by the defect finding"
          },
          {
            "path": "src/concorde/dogfooding/develop.py",
            "description": "lines 124-129, shown by the defect finding"
          },
          {
            "path": "specs/concorde/dogfooding/scenarios.md",
            "description": "defines scenario.dogfooding.develop-install, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T053126-code_review-bd94cc7c",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.dogfooding",
        "context_id": "sha256:9230d00ae980f3ee793903cac51170f04f38967a32aa3d85efe273d558793650",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-open-root-distribution, merged into the primary branch at 8a5cfc367a6280e7de01a6d243e445d6ee49f69d.",
      "evidence": [
        "merge commit 8a5cfc367a6280e7de01a6d243e445d6ee49f69d",
        "task fix-open-root-distribution"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-04T02:34:18.112440+00:00"
    }
  ]
}
```
