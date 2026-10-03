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
    },
    {
      "id": "sha256:ac3d3fbbf5f26d39d792ec69d729860adb05f84ddacd42251175511ff0833a72",
      "created_at": "2026-10-03T08:50:18.241798+00:00",
      "report": {
        "issue_id": "I-fbdad9e5f3825fb69c23bfd745dac37a",
        "expected_revision": "sha256:44beee25e3eb853fa8f0c2f80b1b208b6d72a6d46f69e343c59d0e634743a5b2",
        "report_key": "module.method/3-verified",
        "tier": "obvious-fix",
        "severity": "low",
        "title": "Method's status table maps from the worker result, missing a failed Workers run with an ok worker result",
        "description": "specs/concorde/method/workers.md, 'The round validation', the outcome-to-status table (first matching row wins) has no row for a Workers run record that ended `failed` while the worker result is `ok` or `blocked`, such as Workers' deletion_failed or validation_unavailable (worker-harness/workers/launch.md), so the row 'Worker result status ok, audit clean, every check passed -> ok' formally matches. The errors table already has 'Any other failure of a worker run -> the run record's code', and the code (src/concorde/method/workers.py, absorb) maps from the run record's status. Fix: insert after the first two rows 'The worker run's record ended failed for any other reason (such as deletion_failed or validation_unavailable) -> failed', and qualify the ok row with 'and the worker run's record ended ok'.",
        "impact": "Spec imprecision only: the implementation reads the run record's status and fails such runs correctly; an implementer following the table literally could report ok after a failed deletion.",
        "basis": "Read the table and errors table in specs/concorde/method/workers.md, Workers' launch.md (deletion_failed, validation_unavailable), and src/concorde/method/workers.py (status = record['status']). Classification: pre-existing. Main's specs/concorde/execution/operations/workers.md had the same table without such a row, and main's execution/workers/launch.md already had deletion_failed. Severity lowered from medium to low because the code is correct.",
        "owner_target_id": "module.method",
        "type": "gap",
        "subtype": "spec-conflict",
        "evidence": [
          {
            "path": "specs/concorde/method/workers.md",
            "description": "outcome-to-status table in The round validation"
          },
          {
            "path": "specs/concorde/worker-harness/workers/launch.md",
            "description": "deletion_failed and validation_unavailable end the run failed"
          },
          {
            "path": "src/concorde/method/workers.py",
            "description": "status mapped from the run record"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-910065f1-25d2-4c31-a88f-81c1e1f04127",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.method",
        "context_id": "sha256:dc5a1d8cbf5a69d2834f2ea5f6545ea6067e5caf2e4e3c78dfc4f3342c22cb32",
        "change_id": "parts-review-specs",
        "head": "41bda04db324df4ff913498f023597a72c419955"
      }
    }
  ],
  "dispositions": []
}
```
