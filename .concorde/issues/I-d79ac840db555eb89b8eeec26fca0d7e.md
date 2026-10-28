# I-d79ac840db555eb89b8eeec26fca0d7e

```json
{
  "schema_version": 4,
  "id": "I-d79ac840db555eb89b8eeec26fca0d7e",
  "status": "open",
  "reports": [
    {
      "id": "sha256:4a8b57055258609815ce37cde1fc73e23bd2ce57972204a5a4791075956565d3",
      "created_at": "2026-10-28T07:21:32.303066+00:00",
      "report": {
        "report_key": "check-uv-cache-dir-from-user-config",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "A developer's uv cache-dir setting sends a configured check's uv cache to a read-only path",
        "description": "The check boundary gives a check a writable cache by setting XDG_CACHE_HOME (and npm_config_cache) to its scratch (src/concorde/execution/checks/check_executor.py, around line 515). uv gives a `cache-dir` in the user's uv.toml (~/.config/uv/uv.toml) precedence over XDG_CACHE_HOME, and uv still finds that file inside the boundary through the passwd home. When the developer sets it, every check that runs uv uses a cache outside the scratch. That path is read-only in the boundary, and `uv venv` fails with \"Could not acquire lock\" (EROFS). Seen in task checks-bwrap-compat, task-validation r-20261028T071109-task_validation-2c6fa1a9: check.concorde.tests, check.distribution.tests and check.dogfooding.tests failed (42 tests). A probe in the same bubblewrap options showed that UV_CACHE_DIR=<scratch>/cache/uv fixes it. Suggested fix: the runner also sets UV_CACHE_DIR to the scratch, as it sets npm_config_cache, and the boundary's environment table in module.checks' Spec says so.",
        "impact": "On a host whose developer sets uv's cache-dir in uv.toml, every configured check that runs uv fails, which blocks task-validation and delivery. The developer machine was worked around on 2026-10-28 by removing that setting.",
        "basis": "Task checks-bwrap-compat's escalation uv_cache_outside_scratch and its probe (decision log, 2026-10-28). Main agent's check: with no uv.toml, `env -i PATH=... XDG_CACHE_HOME=/tmp/x uv cache dir` prints /tmp/x/uv.",
        "owner_target_id": "module.checks",
        "evidence": [
          {
            "path": "src/concorde/execution/checks/check_executor.py",
            "description": "the check environment sets XDG_CACHE_HOME and npm_config_cache but not UV_CACHE_DIR"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-c4bd04ae-93eb-4aff-b767-909c7713192c",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.checks",
        "context_id": "sha256:3d0d125f3ea826ecf9f02f9ff73e11fa4a98782eeb462e9b63bffff8c59ced7c",
        "change_id": "checks-bwrap-compat",
        "head": "f9c15f0887def596d612d843e2083ab7cadb0e2a"
      }
    }
  ],
  "dispositions": []
}
```
