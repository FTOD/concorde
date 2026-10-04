# I-a6f3475b51a355ebb6bda7cd2b51cd8f

```json
{
  "schema_version": 4,
  "id": "I-a6f3475b51a355ebb6bda7cd2b51cd8f",
  "status": "closed",
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
    },
    {
      "id": "sha256:8f046f6defc2a3c51d72ad896b49c0c5f8f57ab738e55af357fe688141a836c0",
      "created_at": "2026-10-03T08:48:46.989503+00:00",
      "report": {
        "issue_id": "I-a6f3475b51a355ebb6bda7cd2b51cd8f",
        "expected_revision": "sha256:71538fcebfb6e4dbc497a8904ca84ca1ba6da422afb1a51f91275217a6f41e92",
        "report_key": "module.execution/7-verified",
        "tier": "obvious-fix",
        "severity": "low",
        "title": "req.execution.trace-node's statement omits the lobby its own explanation names",
        "description": "req.execution.trace-node (specs/concorde/execution/requirements.md) SHALL records every run in the binding's workspace folder, or in .concorde/unbound/ for an unbound run or a refused binding; its explanation and req.execution.lobby say a bound run refused or cancelled before it holds the workspace lock stays for good in lobby/<run-id>/ of the binding's .concorde. Fix: make the statement name the three places: 'in the binding's workspace folder once the run entered its workspace, in the lobby of the binding's .concorde when it never did, or in .concorde/unbound/ of the worktree it started in for an unbound run or a run whose binding it refused.'",
        "impact": "Wording inconsistency inside one requirement; the explanation directly below and req.execution.lobby are explicit, and the code keeps such runs in the lobby.",
        "basis": "Read req.execution.trace-node, its explanation, req.execution.lobby and runner.md 'The lobby'. Severity lowered from medium: the explanation under the same heading states the lobby case, so no implementer is misled. Classification: pre-existing - identical statement and explanation on main (git show main:specs/concorde/execution/requirements.md, lines 166-174).",
        "owner_target_id": "module.execution",
        "type": "bug",
        "subtype": null,
        "evidence": [
          {
            "path": "specs/concorde/execution/requirements.md",
            "description": "req.execution.trace-node and req.execution.lobby"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-8778bfaf-6ea8-4001-8343-8c20eed1b2ba",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.execution",
        "context_id": "sha256:dc5a1d8cbf5a69d2834f2ea5f6545ea6067e5caf2e4e3c78dfc4f3342c22cb32",
        "change_id": "parts-review-specs",
        "head": "41bda04db324df4ff913498f023597a72c419955"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-open-execution, merged into the primary branch at 2e0cec3ff64774412d776c2d66551f82e1786542.",
      "evidence": [
        "merge commit 2e0cec3ff64774412d776c2d66551f82e1786542",
        "task fix-open-execution"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-04T02:36:15.601141+00:00"
    }
  ]
}
```
