# I-d838bcb654245eb1ad36a501fdc8afbc

```json
{
  "schema_version": 3,
  "id": "I-d838bcb654245eb1ad36a501fdc8afbc",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:c47d4e6a47a96421adbaf0d462e9055820e5e465ae9929d0e703075889633ed1",
      "created_at": "2026-10-01T05:39:36.256567+00:00",
      "report": {
        "report_key": "module.e2e/2",
        "tier": "preferred-fix",
        "type": "bug",
        "subtype": null,
        "title": "Select the providers for preparation's complete model validation",
        "description": "Preparation directly relies on Workers' configuration and model-map contracts without declaring that provider. Its promise to validate every worker also lacks selected context defining the catalog over which validation operates.\n\nSuggested repair: Declare uses of Workers and select the configuration, model-map and refusal promises preparation consumes. Select the Operation catalog contract needed to enumerate workers, or an existing provider contract that performs that complete validation. Explain E2E's construction and preflight duties and propagation of refusals before cloning.\n\nOther Modules concerned: module.workers, module.operations",
        "impact": "An E2E task must construct and validate configuration without receiving the canonical rules and complete worker enumeration it must follow. Changes to those promises are absent from its declared dependency account.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/e2e/module.md at preparing-a-test-project, line 182 by the dependencies criterion of the Protocol's Evaluating a Spec; the Specs read: Preparation refuses \"a worker configuration whose models that map cannot resolve for every worker of every Operation, with Workers' own refusal (`model_unmapped`, `model_map_missing` or `model_map_invalid`)\". The entry metadata selects Workflows, Distribution, Execution, Main session and Tasks, but neither Workers nor the Operation catalog. Workers' entry owns configuration and model-map resolution; Operations' workers.md describes catalog-based validation.\n\nThe panel's chair merged r2.2, r3.2, a1.1, a2.1 and verified: Verified E2E's dependency selections, Workers' ownership and refusal rules, and Operations' catalog-based validation account. Merged the context and dependency reports. Preferred-fix because selecting the existing canonical contracts is preferable to duplicating them, while the precise selection depends on which provider performs enumeration.",
        "owner_target_id": "module.e2e",
        "evidence": [
          {
            "path": "specs/concorde/e2e/module.md",
            "description": "preparing-a-test-project, cited by the dependencies finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.e2e",
        "context_id": "sha256:6d1ed9a2394f063345e81a92404e19816da64eedbb1c079e0a2bac0dfb3233b5",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    },
    {
      "id": "sha256:66c973203db7003038e484e96cd9882ac2775b64164fa35779598bf9cb7e1b97",
      "created_at": "2026-10-01T14:47:43.803186+00:00",
      "report": {
        "report_key": "module.e2e/2--severity",
        "tier": "preferred-fix",
        "type": "bug",
        "subtype": null,
        "title": "Select the providers for preparation's complete model validation",
        "description": "Preparation directly relies on Workers' configuration and model-map contracts without declaring that provider. Its promise to validate every worker also lacks selected context defining the catalog over which validation operates.\n\nSuggested repair: Declare uses of Workers and select the configuration, model-map and refusal promises preparation consumes. Select the Operation catalog contract needed to enumerate workers, or an existing provider contract that performs that complete validation. Explain E2E's construction and preflight duties and propagation of refusals before cloning.\n\nOther Modules concerned: module.workers, module.operations",
        "impact": "An E2E task must construct and validate configuration without receiving the canonical rules and complete worker enumeration it must follow. Changes to those promises are absent from its declared dependency account.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/e2e/module.md at preparing-a-test-project, line 182 by the dependencies criterion of the Protocol's Evaluating a Spec; the Specs read: Preparation refuses \"a worker configuration whose models that map cannot resolve for every worker of every Operation, with Workers' own refusal (`model_unmapped`, `model_map_missing` or `model_map_invalid`)\". The entry metadata selects Workflows, Distribution, Execution, Main session and Tasks, but neither Workers nor the Operation catalog. Workers' entry owns configuration and model-map resolution; Operations' workers.md describes catalog-based validation.\n\nThe panel's chair merged r2.2, r3.2, a1.1, a2.1 and verified: Verified E2E's dependency selections, Workers' ownership and refusal rules, and Operations' catalog-based validation account. Merged the context and dependency reports. Preferred-fix because selecting the existing canonical contracts is preferable to duplicating them, while the precise selection depends on which provider performs enumeration. Severity medium assessed by the main agent on 2026-10-01: An E2E task must validate worker configuration without the selected Workers rules and worker catalog, slowing that work and hiding the dependency.",
        "owner_target_id": "module.e2e",
        "evidence": [
          {
            "path": "specs/concorde/e2e/module.md",
            "description": "preparing-a-test-project, cited by the dependencies finding"
          }
        ],
        "severity": "medium",
        "issue_id": "I-d838bcb654245eb1ad36a501fdc8afbc",
        "expected_revision": "sha256:b2154b9ebed96b0279ad26bbb6f74a80fe401103ee22d3098d92673dd6683618"
      },
      "source": {
        "invocation_id": "cli-952fd624-c5d2-4fac-97ab-90a3697b1a54",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.e2e",
        "context_id": "sha256:faf611ab5bdd47f3ab93968932072ec605e527fb468e96a4f6c20a419e8f0f8c",
        "change_id": null,
        "head": "f1529d8ad053f873f92891c033e8cdfa2a5ab30f"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-e2e, merged into the primary branch at 3dee80cd30cd6d16e23762e0a57be7440893347f.",
      "evidence": [
        "merge commit 3dee80cd30cd6d16e23762e0a57be7440893347f",
        "task fix-e2e"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-02T02:33:09.958046+00:00"
    }
  ]
}
```
