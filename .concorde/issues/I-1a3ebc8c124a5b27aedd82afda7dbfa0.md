# I-1a3ebc8c124a5b27aedd82afda7dbfa0

```json
{
  "schema_version": 4,
  "id": "I-1a3ebc8c124a5b27aedd82afda7dbfa0",
  "status": "open",
  "reports": [
    {
      "id": "sha256:37b67a24fea0f72d309a74a9716dc7cdd5144e10e98152a5c03f82ca9287f983",
      "created_at": "2026-10-13T20:17:50.823556+00:00",
      "report": {
        "report_key": "spec-panel/module.validation/14",
        "tier": "suggestion",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Expose readiness semantics in readable contract prose",
        "description": "Most human-facing readiness semantics are embedded in one JSON string instead of the readable contract introduction.\n\nSuggested repair: Present field meanings in a readable table and separate paragraphs for partial results, validity and compatibility before the schema. Keep each rule canonical and refer to it from the semantics field.",
        "impact": "Every reader interpreting the output must unpack a large string to distinguish recorded Modules from check selection and interpret finding references.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/validation/contracts.md at contract.validation.readiness, line 337 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: The contract's single semantics string defines modules, finding refs, partial-call result recovery, validity and compatibility. For example, “modules lists, sorted, the changed Modules ... together with the run's Modules” appears only there, below the schema.\n\nThe panel's chair merged r2.5 and verified: Verified the semantics exist, so this is presentation rather than an interface gap. Medium advisory severity reflects substantial recurring reading effort, not sentence-length checking.",
        "owner_target_id": "module.validation",
        "evidence": [
          {
            "path": "specs/concorde/method/validation/contracts.md",
            "description": "contract.validation.readiness, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.validation",
        "context_id": "sha256:1a400b34d37a1f024a7c54437d33cf8fa9b24de6c288b72e32f946471ebfde41",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
