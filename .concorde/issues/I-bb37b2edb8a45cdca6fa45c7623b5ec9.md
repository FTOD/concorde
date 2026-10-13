# I-bb37b2edb8a45cdca6fa45c7623b5ec9

```json
{
  "schema_version": 4,
  "id": "I-bb37b2edb8a45cdca6fa45c7623b5ec9",
  "status": "open",
  "reports": [
    {
      "id": "sha256:4e1d8344d65e0f4cf1d515da34505001b4eb8659a68be929a6a0fd7b23dc3878",
      "created_at": "2026-10-13T18:21:37.023383+00:00",
      "report": {
        "report_key": "spec-panel/module.dogfooding/18",
        "tier": "suggestion",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Present refusal-specific recovery actions as a list",
        "description": "The refusal-code cases and their actions are packed into one paragraph instead of a readily comparable list.\n\nSuggested repair: Present the environment refusal codes and their recovery actions in a short list or two-column table.",
        "impact": "Readers must scan a paragraph to locate the action for a particular refusal code.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/dogfooding/module.md at A failure of the Issue system, line 364 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: \"It finishes an unfinished merge for `merge_incomplete`. It fixes the cause that `commit_failed` names. It fixes the cause that `recovery_failed` names and then runs `concorde issues recover`. It inspects and reverts the record's change for `uncommitted_change`.\"\n\nThe panel's chair merged r1.15 and verified: Verified the run of code/action cases. Retained only the instance in this document, rather than bundling a separate requirements-document example. Low advisory presentation improvement.",
        "owner_target_id": "module.dogfooding",
        "evidence": [
          {
            "path": "specs/concorde/dogfooding/module.md",
            "description": "A failure of the Issue system, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.dogfooding",
        "context_id": "sha256:8f5ee9701ec7233fe2257825efd4007f478812f4816657c310d2c1d21c4410f6",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
