# I-560eb1ab37c957edbfd406f0febcdb23

```json
{
  "schema_version": 4,
  "id": "I-560eb1ab37c957edbfd406f0febcdb23",
  "status": "open",
  "reports": [
    {
      "id": "sha256:34ac46a6320330b0dfb0de8b332ac8526b7c8a49c079a13d729fb5f5cf9bc855",
      "created_at": "2026-10-13T16:50:32.642244+00:00",
      "report": {
        "report_key": "spec-panel/module.understanding/4",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Qualify audit-change retention for unbound runs",
        "description": "The explanation promises that violating changes remain for the caller without distinguishing bound workspaces from unbound checkouts that Execution removes.\n\nSuggested repair: Say Understanding does not revert audit violations, changes remain in a bound workspace, and Execution still removes an unbound checkout after failure. Identify the recorded audit evidence that survives cleanup.\n\nOther Modules concerned: module.execution",
        "impact": "A caller could expect changed files to remain inspectable after an unbound failure, or an implementer could incorrectly retain the disposable checkout.",
        "basis": "project_review run r-20261013T163902-project_review-dfe5114c judged specs/concorde/method/understanding/requirements.md at req.understanding.change-fails, line 90 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “The change is left in place for the caller, never reverted.” The task-worktree requirement explicitly includes unbound checkouts. Execution's selected entry says, “However the run ends, the runner removes the checkout before it writes the result.”\n\nThe panel's chair merged r2.4 and verified: Verified the retention statement, the inclusion of unbound runs, and Execution's unconditional cleanup promise. Medium for an audit-failure edge case; preferred-fix because limiting retention to bound workspaces reconciles the promises while preserving non-reversion by Understanding.",
        "owner_target_id": "module.understanding",
        "evidence": [
          {
            "path": "specs/concorde/method/understanding/requirements.md",
            "description": "req.understanding.change-fails, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T163902-project_review-dfe5114c",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.understanding",
        "context_id": "sha256:da348b1e52e4f85be2b0a66a4e14ec2c264ffac26aa2865dd4e428fc9ae66057",
        "change_id": null,
        "head": "1e5ce2576250630071825f0e00ce7f342e2f153d",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
