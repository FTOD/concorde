# I-cb8f573a1f8e5acd89578f3dbf0eb1b3

```json
{
  "schema_version": 4,
  "id": "I-cb8f573a1f8e5acd89578f3dbf0eb1b3",
  "status": "open",
  "reports": [
    {
      "id": "sha256:e331c92ca390c9ddf3b37bf7a1f0a22e7feb7a00975aa051cc7a69a8deb7c3a5",
      "created_at": "2026-10-08T07:53:14.614237+00:00",
      "report": {
        "report_key": "code-review/module.execution/1",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Preserve cancellation through admission and runtime-path resolution",
        "description": "SIGINT or SIGTERM delivered while a definition's admission or runtime-path resolver runs is wrapped as DefinitionFailed. The run consequently reports host_error rather than cancelled.\n\nSuggested repair: Let Cancelled propagate unchanged through both callback wrappers, as _steps already does. Add tests delivering a signal inside admission and the runtime-path resolver.",
        "impact": "A caller cancelling during admission or runtime-path resolution receives a misleading capability failure instead of the cancellation result and trace outcome it relies on.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/execution/runner.py:273-277, src/concorde/execution/runner.py:311-318, src/concorde/execution/runner.py:619-645 against scenario.execution.cancelled and reported a violation: Cancelled inherits Exception. The runtime-path resolver wrapper catches every Exception and raises DefinitionFailed (runner.py:273-277); admission does the same after exempting only RunError, KernelError and Refused (311-318). The runner handles DefinitionFailed as host_error, whereas the Spec requires SIGINT/SIGTERM from the binding check through execution to produce cancelled evidence.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "src/concorde/execution/runner.py",
            "description": "lines 273-277, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/runner.py",
            "description": "lines 311-318, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/runner.py",
            "description": "lines 619-645, shown by the violation finding"
          },
          {
            "path": "specs/concorde/execution/scenarios.md",
            "description": "defines scenario.execution.cancelled, the finding's basis"
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
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
