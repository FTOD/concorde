# I-431ebf9d2aba500cab75f1ed74fef3f0

```json
{
  "schema_version": 3,
  "id": "I-431ebf9d2aba500cab75f1ed74fef3f0",
  "status": "open",
  "reports": [
    {
      "id": "sha256:287a9f69d7e93348404b31549e8e4e87f07c8a32edb6249ed430ceeadf82f2d5",
      "created_at": "2026-10-01T05:22:40.610030+00:00",
      "report": {
        "report_key": "module.concorde/13",
        "tier": "decision-needed",
        "type": "bug",
        "subtype": null,
        "title": "Test evidence lacks input-identity and prior-report semantics",
        "description": "The promised JSON evidence interface names fingerprint categories and --prior without defining their coverage, representation, defaults, interpretation, or failure behavior.\n\nSuggested repair: Define the report's canonical readable contract: stable fields, fingerprint coverage and identity semantics, --prior input and omission behavior, invalid or unreadable prior handling, repeated output behavior, and compatibility limits. Add an example and scenarios that distinguish changed from unchanged examined inputs.\n\nOther Modules concerned: module.checks",
        "impact": "Implementers must invent what changes an input identity and how prior reports are supplied, while consumers cannot reliably interpret or compare evidence reports.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/development.md at req.concorde.test-evidence, line 13 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"The pytest evidence plugin SHALL record each run's reason, scope, phase, attempt and input fingerprints in its JSON report.\" The scenario accepts arguments \"with or without\" --prior and promises \"prior run and fingerprints of the tests, inputs, runtime, locks and environment\"; the explanation defines defaults only for reason, scope, phase and attempt.\n\nThe panel's chair merged r2.2, r3.1 and verified: Verified the entire development document; neither fingerprint semantics nor prior-run behavior is defined elsewhere in it. The two reports describe the same missing interface contract. Choosing identity and compatibility behavior requires a decision.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/development.md",
            "description": "req.concorde.test-evidence, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.concorde",
        "context_id": "sha256:305c8527376219b0846ea77dd1408f9fab3dc7a2668b3da9791a000f3b49a771",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    }
  ],
  "dispositions": []
}
```
