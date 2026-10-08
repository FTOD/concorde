# I-e7826df5f6af5caeb919b1aa9be3ece2

```json
{
  "schema_version": 4,
  "id": "I-e7826df5f6af5caeb919b1aa9be3ece2",
  "status": "open",
  "reports": [
    {
      "id": "sha256:eb76bc8fd6e06c6539aaf8ff77d8696ee6a262b3830fbe7601112c7e9fd50dc9",
      "created_at": "2026-10-08T04:24:05.696073+00:00",
      "report": {
        "report_key": "code-review/module.views/3",
        "tier": "preferred-fix",
        "severity": "critical",
        "type": "bug",
        "subtype": null,
        "title": "Backup cleanup failure can corrupt the published site",
        "description": "Failure while recursively deleting the old-site backup is treated as a reversible promotion failure. Recursive deletion may already have removed part of that backup, so it is no longer a safe rollback source.\n\nSuggested repair: Separate the reversible rename transaction from post-commit backup cleanup. Once backup deletion starts, preserve the complete promoted destination on cleanup failure and report the cleanup problem; add a test that deletes one backup file before injecting the failure.",
        "impact": "A cleanup failure can destroy the complete new site and restore an incomplete old site, losing published pages despite successful candidate validation and directory promotion.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged docsite/scripts/build.ts:21-32, docsite/tests/contract/build-failures.test.ts:55-62 against specs/concorde/spec-tooling/views/pipeline.md#promotion and reported a defect: After both renames succeed, build.ts:28 recursively deletes the backup inside the rollback try block. Any error then removes the new destination and renames the remaining backup into place. The existing backup-removal test mocks an immediate rejection and never simulates files already removed from the backup.",
        "owner_target_id": "module.views",
        "evidence": [
          {
            "path": "docsite/scripts/build.ts",
            "description": "lines 21-32, shown by the defect finding"
          },
          {
            "path": "docsite/tests/contract/build-failures.test.ts",
            "description": "lines 55-62, shown by the defect finding"
          },
          {
            "path": "specs/concorde/spec-tooling/views/pipeline.md",
            "description": "defines specs/concorde/spec-tooling/views/pipeline.md#promotion, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.views",
        "context_id": "sha256:694a75b7b53df6199b1e598851e63c9bf43c9da18f3e23215369fca09ba2fa05",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
