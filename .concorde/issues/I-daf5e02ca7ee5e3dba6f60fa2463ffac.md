# I-daf5e02ca7ee5e3dba6f60fa2463ffac

```json
{
  "schema_version": 4,
  "id": "I-daf5e02ca7ee5e3dba6f60fa2463ffac",
  "status": "open",
  "reports": [
    {
      "id": "sha256:2a1af0fecd9008370c9d9aa2a4d3b7e1b33e2b85a2b9341db6d59dabd1dfc107",
      "created_at": "2026-10-08T07:52:09.352532+00:00",
      "report": {
        "report_key": "spec-panel/module.execution/3",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Cross-namespace cancellation has no specified safe target",
        "description": "The records-only integration tells an independent workspace preparer to cancel a runner with SIGTERM, but exposes only a namespace-local PID. It does not define how that preparer obtains a valid target or when cancellation through this integration is unsupported.\n\nSuggested repair: Specify the supported cancellation boundary. Either define how an independent preparer obtains and verifies a process identity usable in its namespace, or restrict direct cancellation to callers possessing a valid process handle and explain the supported action for other observers.",
        "impact": "An independent preparer can establish liveness but cannot determine a safe cancellation target from the specified records when namespaces differ. Signalling the recorded number could target an unrelated process.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/execution/module.md at What other parts may ask of Execution, line 531 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “The preparer reads those records itself to tell each run running, ended or lost. It waits on a run lock to learn that a run ended. It sends `SIGTERM` itself, as a task's close does. Execution registers no call for any of it.” The preceding section warns: “A runner started in a sandboxed shell may record 2. On the host, that number names an unrelated, living process.” runner.md defines host_pid as the runner's identifier in its own PID namespace.\n\nThe panel's chair merged r1.3 and verified: Verified the direct-cancellation instruction, namespace warning, host_pid definition, and absence of a cancellation-target mapping in the runner interface. Medium severity because this is a cross-namespace cancellation case and the danger is explicitly warned about, rather than hidden. Decision-needed because the supported cancellation boundary must be chosen.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "specs/concorde/execution/module.md",
            "description": "What other parts may ask of Execution, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.execution",
        "context_id": "sha256:0a3bf4281201b623510ea306359717d9cdd4a2c521a0bee0940eb6449eaefa39",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
