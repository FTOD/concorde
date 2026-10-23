# I-2dbb980befa354c2833bb7e38caddd7e

```json
{
  "schema_version": 4,
  "id": "I-2dbb980befa354c2833bb7e38caddd7e",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:78ef216c2b7f4a1bbfe224f426e20159e90ac124079ac43132081aa27b9b341e",
      "created_at": "2026-10-13T18:26:54.345385+00:00",
      "report": {
        "report_key": "spec-panel/module.e2e/1",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "Select the canonical record and lock contracts E2E consumes",
        "description": "E2E directly consumes persisted provider records and participates in workspace locking, but selects concept explanations without the canonical definitions needed for those interactions.\n\nSuggested repair: Select the applicable contracts through relies_on or explicit document inclusions: specs/concorde/workflows/contracts.md, specs/concorde/execution/runner.md, specs/concorde/execution/contracts.md, specs/concorde/kernel/contracts.md, specs/concorde/coordination/tasks/contracts.md, and the lock contract in specs/concorde/kernel/tracing/contracts.md. Link each direct reliance to its canonical definition.\n\nOther Modules concerned: module.workflows, module.execution, module.kernel, module.tasks",
        "impact": "An implementer cannot reliably implement the main run and watch paths or the owners case's runner lookup and lock participation from selected context without guessing persisted representations.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/e2e/module.md at uses-workflows, line 859 by the context criterion of the Protocol's Evaluating a Spec; the Specs read: The entry says, “In that record, `run` finds the latest saved result” and “In that record, `watch` finds the steps.” mechanics.md says, “The runner is the process the [run progress file](../glossary.json#concept.run-progress-file)'s `host_pid` names.” The uses declarations select provider concepts but omit the contracts for these records, the workspace binding, the task record and lock participation.\n\nThe panel's chair merged r1.5, r2.1, r3.1 and verified: Verified E2E's declarations and direct record dependencies, and the selected providers' references to exact contracts outside the supplied context. Merged the narrower host_pid and owners-mechanics reports into the broader selection gap. High because main paths depend on these interfaces; preferred-fix because explicitly selecting their canonical definitions repairs the gap without changing behavior.",
        "owner_target_id": "module.e2e",
        "evidence": [
          {
            "path": "specs/concorde/e2e/module.md",
            "description": "uses-workflows, cited by the context finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.e2e",
        "context_id": "sha256:982f7551fa9f6d20906174bc1a98eeaa5c0c1ff11a4ab7be751f9a985dff0432",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task r4-e2e-dist, merged into the primary branch at ad2f6af4d5d883cae87062430b9963cbcfc099b5.",
      "evidence": [
        "merge commit ad2f6af4d5d883cae87062430b9963cbcfc099b5",
        "task r4-e2e-dist"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-23T09:03:02.203314+00:00"
    }
  ]
}
```
