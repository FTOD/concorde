# I-faedb500be4d52a4b1f8feadfee54337

```json
{
  "schema_version": 4,
  "id": "I-faedb500be4d52a4b1f8feadfee54337",
  "status": "open",
  "reports": [
    {
      "id": "sha256:d591bc84d8d064ea8d7e2792efd1ff3120584a72293535a4ec3a5a9ad34a15dd",
      "created_at": "2026-10-13T18:11:47.292713+00:00",
      "report": {
        "report_key": "code-review/module.dogfood-scenarios/3",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Prepare can mask scenario errors with worker configuration errors",
        "description": "The prepare command validates worker configuration and model mappings before reading its scenario. Thus scenario validation depends on unrelated local worker setup despite the promise to read the scenario first.\n\nSuggested repair: Read and validate the chosen scenario in the command dispatch before loading or checking worker configuration, while retaining model validation before creating the scenario directory. Test unknown and malformed scenarios with an unavailable worker configuration.",
        "impact": "An unknown or malformed scenario can instead report worker_configuration_unreadable or model_unmapped, concealing the scenario error and violating the documented refusal precedence.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged scripts/e2e/e2e.py:506-517, scripts/e2e/dogfood.py:215-216 against contract.dogfood-scenarios.scenario and reported a violation: The contract says every command reads the scenario first and refuses an unknown name with unknown_scenario. dogfood_command calls worker_configuration and require_mapped at lines 515-516 before dogfood.prepare, which is where scenario(name) is read.",
        "owner_target_id": "module.dogfood-scenarios",
        "evidence": [
          {
            "path": "scripts/e2e/e2e.py",
            "description": "lines 506-517, shown by the violation finding"
          },
          {
            "path": "scripts/e2e/dogfood.py",
            "description": "lines 215-216, shown by the violation finding"
          },
          {
            "path": "specs/concorde/e2e/dogfood/contracts.md",
            "description": "defines contract.dogfood-scenarios.scenario, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.dogfood-scenarios",
        "context_id": "sha256:a98f3d8632fed7f7642337ec3440756d64b8d8aa784dc64e0aab87af29ec61f8",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
