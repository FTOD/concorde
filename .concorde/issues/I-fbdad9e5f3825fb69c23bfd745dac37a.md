# I-fbdad9e5f3825fb69c23bfd745dac37a

```json
{
  "schema_version": 4,
  "id": "I-fbdad9e5f3825fb69c23bfd745dac37a",
  "status": "open",
  "reports": [
    {
      "id": "sha256:0145fd5d7a99625ea126e526f695631710d9859a8e8b47983cd7ac95230bc595",
      "created_at": "2026-10-03T08:33:19.854478+00:00",
      "report": {
        "report_key": "module.method/3",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "Preserve Workers' host failures in Method's status mapping",
        "description": "Method's ordered status mapping does not account for every failed Workers run before examining the worker's claimed status. It contradicts the host failure precedence promised by Workers.\n\nSuggested repair: After the final glossary-ownership override, make any failed Workers run yield failed and retain its error as a cause. Require an ok Workers record for success, and align step 8 and the flow with deletion and validation-unavailable failures.\n\nOther Modules concerned: module.workers, module.implementation, module.specification, module.adoption",
        "impact": "An implementer following Method's ordered table can hide a failed deletion or unavailable validation behind an ok or blocked worker claim.",
        "basis": "spec_panel run r-20261003T074406-spec_panel-0a7388d8 judged specs/concorde/method/workers.md at The round validation, line 171 by the consistency criterion of the Protocol's Evaluating a Spec; the Specs read: Method says \"the first matching row wins\" and maps \"Worker result status `blocked`\" to blocked and \"Worker result status `ok`, audit clean, every check passed\" to ok. Workers' launch.md says: \"When a deletion failed, the run ends `failed` with `deletion_failed` whatever status it would otherwise have had\" and its rounds table fails a run when validation is unavailable.\n\nThe panel's chair merged r2.2, a2.3 and verified: Verified the status table, step 8, Method's catch-all worker-run error row and Workers' deletion and validation rules. Medium because these are exceptional outcomes; obvious-fix because the provider already fixes their failure semantics.",
        "owner_target_id": "module.method",
        "evidence": [
          {
            "path": "specs/concorde/method/workers.md",
            "description": "The round validation, cited by the consistency finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T074406-spec_panel-0a7388d8",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.method",
        "context_id": "sha256:883e787b374e75b7096580c3ab82f42b6e7a2c3910c13ad095e11873f874c95b",
        "change_id": "parts-review-specs",
        "head": "959c856c3a7732af1420829a271f59dd21ba837c"
      }
    }
  ],
  "dispositions": []
}
```
