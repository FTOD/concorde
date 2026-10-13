# I-cb40daab2195569cadac8aecd873aea6

```json
{
  "schema_version": 4,
  "id": "I-cb40daab2195569cadac8aecd873aea6",
  "status": "open",
  "reports": [
    {
      "id": "sha256:a3847a54a0eee2984c93b9815c5f1444beb2a5f75d4782838a2f25f417735c03",
      "created_at": "2026-10-13T20:17:45.160380+00:00",
      "report": {
        "report_key": "spec-panel/module.validation/3",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The check-coverage requirement omits selection and execution exceptions",
        "description": "The check-running obligation omits the selective-check eligibility conditions and the failures that prevent execution. It also fails to express the documented selection of eligible selective checks owned outside the selected Modules.\n\nSuggested repair: Specify selection of the listed Modules and execution of ordinary and eligible selective checks under the canonical service rules. Keep the no-tests exception and execution-preventing failures within the obligation, with precise links.\n\nOther Modules concerned: module.checks",
        "impact": "Implementers and test authors receive incompatible rules for selective checks and failed check calls.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/validation/requirements.md at req.validation.changed-modules, line 50 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The requirement says the run “SHALL run the configured checks of all these Modules”. Step 6 says “When no test verifies a scenario of the selection, the call keeps no selective check and runs nothing”, and describes call failures that prevent checks from running. It also runs eligible selective checks whichever Module owns them.\n\nThe panel's chair merged r1.3, r2.2, r3.1 and verified: Verified all three reports against the requirement, step 6, selective-check scenario and Check execution's service contract. Medium severity reflects eligibility and failure cases rather than universal failure of the main flow. Aligning the requirement with the documented service rules is the preferred repair.",
        "owner_target_id": "module.validation",
        "evidence": [
          {
            "path": "specs/concorde/method/validation/requirements.md",
            "description": "req.validation.changed-modules, cited by the obligations finding"
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
