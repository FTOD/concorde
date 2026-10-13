# I-130c2bbff2eb5fefa7ce27e19a4f5dfa

```json
{
  "schema_version": 4,
  "id": "I-130c2bbff2eb5fefa7ce27e19a4f5dfa",
  "status": "open",
  "reports": [
    {
      "id": "sha256:67ff020f28471a824ffe941dbc92d589d7f47233f9f0ea8a9e92d342108aa8a4",
      "created_at": "2026-10-13T20:05:59.572601+00:00",
      "report": {
        "report_key": "spec-panel/module.tasks/16",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Unreadable markers have conflicting refusal codes",
        "description": "The requirement assigns the foreign-marker error to unreadable markers even though the interface distinguishes those failures.\n\nSuggested repair: Keep merge_incomplete for readable foreign markers and specify unreadable_merge_marker for unreadable or invalid markers, retaining the no-change guarantee and underlying Kernel refusal.",
        "impact": "Consumers and tests cannot rely on one error code for corrupt or unreadable markers.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/coordination/tasks/requirements.md at req.tasks.foreign-marker-refused, line 606 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The requirement prescribes merge_incomplete while \"a marker of another part, or a marker it cannot read, remains\". The contract and scenario.tasks.merge-foreign-marker prescribe unreadable_merge_marker for an unreadable marker.\n\nThe panel's chair merged r2.4 and verified: Verified the requirement, error table, entry and scenario. Medium for malformed-marker handling; preferred-fix follows their consistent distinction between foreign and unreadable markers.",
        "owner_target_id": "module.tasks",
        "evidence": [
          {
            "path": "specs/concorde/coordination/tasks/requirements.md",
            "description": "req.tasks.foreign-marker-refused, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.tasks",
        "context_id": "sha256:f497bc164eba45dad39aa87bce07d7df8632247026c710b423b2a3e9bcb91301",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
