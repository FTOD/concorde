# I-cbde7d00eba65a7bbdacf14d8b458844

```json
{
  "schema_version": 3,
  "id": "I-cbde7d00eba65a7bbdacf14d8b458844",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:7882a0688eb1886a13d3ee93c78a941adc2767b6907e71a783efbf85e5cd0adc",
      "created_at": "2026-10-01T12:05:19.225259+00:00",
      "report": {
        "report_key": "workers-proxy-task-session-sandbox",
        "tier": "preferred-fix",
        "type": "bug",
        "subtype": null,
        "title": "Workers justifies its proxy rule by a task session's sandbox, which is gone",
        "owner_target_id": "module.workers",
        "description": "Workers' Proxy section gives the reason for passing the host's proxy variables on to a worker, and for removing `localhost`, `127.0.0.1`, `::1` and `[::1]` from the no-proxy lists when every passed proxy names a loopback host, as the task session's own sandbox: \"A task session runs its shell commands, and so the Operations it starts and their workers, inside a sandbox with a network namespace of its own that holds only a loopback interface: its only way out is the sandbox's proxy, which it names on localhost in those variables, and its no-proxy lists name loopback.\" scenario.workers.session-proxy states the same in its GIVEN, \"as a task session's sandbox sets them\", and in its title, \"A worker started in a task session uses the session's proxy\"; the code and tests repeat it in comments (src/concorde/harness/claude_backend.py, tests/concorde/harness/workers/test_workers.py). Since req.task-session.no-sandbox a task session's settings carry no sandbox, so a task session has no network namespace, runs no loopback proxy and sets none of those variables: the only cause the Spec gives for the behaviour cannot occur any more. The behaviour itself still has a purpose, since any enclosing loopback proxy, such as a developer's own local model proxy or a main agent whose own session is sandboxed, still reaches a worker the same way.",
        "impact": "A reader cannot tell whether the rule is still wanted, because the Spec, the scenario and the code comments all justify it by a sandbox that no longer exists. A later change could drop the loopback stripping that a developer's own local proxy still needs, or keep it while believing a task session supplies the proxy, and the scenario as written can no longer be set up the way its GIVEN describes.",
        "basis": "specs/concorde/execution/workers/launch.md, section Proxy, attributes the passed variables and the loopback stripping to a task session's sandbox and its network namespace; specs/concorde/execution/workers/scenarios.md states the same in scenario.workers.session-proxy's title and GIVEN; specs/concorde/coordination/task-session/requirements.md#req.task-session.no-sandbox requires a task session's boundary to carry no sandbox, so its commands reach every network host directly.",
        "evidence": [
          {
            "path": "specs/concorde/execution/workers/launch.md",
            "description": "the Proxy section, whose stated reason is that a task session runs its commands inside a sandbox with a loopback-only network namespace"
          },
          {
            "path": "specs/concorde/execution/workers/scenarios.md",
            "description": "scenario.workers.session-proxy, whose title and GIVEN name a task session's sandbox as what sets the proxy variables"
          },
          {
            "path": "specs/concorde/coordination/task-session/requirements.md",
            "description": "req.task-session.no-sandbox, which requires a task session's settings to carry no sandbox"
          },
          {
            "path": "src/concorde/harness/claude_backend.py",
            "description": "the comment at the proxy constant naming a task session's sandbox as what leaves the process the proxy"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-509fe139-7ef2-4f41-84d2-c1f494e38d86",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:73b3e45dc9afde2ec1516e7b185aab416c21c8f99e55ea0431c017b96accf7a0",
        "change_id": "execution-detached-example",
        "head": "9218e5000ae834615c74abd7b0f6af6ffb82b386"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task stale-text-cleanup, merged into the primary branch at b57399d25133e63239c7fa185d146b58dd8d9abd.",
      "evidence": [
        "merge commit b57399d25133e63239c7fa185d146b58dd8d9abd",
        "task stale-text-cleanup"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-01T12:44:02.012657+00:00"
    }
  ]
}
```
