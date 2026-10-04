# I-fde7a6ca2fa45c0eae2c6352d480b6fc

```json
{
  "schema_version": 4,
  "id": "I-fde7a6ca2fa45c0eae2c6352d480b6fc",
  "status": "closed",
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
    },
    {
      "id": "sha256:26494c13249c81f661d23dfca32c690e3db3ebf9cec352c8f069f80db18d2f27",
      "created_at": "2026-10-03T08:49:46.766910+00:00",
      "report": {
        "issue_id": "I-fde7a6ca2fa45c0eae2c6352d480b6fc",
        "expected_revision": "sha256:c972182c5c72c9847a4f4d7ada223aae6fa2881e76e35cfd7f9526810532eb80",
        "report_key": "module.distribution/9-verified",
        "tier": "preferred-fix",
        "severity": "low",
        "title": "protocol-manifest's precondition and write table live only in module reading",
        "description": "specs/concorde/distribution/module.md, reconciling-the-protocol-manifest, states the fresh-build/readable-manifest precondition (refusal `invalid` with CONCORDE-PROTOCOL-MANIFEST-001, nothing written whatever the flags) and the flag-by-flag write table; requirements.md has no requirement for protocol-manifest and scenarios.md covers the changed-manifest cases but not the stale-build refusal or an unchanged `--write`.\n\nFix (preferred): add to requirements.md a requirement 'protocol-manifest SHALL write nothing and report invalid with CONCORDE-PROTOCOL-MANIFEST-001 when the build is stale or the tracked manifest is unreadable or names an asset the build lacks', and a scenario for that refusal, linking the module table to it; the table itself may stay explanatory.",
        "impact": "Minor: the behaviour is precise in the entry and the code follows it; an implementer reading only implementation documents misses the precondition.",
        "basis": "Read module.md and the protocol-manifest scenarios. Classification: pre-existing — the same paragraph and table are on main (git show main:specs/concorde/distribution/module.md, lines ~176-190) with no requirement either. Severity lowered from medium: nothing goes wrong; the precise text exists, only in the module role.",
        "owner_target_id": "module.distribution",
        "type": "bug",
        "subtype": null,
        "evidence": [
          {
            "path": "specs/concorde/distribution/module.md",
            "description": "reconciling-the-protocol-manifest precondition and flag table"
          },
          {
            "path": "specs/concorde/distribution/scenarios.md",
            "description": "protocol-manifest scenarios cover only a changed Protocol with a fresh build"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-560faa6d-6051-4f12-aebc-33f78dcbff18",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:dc5a1d8cbf5a69d2834f2ea5f6545ea6067e5caf2e4e3c78dfc4f3342c22cb32",
        "change_id": "parts-review-specs",
        "head": "41bda04db324df4ff913498f023597a72c419955"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-open-root-distribution, merged into the primary branch at 8a5cfc367a6280e7de01a6d243e445d6ee49f69d.",
      "evidence": [
        "merge commit 8a5cfc367a6280e7de01a6d243e445d6ee49f69d",
        "task fix-open-root-distribution"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-04T02:34:20.837004+00:00"
    }
  ]
}
```
