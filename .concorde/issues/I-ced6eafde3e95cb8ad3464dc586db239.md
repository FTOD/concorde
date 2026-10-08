# I-ced6eafde3e95cb8ad3464dc586db239

```json
{
  "schema_version": 4,
  "id": "I-ced6eafde3e95cb8ad3464dc586db239",
  "status": "open",
  "reports": [
    {
      "id": "sha256:a4cc87b482ca88c4fc1d173f3814a981cc9dfedad2f1b3b430abc5c8ed3d1e5e",
      "created_at": "2026-10-08T07:55:53.832257+00:00",
      "report": {
        "report_key": "code-review/module.general-work/2",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Give the reviewer the input material needed to verify the work",
        "description": "The review handoff omits admitted inputs and the workspace goal even though they are provided to the worker and may be necessary to interpret and verify the caller's instruction.\n\nSuggested repair: Include the same admitted input material and workspace goal in the reviewer's brief, still keeping the worker's answer separate as a claim. Add a handoff test for an instruction whose answer depends on an admitted output.",
        "impact": "For an instruction such as 'Summarize the admitted run outputs', the reviewer has only the worker's purported summary, with no source material to check it against. It must block or return a review without verifying the central claim. Instructions referring to the workspace goal have the same problem.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/method/general_work/operation.py:381-390, src/concorde/method/general_work/operation.py:431-458 against specs/concorde/method/general-work/module.md#the-review and reported a defect: worker_instructions() supplies both the workspace goal and inputs_material(ctx). reviewer_instructions() supplies only the bound Module names, instruction, change and answer; review() adds readable access only to change.diff and before/. The Spec supports --input material and says the reviewer 'judges whether the result does what the instruction asks'.",
        "owner_target_id": "module.general-work",
        "evidence": [
          {
            "path": "src/concorde/method/general_work/operation.py",
            "description": "lines 381-390, shown by the defect finding"
          },
          {
            "path": "src/concorde/method/general_work/operation.py",
            "description": "lines 431-458, shown by the defect finding"
          },
          {
            "path": "specs/concorde/method/general-work/module.md",
            "description": "defines specs/concorde/method/general-work/module.md#the-review, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.general-work",
        "context_id": "sha256:b235e36c0f88cdeeb77624cbec0b5a434f24ca9386e7777c5546c8ce6d18f586",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
