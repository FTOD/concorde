# I-a0a8f1dd01ef5b8fa2ac0ccd599faec8

```json
{
  "schema_version": 4,
  "id": "I-a0a8f1dd01ef5b8fa2ac0ccd599faec8",
  "status": "open",
  "reports": [
    {
      "id": "sha256:7f9cccdd6d11ffca95d261b1b653b0695e1e5a49a1f28e04ac40841d6cf95cbe",
      "created_at": "2026-10-08T08:41:39.150643+00:00",
      "report": {
        "report_key": "spec-panel/module.spec-mcp/1",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "Select the provider contracts needed to interpret tool results",
        "description": "The public contracts rely on provider documents that the Module's declarations do not select. Links to those documents do not make their definitions available in the Module's context.\n\nSuggested repair: Extend the Spec core dependency selection to the promises defining source and term records, validation results and error records in specs/concorde/spec-tooling/spec/contracts.md and specs/concorde/spec-tooling/spec/errors.md. Keep the canonical definitions with Spec core and retain the links.\n\nOther Modules concerned: module.spec",
        "impact": "An implementer or consumer cannot determine the canonical context, validation and error record formats from the selected context, or establish that results preserve Spec core's records unchanged.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/spec-tooling/spec-mcp/contracts.md at Tools, line 45 by the context criterion of the Protocol's Evaluating a Spec; the Specs read: The context result uses Spec core's “source and term records” at ../spec/contracts.md#spec-context-records; validate uses ../spec/contracts.md#validation-result; Session uses the “error record” at ../spec/errors.md#the-error-record. module.md.json selects only concept.grant, concept.context-identity, concept.boundary-set, concept.impact-index, concept.structural-check and concept.registry, and declares no includes.\n\nThe panel's chair merged r1.1, r2.1, r3.1 and verified: Verified the three delegated definitions, the dependency selection, and the supplied Spec core entry. The entry explains the concepts but does not supply these canonical records. High severity reflects missing contracts in main tool uses; preferred-fix reflects the clear repair of selecting the provider's defining promises without duplicating them.",
        "owner_target_id": "module.spec-mcp",
        "evidence": [
          {
            "path": "specs/concorde/spec-tooling/spec-mcp/contracts.md",
            "description": "Tools, cited by the context finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec-mcp",
        "context_id": "sha256:af82eaf7bfd3aac2fcb03f3bdb58251bc378347bc7f2b624c34d591d59b1dcbd",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
