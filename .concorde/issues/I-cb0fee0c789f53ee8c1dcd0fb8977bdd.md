# I-cb0fee0c789f53ee8c1dcd0fb8977bdd

```json
{
  "schema_version": 4,
  "id": "I-cb0fee0c789f53ee8c1dcd0fb8977bdd",
  "status": "open",
  "reports": [
    {
      "id": "sha256:fb1009aa0db94809d0f5aac473a12a06ecb1d5526bcda7339e769767cd05417a",
      "created_at": "2026-10-13T19:25:04.770345+00:00",
      "report": {
        "report_key": "spec-panel/module.spec/21",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The entry omits the transaction concurrency precondition",
        "description": "The entry explains transactional safety without the exclusive-writer precondition its adopted format requires.\n\nSuggested repair: State that callers exclude competing writes throughout the transaction and that digest checks do not provide isolation. Identify caller responsibility for initialization, registry regeneration and installation binding without inventing an undocumented lock.\n\nOther Modules concerned: module.kernel",
        "impact": "A caller could mistake digest checks and rollback for isolation and allow writes that overwrite another writer's changes.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/spec-tooling/spec/module.md at uses-kernel, line 501 by the design criterion of the Protocol's Evaluating a Spec; the Specs read: “Initialization and registry regeneration write through file transactions. Thus, a failure they observe never leaves half an update behind.” Kernel contracts.md:543–549 says concurrent changes can be overwritten and the caller must exclude every other writer for the whole transaction.\n\nThe panel's chair merged r2.11 and verified: Verified the entry and selected Kernel concurrency contract. The precondition is available in selected context but absent beside the entry's safe-use guarantee. Medium, preferred-fix because exposing an existing precondition does not invent a new locking promise.",
        "owner_target_id": "module.spec",
        "evidence": [
          {
            "path": "specs/concorde/spec-tooling/spec/module.md",
            "description": "uses-kernel, cited by the design finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec",
        "context_id": "sha256:9a8205f3d9b7372077a103ac4774b7e0aa10ec031c1fc770920c798b246c0ad7",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
