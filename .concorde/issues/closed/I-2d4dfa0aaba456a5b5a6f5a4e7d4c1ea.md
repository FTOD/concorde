# I-2d4dfa0aaba456a5b5a6f5a4e7d4c1ea

```json
{
  "schema_version": 4,
  "id": "I-2d4dfa0aaba456a5b5a6f5a4e7d4c1ea",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:38452f45f911b34da70240ecb589a026f64950ec3e684e6c334c4ec769d37672",
      "created_at": "2026-10-03T04:04:36.008109+00:00",
      "report": {
        "report_key": "module.harness/7",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Write-hook command does not quote filesystem paths",
        "description": "The generated write-hook command interpolates executable and script paths without shell quoting. Valid installation paths containing spaces are split into multiple shell words.\n\nSuggested repair: Construct the command with shell-safe quoting for each path, such as shlex.join([python, str(run.control / 'write_hook.py')]), and verify generation for paths containing spaces and apostrophes.",
        "impact": "A Python installation in a directory containing spaces causes the shell to invoke the wrong executable name, so the required write hook does not run correctly.",
        "basis": "code_review run r-20261003T035159-code_review-dc0efdcc (module review) judged src/concorde/worker_harness/settings.py:458-464 against specs/concorde/worker-harness/harness/claude-code.md#write-hook and reported a defect: worker_settings builds the hook shell command as 'f\"{python} {(run.control / 'write_hook.py').as_posix()}\"' without quoting either argument. The Spec requires the generated hook to receive PreToolUse input and enforce the exact rw allowlist; it places no restriction on spaces or shell metacharacters in the Python executable path.",
        "owner_target_id": "module.harness",
        "evidence": [
          {
            "path": "src/concorde/worker_harness/settings.py",
            "description": "lines 458-464, shown by the defect finding"
          },
          {
            "path": "specs/concorde/worker-harness/harness/claude-code.md",
            "description": "defines specs/concorde/worker-harness/harness/claude-code.md#write-hook, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T035159-code_review-dc0efdcc",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.harness",
        "context_id": "sha256:3998618385178bb15cf4e164a7fa553feef4ef1a81e88c288a3d18082951a51b",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-open-worker-harness, merged into the primary branch at 29fd888f6ba4e29480b0d2429561b42e6c5b200c.",
      "evidence": [
        "merge commit 29fd888f6ba4e29480b0d2429561b42e6c5b200c",
        "task fix-open-worker-harness"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-04T02:58:06.611552+00:00"
    }
  ]
}
```
