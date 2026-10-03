# I-eddf3858f30e5744af1ddd01b1b8c7ec

```json
{
  "schema_version": 4,
  "id": "I-eddf3858f30e5744af1ddd01b1b8c7ec",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:58014e411a0bc3637dc39652709871cba8a57e3168dd4b457bbf83b6f0b6623d",
      "created_at": "2026-10-03T08:07:35.759901+00:00",
      "report": {
        "report_key": "module.workflows/16",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Reconcile step deadlines with the detached-launch handshake",
        "description": "The promised total step-call deadline does not account for the prescribed detached-launch handshake. The tool contract exposes additional allowances without reconciling them with the CLI requirement.\n\nSuggested repair: Choose a common timing model across CLI, adapter and MCP. Prefer explicitly separating the bounded launch phase from the wait budget and stating lock-wait policy and total bounds; preserving a total deadline instead needs a recoverable pending launch. Add a slow-launch scenario with a shorter wait.\n\nOther Modules concerned: module.execution, module.distribution",
        "impact": "Short-wait callers cannot rely on a total deadline; enforcing it during launch can interrupt the handoff before the run identity is recorded.",
        "basis": "spec_panel run r-20261003T074406-spec_panel-0a7388d8 judged specs/concorde/workflows/requirements.md at req.workflows.bounded-wait, line 79 by the interfaces criterion of the Protocol's Evaluating a Spec; the Specs read: “`concorde workflow step` SHALL return within its `--wait` seconds”. Execution's detached announcement may wait “60 seconds from its start”; workflow_step permits the process `wait` plus 60 seconds and its server call `wait` plus 120 seconds.\n\nThe panel's chair merged a1.3, a2.3 and verified: Confirmed the synchronous launch sequence, Execution handshake and MCP bounds. Medium concerns short waits and slow launch; deciding total versus phase-specific deadlines changes behavior.",
        "owner_target_id": "module.workflows",
        "evidence": [
          {
            "path": "specs/concorde/workflows/requirements.md",
            "description": "req.workflows.bounded-wait, cited by the interfaces finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T074406-spec_panel-0a7388d8",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.workflows",
        "context_id": "sha256:2c305b6afec96b63a500449fab50ec9cf6cf675aff322d77216b1a05e4ce1462",
        "change_id": "parts-review-specs",
        "head": "959c856c3a7732af1420829a271f59dd21ba837c"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "duplicate",
      "note": "Same problem as I-c9732ed8: req.workflows.bounded-wait promises a return within --wait, but the detached launch (Execution's announcement wait, up to 60 s, runner.md) runs under the deadline unbounded, and contracts.md 'Starting a workflow step' already allows wait + 60 s (process) and wait + 120 s (call). The fix of I-c9732ed8 must choose between bounding the launch and narrowing the requirement to '--wait plus the launch handshake', matching the MCP tool's grace. Pre-existing: requirement identical on main.",
      "evidence": [
        "specs/concorde/workflows/requirements.md",
        "specs/concorde/workflows/contracts.md",
        "specs/concorde/execution/runner.md"
      ],
      "duplicate_of": "I-c9732ed8ffd459b5b2346bd87996eed6",
      "actor": "task-session",
      "created_at": "2026-10-03T08:49:11.384205+00:00"
    }
  ]
}
```
