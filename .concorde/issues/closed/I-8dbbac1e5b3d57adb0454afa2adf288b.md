# I-8dbbac1e5b3d57adb0454afa2adf288b

```json
{
  "schema_version": 4,
  "id": "I-8dbbac1e5b3d57adb0454afa2adf288b",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:dcbdcd351ba7c3f1780ee4131435ff9efd05f7886654a35f7b9b3f281ac5f39c",
      "created_at": "2026-10-13T17:59:47.915751+00:00",
      "report": {
        "report_key": "code-review/module.delivery/1",
        "tier": "obvious-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Raw blob equality bypasses checkout-content verification",
        "description": "The staged-content gate treats equality of raw blob bytes as proof of checkout equality. A smudge filter or checkout conversion can change those bytes even when the raw blob already matches the readiness digest.\n\nSuggested repair: Compare each measured regular file against its checkout-filtered content even when its raw blob digest matches. Add a regression case with an identity clean filter and a rewriting smudge filter, asserting staged_unvalidated and restoration of the index.",
        "impact": "Delivery can report success for a commit whose checkout produces content different from what its readiness validated.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/method/delivery/command.py:833-850 against req.delivery.staged-validated and reported a violation: command.py:838-845 hashes the raw blob and invokes `git cat-file --filters` only `if given != digest`. The requirement permits committing only when a checkout gives back the measured content. With an identity clean filter and a smudge filter that rewrites content, the raw blob equals the measured bytes, so this comparison skips the transformation that a checkout would perform.",
        "owner_target_id": "module.delivery",
        "evidence": [
          {
            "path": "src/concorde/method/delivery/command.py",
            "description": "lines 833-850, shown by the violation finding"
          },
          {
            "path": "specs/concorde/method/delivery/requirements.md",
            "description": "defines req.delivery.staged-validated, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.delivery",
        "context_id": "sha256:2e9311c7fad1ddbccf1fc15ba4b778158051ec1d79be866c44ef2d3640127e10",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task r4-method-work, merged into the primary branch at fbd1a1e92b64d950338cd035fc9adac07bcde8d2.",
      "evidence": [
        "merge commit fbd1a1e92b64d950338cd035fc9adac07bcde8d2",
        "task r4-method-work"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-23T09:02:31.384166+00:00"
    }
  ]
}
```
