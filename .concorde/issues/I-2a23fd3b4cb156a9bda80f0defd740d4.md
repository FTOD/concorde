# I-2a23fd3b4cb156a9bda80f0defd740d4

```json
{
  "schema_version": 4,
  "id": "I-2a23fd3b4cb156a9bda80f0defd740d4",
  "status": "open",
  "reports": [
    {
      "id": "sha256:4e324bb2eddee6804110860641b68983a670e9c1d83720d9676b6b4dc000c6e4",
      "created_at": "2026-10-08T09:17:27.571159+00:00",
      "report": {
        "report_key": "spec-panel/module.tasks/4",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "Selected context omits contracts Tasks directly consumes",
        "description": "The selected context omits precise external contracts that Tasks directly consumes, including the workflow synchronization promise on which safe archival depends.\n\nSuggested repair: Select the consumed Execution result and progress formats, Issues command interface and Spec registry format from their defining documents. Declare and select the Workflows locking and retirement collaboration, including its entry and canonical defining document. Keep selections limited to the promises Tasks uses.\n\nOther Modules concerned: module.execution, module.issues, module.spec, module.workflows",
        "impact": "A task bound to Tasks lacks canonical input formats and the provider locking promise needed to implement its integrations reliably.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/coordination/tasks/contracts.md at parts-not-depended-on, line 1119 by the context criterion of the Protocol's Evaluating a Spec; the Specs read: Tasks explicitly reads execution/contracts.md#contract.execution.run-result, invokes Issues show/recover/close and reads their answers, and relies on Workflows' lock allowing no other lock wait. Its module metadata selects Execution concepts, concept.registry and Issues' recovery requirement, with no Workflows selection. The entry also reads the registry \"through that mirror's format\".\n\nThe panel's chair merged r1.4, r2.5, r3.4 and verified: Verified Tasks' selections and reliance passages. Execution's selected entry delegates the envelope to contracts.md, and Issues' entry delegates exact interfaces to interface.md. The supplied boundary excludes those documents, the registry contract and Workflows documents. High severity affects ordinary integrations; explicit selection of existing relied-on promises is the preferred repair.",
        "owner_target_id": "module.tasks",
        "evidence": [
          {
            "path": "specs/concorde/coordination/tasks/contracts.md",
            "description": "parts-not-depended-on, cited by the context finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.tasks",
        "context_id": "sha256:371254edb81afb6f42aa4ce6761c1921cf5475dad4c7379cdf74220829d75420",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
