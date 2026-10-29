# I-20ce0e0cf8bc512bba8f1dcf6e6d187e

```json
{
  "schema_version": 4,
  "id": "I-20ce0e0cf8bc512bba8f1dcf6e6d187e",
  "status": "open",
  "reports": [
    {
      "id": "sha256:75369a296375d4102eafb3510a650355359e68ddffd3354e07a3765779a4ee46",
      "created_at": "2026-10-29T07:29:19.211753+00:00",
      "report": {
        "report_key": "spec-panel/module.kernel/1",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Lock calls leave argument meanings and holder return types unspecified",
        "description": "The lock rows do not explain workspace_lock's waiting and task arguments or the representation of holder. The holder-reading calls promise a holder line without specifying text versus an object.\n\nSuggested repair: Specify each argument's meaning and type, and choose the holder-reading return representation. Explicitly identify any arguments forwarded unchanged to Tracing's locks.hold and reconcile the removed/replaced wording for retake.",
        "impact": "Callers cannot confidently construct optional lock arguments or consume the holder-reading result without implementation knowledge.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 judged specs/concorde/kernel/contracts.md at library by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: workspace_lock takes `waiting=None, task=None, retake=True`, but its Takes cell says only \"the `.concorde` a binding names, the workspace, the holder, how long to wait and whether to take a lock file its holder removed meanwhile\". Holder reads return \"its holder line, or none when nobody holds it\".\n\nThe panel's chair merged r1.2 and verified: Verified both Kernel lock rows and Tracing's Library, which distinguishes holder text from entry objects and explains waiting. Medium because optional usage is affected; decision-needed because selecting the unspecified public return representation determines the interface promise.",
        "owner_target_id": "module.kernel",
        "evidence": [
          {
            "path": "specs/concorde/kernel/contracts.md",
            "description": "library, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.kernel",
        "context_id": "sha256:8536de46e038445d36f6035d0a0dc61acbc58838be68d4f4f4cdf83503df7d10",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
