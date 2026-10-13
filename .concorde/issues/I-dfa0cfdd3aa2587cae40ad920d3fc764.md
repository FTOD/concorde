# I-dfa0cfdd3aa2587cae40ad920d3fc764

```json
{
  "schema_version": 4,
  "id": "I-dfa0cfdd3aa2587cae40ad920d3fc764",
  "status": "open",
  "reports": [
    {
      "id": "sha256:fbe57d36239527c1a822b06a3e0767e0df391110ae5a2603f5281ccffd61b3cf",
      "created_at": "2026-10-13T17:46:34.497404+00:00",
      "report": {
        "report_key": "spec-panel/module.commands/11",
        "tier": "suggestion",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Place registration timing conditions before their actions",
        "description": "Registration and loading sentences place timing conditions after the actions they limit.\n\nSuggested repair: Move each timing condition before its action while preserving its scope, for example: “When the providing part's code loads, the part registers the command's definition.”",
        "impact": "Readers encounter the action before the timing condition that limits it.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/execution/commands/module.md at The command table, line 190 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: “The part that provides a command registers the command's definition when the part's code loads.” Earlier, “The catalog refuses it when it loads, naming both parts.”\n\nThe panel's chair merged r2.6 and verified: Verified both trailing timing conditions. Their meaning is recoverable and no obligation changes, so this is an advisory sentence-style finding of low severity.",
        "owner_target_id": "module.commands",
        "evidence": [
          {
            "path": "specs/concorde/execution/commands/module.md",
            "description": "The command table, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.commands",
        "context_id": "sha256:d199563290b24d8f2cbce6f23700239d07543af9afdae821accb5aa1c987016c",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
