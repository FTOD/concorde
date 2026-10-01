# I-07e549dde12655e095abcabcfb422fee

```json
{
  "schema_version": 3,
  "id": "I-07e549dde12655e095abcabcfb422fee",
  "status": "open",
  "reports": [
    {
      "id": "sha256:4fab574786916fcdd4d40f4a103ceb84eb7a2f0a7c53c692041d60ee1ff34eac",
      "created_at": "2026-10-01T10:21:05.317047+00:00",
      "report": {
        "report_key": "execution-detached-namespace-task-session-example",
        "tier": "obvious-fix",
        "type": "bug",
        "subtype": null,
        "title": "The detached-run passage names a task session as a sandboxed caller",
        "description": "Execution's \"A detached run lives only as long as the PID namespace it started in\" passage ends by naming the two ways to outlive a sandboxed Bash call, the second being \"keeps the call alive as long as the run, as a task session does when it runs a run in background Bash\". Since task sessions dropped the operating-system Bash sandbox (task session-without-sandbox), a task session's Bash calls are not sandboxed, so it is no longer an example of that case. The statement about PID namespaces itself stays true, and still holds for workers and for a main agent whose own session runs in a sandbox; only the example is stale. A task session still starts its runs in background Bash, now because Claude Code may end the processes of a call that returned, not because of a namespace.",
        "impact": "A reader is told that a task session's Bash calls are sandboxed, which contradicts the task-session boundary and may lead a change to keep a workaround that has no cause any more.",
        "basis": "specs/concorde/execution/module.md#detached-namespace names the task session; specs/concorde/coordination/task-session/requirements.md#req.task-session.no-sandbox requires the task-session settings to carry no sandbox.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "specs/concorde/execution/module.md",
            "description": "the detached-namespace passage naming a task session's background Bash as a sandboxed call"
          },
          {
            "path": "specs/concorde/coordination/task-session/requirements.md",
            "description": "req.task-session.no-sandbox, which drops the sandbox from a task session's boundary"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-e2a37858-7e65-4b6d-a3e1-ae7e1a92a12c",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.execution",
        "context_id": "sha256:73b3e45dc9afde2ec1516e7b185aab416c21c8f99e55ea0431c017b96accf7a0",
        "change_id": "session-without-sandbox",
        "head": "9693b9a95d036c6fbc3381c73580d4ce6e268541"
      }
    }
  ],
  "dispositions": []
}
```
