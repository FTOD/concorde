# I-7aebc9c0fb2759a0aee38f1aabcf1a62

```json
{
  "schema_version": 4,
  "id": "I-7aebc9c0fb2759a0aee38f1aabcf1a62",
  "status": "open",
  "reports": [
    {
      "id": "sha256:1a5893e97a192ee6ce37d73308e97cbb7eb9eb7efb941e773ac12fa1324c9bfb",
      "created_at": "2026-10-13T17:57:03.116803+00:00",
      "report": {
        "report_key": "spec-panel/module.concorde/13",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The reasoning-level source promise conflicts with the backend-default fallback",
        "description": "The root unconditionally sources every reasoning level from checkout configuration, while the selected provider contract permits the program's default.\n\nSuggested repair: Decide whether omitted reasoning levels may use the agent program's default. Prefer retaining the existing worker contract and qualifying the root promise to cover configured choices, with an explicit default exception and canonical link.\n\nOther Modules concerned: module.workers",
        "impact": "An implementer cannot satisfy the unconditional source promise while also allowing a valid configuration to defer its effective reasoning level to the agent program.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/requirements.md at req.concorde.worker-models-per-worktree, line 130 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"The model and reasoning level of every worker SHALL come from the worker configuration of the checkout its run works in\". contract.workers.worker-configuration resolves an omitted reasoning level to \"otherwise none, which leaves the program's own default level.\"\n\nThe panel's chair merged r2.3 and verified: Verified the root requirement and the worker-configuration contract's exact fallback. Medium severity applies to omitted-level configurations. Choosing whether the root promises an explicit effective level or allows a backend default changes the stated guarantee and therefore needs a decision.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/requirements.md",
            "description": "req.concorde.worker-models-per-worktree, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.concorde",
        "context_id": "sha256:7505f2053f2a75c7156099c5a9afbde65ad8ffd5fa4510cd835baf28a4b6db63",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
