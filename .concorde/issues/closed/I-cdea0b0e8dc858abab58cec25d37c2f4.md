# I-cdea0b0e8dc858abab58cec25d37c2f4

```json
{
  "schema_version": 4,
  "id": "I-cdea0b0e8dc858abab58cec25d37c2f4",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:3a439b12a64254e56b2591fe1ebb5f72dfe6375c0243488d939ac82aaabfedeb",
      "created_at": "2026-10-02T02:36:34.489104+00:00",
      "report": {
        "report_key": "module.harness/fix-workers-1",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "Harness defines runtime paths more narrowly than Workers passes them",
        "description": "Harness's module.md defines the runtime paths as 'the paths Bash itself needs to read, such as the toolchain, .venv or node_modules'. Workers' launch.md (Inputs, 'Reading beside the grant'), as revised by the fix-workers task for I-9c0126964e99564b940173c1c460ecc3 and I-1be01905aee65e14a405635e6091cec5, defines them as every path outside the grant that every tool may read and none may write, exactly as the caller lists them: the configured runtime paths, the project interpreter's environment and the host material the caller admits for one run, such as the folder of its own check logs. The Harness already treats them that way on both backends (pi read table, Claude Code deny rules and allowRead); only its wording is narrower.\n\nSuggested repair: in specs/concorde/harness/module.md say that the runtime paths are the read-only material Workers passes beside the grant, readable by every tool, such as the toolchain, .venv, node_modules or the check logs a caller admits, linking Workers' 'Reading beside the grant'.\n\nOther Modules concerned: module.workers",
        "impact": "A reader of the Harness may think a runtime path serves only Bash, and could later restrict file-tool reads of check logs that Implementation and Code review rely on.",
        "basis": "Comparison by the task session of fix-workers on 2026-10-02 of specs/concorde/harness/module.md (runtime paths) with specs/concorde/execution/workers/launch.md.",
        "owner_target_id": "module.harness",
        "evidence": [
          {
            "path": "specs/concorde/harness/module.md",
            "description": "definition of the runtime paths as what Bash needs"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-cc2144d8-ff33-460e-b2ff-9df0a715e1ff",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.harness",
        "context_id": "sha256:14bb0fb334ea038d184ebe0027b5e6a8721c6fbaf0f3c9ab608979757ed02c71",
        "change_id": "fix-workers",
        "head": "8499494021bb16b34b9c8e9e45c21f418a379fb8"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task final-obvious-fixes, merged into the primary branch at 5958df52e3d0ed2504acaf7cdca5a901718e586b.",
      "evidence": [
        "merge commit 5958df52e3d0ed2504acaf7cdca5a901718e586b",
        "task final-obvious-fixes"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-02T03:11:36.860896+00:00"
    }
  ]
}
```
