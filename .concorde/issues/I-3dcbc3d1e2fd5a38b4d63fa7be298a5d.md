# I-3dcbc3d1e2fd5a38b4d63fa7be298a5d

```json
{
  "schema_version": 4,
  "id": "I-3dcbc3d1e2fd5a38b4d63fa7be298a5d",
  "status": "open",
  "reports": [
    {
      "id": "sha256:8d137d42d3a067b009b3f9db0f922801a39fdb8582cf8ed598dfc65bfbd68dcd",
      "created_at": "2026-10-02T19:46:41.882250+00:00",
      "report": {
        "report_key": "module.method/19",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "Brownfield requires data its provider contracts do not supply",
        "description": "Brownfield consumes dependency and readiness data that its providers do not expose through the workflow handoff Method promises to use.\n\nSuggested repair: Define the precise workflow.data consumed by brownfield and link to canonical Scaffold and Validation contributions. Scaffold should supply created identities with their dependencies; Validation should supply readiness and its blocking contribution. Coordinate versioned provider contract changes with the generic step-outcome repair.\n\nOther Modules concerned: module.scaffold, module.validation, module.workflows, module.adoption",
        "impact": "The normal brownfield script cannot obtain its dependency graph or readiness through the stated generic boundary without undocumented provider interpretation.",
        "basis": "spec_panel run r-20261002T190724-spec_panel-89d5bab4 judged specs/concorde/method/brownfield.md at The script, line 15 by the interfaces criterion of the Protocol's Evaluating a Spec; the Specs read: brownfield.md reads created Modules “with the `uses` among them, from that run's output itself” and decides from validation readiness. contract.scaffold.record is closed and has neither dependency lists nor a workflow contribution. contract.validation.readiness is also closed without workflow. contract.workflows.step-output says an output without workflow “declares nothing and hands the script nothing”.\n\nThe panel's chair merged a1.8, a2.3 and verified: Verified both complete provider output shapes and Workflows' convention. Merged the narrower Scaffold report with the consumer collaboration report. High severity because this blocks the ordinary procedure; preferred-fix because explicit provider-owned payloads implement the agreed generic boundary.",
        "owner_target_id": "module.method",
        "evidence": [
          {
            "path": "specs/concorde/method/brownfield.md",
            "description": "The script, cited by the interfaces finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261002T190724-spec_panel-89d5bab4",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.method",
        "context_id": "sha256:031e5d291c8c83e08d3a366b69fb1a477e63583a3bcc70652d30789e41ee4690",
        "change_id": "parts-spec",
        "head": "5c717b606e11e429829ec27129610d7a6d21916a"
      }
    }
  ],
  "dispositions": []
}
```
