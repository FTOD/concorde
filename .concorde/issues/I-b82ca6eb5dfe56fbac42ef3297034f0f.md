# I-b82ca6eb5dfe56fbac42ef3297034f0f

```json
{
  "schema_version": 4,
  "id": "I-b82ca6eb5dfe56fbac42ef3297034f0f",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9839c11ae2245f9c1a6efccf47ae8ed05bf52def6f666c1189dd7a3802685b0a",
      "created_at": "2026-10-29T08:13:23.332621+00:00",
      "report": {
        "report_key": "code-review/module.validation/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Recheck the bound branch before issuing readiness",
        "description": "The bound branch is checked only before validation starts. If another process detaches HEAD or switches to another branch at the same commit during the run, the final input digest is unchanged and Validation still issues readiness off the bound branch.\n\nSuggested repair: Recheck the bound branch during final validation, before saving readiness, using the existing wrong_branch failure handling. Add regression tests that detach HEAD and switch to another branch at the same commit while checks run; neither case should save readiness.",
        "impact": "A caller can receive a ready verdict for a workspace that no longer satisfies the required branch precondition.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 (module review) judged src/concorde/method/validation/command.py:569-582, src/concorde/method/validation/measurement.py:349-355 against req.validation.bound-branch and reported a violation: remeasure compares only again['digest'] with state.inputs['digest'] and then returns Continue(). The measured value contains only head, base, changed and config_digest, so changing the symbolic branch without changing the commit or files is invisible. req.validation.bound-branch requires readiness only when the workspace's head is on the branch its binding names.",
        "owner_target_id": "module.validation",
        "evidence": [
          {
            "path": "src/concorde/method/validation/command.py",
            "description": "lines 569-582, shown by the violation finding"
          },
          {
            "path": "src/concorde/method/validation/measurement.py",
            "description": "lines 349-355, shown by the violation finding"
          },
          {
            "path": "specs/concorde/method/validation/requirements.md",
            "description": "defines req.validation.bound-branch, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.validation",
        "context_id": "sha256:4dae1a8a4c3fddfdd249a81fcef3d62ec000369f1663bb3aa515c4943b890ca3",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
