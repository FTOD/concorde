# I-e6635dfe06dc5d81bf4ad7b7ca279b7f

```json
{
  "schema_version": 3,
  "id": "I-e6635dfe06dc5d81bf4ad7b7ca279b7f",
  "status": "open",
  "reports": [
    {
      "id": "sha256:3b446dd5922522cd730410ee81ac674a4006df3acb627fbbdec847fdea4fb93f",
      "created_at": "2026-10-01T05:21:54.383280+00:00",
      "report": {
        "report_key": "module.code-review/2",
        "tier": "preferred-fix",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Preserve obtained review metadata on incomplete outcomes",
        "description": "Worker failures and unresolved evidence leave report metadata null even when the corresponding information was obtained. A blocked reviewer’s returned summary is discarded, and successfully read earlier Issues disappear from the report whenever processing exits before settlement.\n\nSuggested repair: Initialize the earlier-Issue report with all offered Issues carried as soon as they are read, replacing it after successful settlement. Preserve each returned worker summary before handling its failure status, without accidentally copying a previous Module’s worker result after a prelaunch failure. Add assertions for both worker-failure and unresolved-evidence reports.",
        "impact": "Incomplete reports lose returned reviewer summaries and hide the earlier Issues that were actually offered. Consumers cannot distinguish unread Issue history from history read successfully before a later failure.",
        "basis": "code_review run r-20261001T051949-code_review-25f69f0d (module review) judged src/concorde/code_review/operation.py:743-757, src/concorde/code_review/operation.py:785-797, src/concorde/code_review/operation.py:829-837 against contract.code-review.review and reported a violation: The contract says summary is null 'when no reviewer returned one' and earlier_issues is null 'when the Module’s earlier Issues were never read'. In _judge, the Stop branch returns before assigning review.summary; evidence failures return before issues.settle. derive_verdict emits `\"summary\": item.summary` and `\"earlier_issues\": item.settled`, whose defaults are null.",
        "owner_target_id": "module.code-review",
        "evidence": [
          {
            "path": "src/concorde/code_review/operation.py",
            "description": "lines 743-757, shown by the violation finding"
          },
          {
            "path": "src/concorde/code_review/operation.py",
            "description": "lines 785-797, shown by the violation finding"
          },
          {
            "path": "src/concorde/code_review/operation.py",
            "description": "lines 829-837, shown by the violation finding"
          },
          {
            "path": "specs/concorde/execution/operations/code-review/contracts.md",
            "description": "defines contract.code-review.review, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051949-code_review-25f69f0d",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.code-review",
        "context_id": "sha256:45c63103050415ac5e01a3bed7084fe742e73432651c0b381e2b4203e3f5a6f2",
        "change_id": "module-code-review",
        "head": "e59262e0bd4e6b3d8a5c520dd44a66bd0b41faaa"
      }
    }
  ],
  "dispositions": []
}
```
