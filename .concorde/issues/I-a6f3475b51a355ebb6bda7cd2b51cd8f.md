# I-a6f3475b51a355ebb6bda7cd2b51cd8f

```json
{
  "schema_version": 4,
  "id": "I-a6f3475b51a355ebb6bda7cd2b51cd8f",
  "status": "open",
  "reports": [
    {
      "id": "sha256:7b58b51657144789f143adefc5a90d4cde716fbfbccfee070fd758b70d0ffc76",
      "created_at": "2026-10-03T07:55:02.101241+00:00",
      "report": {
        "report_key": "module.execution/7",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The trace-node requirement excludes bound runs left in the lobby",
        "description": "The trace-node requirement omits the permanent lobby location of a bound run that never enters its workspace. Its normative sentence contradicts its own explanation and req.execution.lobby.\n\nSuggested repair: State the three cases explicitly: workspace folder after entry, the binding's lobby for a bound run that never entered, and the starting worktree's unbound store for an unbound run or refused binding.",
        "impact": "An implementer or test following the SHALL statement could place or expect a refused bound run in the workspace folder, contrary to the lobby rule that protects workspace retirement.",
        "basis": "spec_panel run r-20261003T074406-spec_panel-0a7388d8 judged specs/concorde/execution/requirements.md at req.execution.trace-node, line 176 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"The runner SHALL record every run as a ... trace node ... in the binding's workspace folder, or in `.concorde/unbound/` ... for an unbound run or a run whose binding it refused.\" Its explanation says a bound node \"lies in the ... lobby ... until the run enters its workspace, and stays there when the run never does.\" req.execution.lobby forbids writing into the workspace before admission under its lock.\n\nThe panel's chair merged r1.1 and verified: Verified the requirement, its explanation and the lobby rules. Medium because pre-entry refusals are the affected case; obvious-fix because the intended three locations are already consistently specified elsewhere.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "specs/concorde/execution/requirements.md",
            "description": "req.execution.trace-node, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T074406-spec_panel-0a7388d8",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.execution",
        "context_id": "sha256:5f735f88697ff6604c75aad4f90ea8f92f999c62ddc37bcfd005c5444e51fcfb",
        "change_id": "parts-review-specs",
        "head": "959c856c3a7732af1420829a271f59dd21ba837c"
      }
    }
  ],
  "dispositions": []
}
```
