# I-fde7a6ca2fa45c0eae2c6352d480b6fc

```json
{
  "schema_version": 4,
  "id": "I-fde7a6ca2fa45c0eae2c6352d480b6fc",
  "status": "open",
  "reports": [
    {
      "id": "sha256:afc5e170114d4f63a04e6bc97ad79e7120e841dfa72b3be659124521af4d1d32",
      "created_at": "2026-10-03T08:43:39.160775+00:00",
      "report": {
        "report_key": "module.distribution/9",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Protocol-manifest lacks a complete implementation contract",
        "description": "The command's precise precondition and complete flag-dependent effects are defined only in module-role prose. Existing scenarios cover several changed-manifest cases but leave the precondition refusal and unchanged-write behavior outside implementation reading.\n\nSuggested repair: Give protocol-manifest a canonical implementation contract for preconditions, writes and outcomes, reusing the existing scenarios. Add the stale-build/no-write refusal and unchanged --write cases, and link the explanatory table to the contract.\n\nOther Modules concerned: module.spec",
        "impact": "A task must treat module-role prose as the precise contract for a command that changes the Protocol binding; existing acceptance situations do not supply its complete preflight and write behavior.",
        "basis": "spec_panel run r-20261003T074406-spec_panel-0a7388d8 judged specs/concorde/distribution/module.md at reconciling-the-protocol-manifest, line 311 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “It first requires a fresh build and a readable tracked manifest whose every asset the build holds; otherwise it reports `invalid` with `CONCORDE-PROTOCOL-MANIFEST-001` naming the problem and writes nothing, whatever its flags.” This precondition and the full flag/write table appear only in module.md.\n\nThe panel's chair merged r1.9 and verified: Verified the requirements and all Protocol-manifest scenarios. Some flag behaviors are already specified in scenarios, so the repair should fill the missing canonical precondition and complete the contract, not create duplicate requirements for every case. Medium severity and preferred-fix reflect a clear contract-location repair with several possible organizations.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/module.md",
            "description": "reconciling-the-protocol-manifest, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T074406-spec_panel-0a7388d8",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:2ff62e1118b212ef9ad5fe6e9d93adf72d0b8ac20908c609971a80ecb027ae5f",
        "change_id": "parts-review-specs",
        "head": "959c856c3a7732af1420829a271f59dd21ba837c"
      }
    }
  ],
  "dispositions": []
}
```
