# I-7f5cd9e6a0ca5feb82fddc95e7fa0634

```json
{
  "schema_version": 4,
  "id": "I-7f5cd9e6a0ca5feb82fddc95e7fa0634",
  "status": "open",
  "reports": [
    {
      "id": "sha256:687a531de1f331027b0e861ca27afb479e824d4f3d48fb4a382c6c3b0f629630",
      "created_at": "2026-10-08T09:44:02.788181+00:00",
      "report": {
        "report_key": "code-review/module.workflows/6",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Workflow tool timeout refusals omit captured command output",
        "description": "The timeout refusal drops the output captured before the command timed out. It does not preserve the output tail required by the workflow_step refusal contract.\n\nSuggested repair: Handle TimeoutExpired separately and include bounded, safely decoded tails of its stdout and stderr, or an explicit no-output marker, in the refusal. Test a timeout exception carrying partial diagnostic output.",
        "impact": "Diagnostics printed before a step-command timeout disappear from the tool's error chain, making the timeout harder to investigate from the returned refusal.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/workflows/tools.py:165-185 against specs/concorde/workflows/contracts.md#refusals-of-the-tools and reported a violation: workflow_step captures subprocess output, but its TimeoutExpired handler constructs the refusal from `f\"`{shown}` in {root} did not answer: {error}\"` only. TimeoutExpired's string gives the command and timeout, not its captured stdout or stderr. The contract says step_failed detail carries the end of the command's output.",
        "owner_target_id": "module.workflows",
        "evidence": [
          {
            "path": "src/concorde/workflows/tools.py",
            "description": "lines 165-185, shown by the violation finding"
          },
          {
            "path": "specs/concorde/workflows/contracts.md",
            "description": "defines specs/concorde/workflows/contracts.md#refusals-of-the-tools, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.workflows",
        "context_id": "sha256:68c66c193fe463da1fbb4fa96d0de82eca92444f1e6c4885bc66a36525c6324b",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
