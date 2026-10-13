# I-90e1c2cbbaa250efafb4bb30eef40d9e

```json
{
  "schema_version": 4,
  "id": "I-90e1c2cbbaa250efafb4bb30eef40d9e",
  "status": "open",
  "reports": [
    {
      "id": "sha256:873730b692774f0193cad727a59ed99ba6bf89b22a9d3ea8bd27fa3ec956ea11",
      "created_at": "2026-10-13T19:54:26.779853+00:00",
      "report": {
        "report_key": "spec-panel/module.specification/5",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Document deletion lacks a registration and validation sequence",
        "description": "The file-deletion mechanism is available from Workers, but Specification does not define how deleting a Spec document coordinates its reading file, metadata and owns registration. It gives no valid sequence through round validation, host deletion and final validation.\n\nSuggested repair: Define one complete document-deletion procedure: the proposed_deletions entries for the document pair, the actor and timing for owns changes, and how validation handles the state before and after Workers performs deletion. Link to Workers for the file-level mechanics and add a concrete deletion scenario.\n\nOther Modules concerned: module.workers, module.method",
        "impact": "A worker can leave ownership metadata referring to deleted documents, or remove registration before validation without a stated procedure for the still-present document pair. The final validation can then block the run after repair opportunities have ended.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/specification/module.md at New and deleted documents, line 218 by the design criterion of the Protocol's Evaluating a Spec; the Specs read: “An owned document is deleted only by proposing it. After a clean audit, the Operation performs the deletion.” The step table delegates proposed deletions to Workers. Workers' launch.md performs file deletions after the last round validation; Specification supplies no corresponding ownership-metadata update procedure.\n\nThe panel's chair merged r1.5 and verified: Workers' selected contract already defines proposed_deletions, so the claimed absence of a proposal field is not retained. Delegating deletion to Workers is also compatible with Operation-level responsibility. The unresolved document-pair and owns-update sequence remains a medium blocking gap requiring a design decision.",
        "owner_target_id": "module.specification",
        "evidence": [
          {
            "path": "specs/concorde/method/specification/module.md",
            "description": "New and deleted documents, cited by the design finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.specification",
        "context_id": "sha256:ce0905a0b37eb1808516eaa1c8160029e96d19b43026433e2ec0580cda53e75e",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
