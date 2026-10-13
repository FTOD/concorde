# I-13dd7450d9ea5cfd89ad265e9ddab8ef

```json
{
  "schema_version": 4,
  "id": "I-13dd7450d9ea5cfd89ad265e9ddab8ef",
  "status": "open",
  "reports": [
    {
      "id": "sha256:0e5cdcdb69e7ab23b2a895ed5a8e7381b9a877dc24043e34d0348b862c0e0fae",
      "created_at": "2026-10-13T18:04:16.747144+00:00",
      "report": {
        "report_key": "spec-panel/module.delivery/4",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The commit contract omits two verification conditions",
        "description": "The canonical commit contract gives an incomplete set of conditions for verifying a newly created delivery commit.\n\nSuggested repair: Replace the partial list with a reference to req.delivery.commit-verified, or include all five conditions without weakening them.",
        "impact": "A reader using the contract's verification definition could accept a dirty worktree or a commit below a hook-created head that the requirement rejects.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/delivery/contracts.md at delivery-commit, line 37 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The contract's created-commit verification list contains only parent, subject and tree. req.delivery.commit-verified additionally requires \"It is the head of the bound branch\" and \"The worktree is clean.\"\n\nThe panel's chair merged r1.3 and verified: Compared the complete contract list with the five conditions in the requirement and step 10. Medium severity because the conflict arises with hook effects; obvious-fix because the missing conditions are already explicitly required.",
        "owner_target_id": "module.delivery",
        "evidence": [
          {
            "path": "specs/concorde/method/delivery/contracts.md",
            "description": "delivery-commit, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.delivery",
        "context_id": "sha256:2e9311c7fad1ddbccf1fc15ba4b778158051ec1d79be866c44ef2d3640127e10",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
