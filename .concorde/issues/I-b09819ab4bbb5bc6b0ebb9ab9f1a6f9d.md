# I-b09819ab4bbb5bc6b0ebb9ab9f1a6f9d

```json
{
  "schema_version": 4,
  "id": "I-b09819ab4bbb5bc6b0ebb9ab9f1a6f9d",
  "status": "open",
  "reports": [
    {
      "id": "sha256:ec501c6f3575f01d3865b2b82bc8caff9a5a00a8284f06835fcc652f9daed3fb",
      "created_at": "2026-10-08T07:14:11.501393+00:00",
      "report": {
        "report_key": "code-review/module.adoption/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Preparation failures bypass the promised stub cleanup",
        "description": "Stub cleanup covers failures during description but not failures during preparation after the stubs have been written. A registry write error or cancellation in that interval leaves every prepared stub behind.\n\nSuggested repair: Establish the cleanup guard and record the intended stub contents before committing preparation writes. Ensure preparation failures clean up successfully created stubs and ownership entries; add a regression test that fails registry reconciliation after stub creation.",
        "impact": "A failed preparation leaves unused documents and their ownership entries in the workspace even though no worker ran. Subsequent runs treat those files as existing documents rather than removable prepared stubs.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/method/adoption/code_to_spec.py:211-216, src/concorde/method/adoption/code_to_spec.py:392-403, src/concorde/spec/registry.py:127-134 against req.adoption.stubs-removed and reported a violation: prepare() applies the stub and ownership writes at lines 211–212, then calls registry_command(), and only afterward saves ctx.state['stubs']. describe_code() calls prepare() before entering its try/finally. registry_command() performs its write outside its exception handlers, so a registry write failure after successful stub creation bypasses tidy() entirely. The requirement says cleanup must happen 'whichever step stops it'.",
        "owner_target_id": "module.adoption",
        "evidence": [
          {
            "path": "src/concorde/method/adoption/code_to_spec.py",
            "description": "lines 211-216, shown by the violation finding"
          },
          {
            "path": "src/concorde/method/adoption/code_to_spec.py",
            "description": "lines 392-403, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/registry.py",
            "description": "lines 127-134, shown by the violation finding"
          },
          {
            "path": "specs/concorde/method/adoption/requirements.md",
            "description": "defines req.adoption.stubs-removed, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.adoption",
        "context_id": "sha256:2f179174326ccd8ed2c6a39f70f20983346f3cd314470930b75aa861ee71cf43",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
