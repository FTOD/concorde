# I-f7d61c736fac5dc6acfd74b9c69a70cc

```json
{
  "schema_version": 4,
  "id": "I-f7d61c736fac5dc6acfd74b9c69a70cc",
  "status": "open",
  "reports": [
    {
      "id": "sha256:ab608d8a9757e9396ca6f5298f9ff19d4866b94d81e02e0a8b75e245fc666ff3",
      "created_at": "2026-10-13T18:42:46.803834+00:00",
      "report": {
        "report_key": "code-review/module.headless-sessions/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Run relocation can falsely fail observation",
        "description": "Run relocation recovery does not find workflow-step runs whose destination basename is `run`, and it does not recover moves that happen after the initial existence check. Some subsequent reads also retain the obsolete lobby path.\n\nSuggested repair: Resolve moved folders by run identity, including the status record of workflow-step folders, and re-resolve on a missing-file retry. Carry the resolved directory through status, result and modification-time reads. Add relocation tests for workflow destinations and moves between individual reads.",
        "impact": "A normal lobby-to-workspace transition can falsely end a session with observation_failed instead of allowing the promised wake.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged scripts/e2e/sessions.py:308-339, scripts/e2e/sessions.py:359-361, scripts/e2e/sessions.py:384-391 against scenario.headless-sessions.moved-run and reported a violation: _moved matches only `folder.name == directory.name`. A lobby folder named r-... becomes `workflow/steps/<step>/run`, so its new basename cannot match. Also, _observed retries the same fixed path, and unsettled_runs rereads a moved status at line 384 without updating the directory used for result.json at line 389. The scenario requires a run moved between listing and reading to be read in its workspace folder once.",
        "owner_target_id": "module.headless-sessions",
        "evidence": [
          {
            "path": "scripts/e2e/sessions.py",
            "description": "lines 308-339, shown by the violation finding"
          },
          {
            "path": "scripts/e2e/sessions.py",
            "description": "lines 359-361, shown by the violation finding"
          },
          {
            "path": "scripts/e2e/sessions.py",
            "description": "lines 384-391, shown by the violation finding"
          },
          {
            "path": "specs/concorde/e2e/sessions/scenarios.md",
            "description": "defines scenario.headless-sessions.moved-run, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.headless-sessions",
        "context_id": "sha256:93b6e4c52a25a3c80e6aa35d563fd4b9b29870750c499fba5d692444c76f1eb4",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
