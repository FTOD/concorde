# I-88e8ba4c962e51db9b8dfa9fdbd52e61

```json
{
  "schema_version": 3,
  "id": "I-88e8ba4c962e51db9b8dfa9fdbd52e61",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:396fec6b7def9f2375e073b9aa8d39eec2019f7cc7b19990658f3158d0b38603",
      "created_at": "2026-10-01T06:13:09.349697+00:00",
      "report": {
        "report_key": "module.workers/7",
        "tier": "decision-needed",
        "type": "bug",
        "subtype": null,
        "title": "Whole-configuration map checking has no defined invocation policy",
        "description": "The scenario introduces whole-configuration map validation without specifying its entry point, invocation policy or error code.\n\nSuggested repair: Decide whether this is launch-time validation or a separate check, then define its caller, timing, aggregate refusal code and result. If no such behavior is intended, remove the scenario.\n\nOther Modules concerned: module.operations",
        "impact": "An implementer must invent when the aggregate map check runs, how it is invoked and which refusal it returns.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/execution/workers/scenarios.md at scenario.workers.model-map-checked, line 447 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"WHEN the whole configuration is checked against the map\" and \"THEN one refusal names every model and backend the map lacks, with the workers that would take them\". The entry describes resolving the map for the requested worker and whole-configuration validation of structure, catalog names, limits and reasoning vocabulary.\n\nThe panel's chair merged r1.2 and verified: Verified the aggregate scenario against the entry, contracts and Operations' worker sequence. Choosing whether this check gates launches or is a separate operation changes observable admission behavior.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/execution/workers/scenarios.md",
            "description": "scenario.workers.model-map-checked, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:d9d26b9c3b118a1ec71a8cb21310fcb039173ad3cfece95db1c14e2faee0ef23",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    },
    {
      "id": "sha256:6147fc15fd53d9612b7ee57686424f557033aafe40d2f5e7284101eb38037f0e",
      "created_at": "2026-10-01T14:48:03.144879+00:00",
      "report": {
        "report_key": "module.workers/7--severity",
        "tier": "decision-needed",
        "type": "bug",
        "subtype": null,
        "title": "Whole-configuration map checking has no defined invocation policy",
        "description": "The scenario introduces whole-configuration map validation without specifying its entry point, invocation policy or error code.\n\nSuggested repair: Decide whether this is launch-time validation or a separate check, then define its caller, timing, aggregate refusal code and result. If no such behavior is intended, remove the scenario.\n\nOther Modules concerned: module.operations",
        "impact": "An implementer must invent when the aggregate map check runs, how it is invoked and which refusal it returns.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/execution/workers/scenarios.md at scenario.workers.model-map-checked, line 447 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"WHEN the whole configuration is checked against the map\" and \"THEN one refusal names every model and backend the map lacks, with the workers that would take them\". The entry describes resolving the map for the requested worker and whole-configuration validation of structure, catalog names, limits and reasoning vocabulary.\n\nThe panel's chair merged r1.2 and verified: Verified the aggregate scenario against the entry, contracts and Operations' worker sequence. Choosing whether this check gates launches or is a separate operation changes observable admission behavior. Severity medium assessed by the main agent on 2026-10-01: Implementers must invent when and how the whole-configuration map check runs and what it refuses with.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "specs/concorde/execution/workers/scenarios.md",
            "description": "scenario.workers.model-map-checked, cited by the obligations finding"
          }
        ],
        "severity": "medium",
        "issue_id": "I-88e8ba4c962e51db9b8dfa9fdbd52e61",
        "expected_revision": "sha256:e8006fa36e209f719a926c3894b2a90d9661dc0d24abc7e135fe81ca3dfbbb9f"
      },
      "source": {
        "invocation_id": "cli-2b67c4ef-b986-40f3-aa3f-0d390d8b9d9c",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:faf611ab5bdd47f3ab93968932072ec605e527fb468e96a4f6c20a419e8f0f8c",
        "change_id": null,
        "head": "2b45ea76e4576f85aa05b911937d874314daa7c8"
      }
    },
    {
      "id": "sha256:cb9cc104688a0eb35e0b6fed305ca5f4b8140382eb01b1b93476e780e3f73714",
      "created_at": "2026-10-02T02:30:30.083068+00:00",
      "report": {
        "report_key": "fix-e2e/workers-whole-check-caller",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Whole-configuration map checking has no defined invocation policy",
        "description": "A caller of the whole-configuration check exists: End-to-end testing's `prepare` (scripts/e2e/e2e.py `require_mapped`) calls `concorde.harness.models.check_mapped` on the worker configuration it builds for a test project before anything is cloned, and passes its refusal on with its code. module.e2e now declares this reliance as `uses module.workers` with `relies_on` `scenario.workers.model-map-checked`, and names the codes `config_invalid`, `model_map_missing`, `model_map_invalid` and `model_unmapped`. Whatever this Issue decides should keep a callable check of a whole configuration, or tell End-to-end testing what replaces it.",
        "impact": "Removing the scenario or the function, as one repair option suggests, would leave E2E's preparation without the promise it relies on.",
        "basis": "Read at fix-e2e (base 84994940): scripts/e2e/e2e.py `require_mapped` calls `models.check_mapped`; src/concorde/harness/models.py `check_mapped` validates the configuration and resolves every worker of every Operation through the map, raising `model_unmapped` with every missing entry; specs/concorde/e2e/module.md (Preparing a test project, Around it) now relies on scenario.workers.model-map-checked.",
        "owner_target_id": "module.workers",
        "evidence": [
          {
            "path": "scripts/e2e/e2e.py",
            "description": "require_mapped, the caller"
          },
          {
            "path": "src/concorde/harness/models.py",
            "description": "check_mapped, the whole-configuration check"
          }
        ],
        "issue_id": "I-88e8ba4c962e51db9b8dfa9fdbd52e61",
        "expected_revision": "sha256:a377f23be5f353273c900e18969e33314c5ba12ac37e764545f70efc1df9e497"
      },
      "source": {
        "invocation_id": "cli-15a88396-3762-431a-bf85-bb4b213692a0",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.workers",
        "context_id": "sha256:dfb4f137a9680b00f2a784cd5cd2ac8ab37e1dbe2996939b1f308ef5168552c3",
        "change_id": "fix-e2e",
        "head": "ed5d82660960b9945565f41382ff2ea7aaa29103"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-workers, merged into the primary branch at d52e5de3abbc2d5a4e3fa5675741d4078a152185.",
      "evidence": [
        "merge commit d52e5de3abbc2d5a4e3fa5675741d4078a152185",
        "task fix-workers"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-02T02:43:08.381079+00:00"
    }
  ]
}
```
