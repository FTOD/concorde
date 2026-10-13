# I-ad057bfd92f65b8e80ebe6aa37ea2ba2

```json
{
  "schema_version": 4,
  "id": "I-ad057bfd92f65b8e80ebe6aa37ea2ba2",
  "status": "open",
  "reports": [
    {
      "id": "sha256:bb97f94bca4437343b9feed181e5261b6d7e6c8d17ed837f578db019a3096226",
      "created_at": "2026-10-13T18:33:27.712791+00:00",
      "report": {
        "report_key": "spec-panel/module.execution/8",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Align the cleanup explanation with permitted checkout leftovers",
        "description": "The entry guarantees successful cleanup for every ending, while the requirements and detailed runner behavior allow retained checkout files. The runner's unconditional checkout-refusal statement repeats the overpromise.\n\nSuggested repair: Describe cleanup as an attempt before result publication. Explain that checkout-not-removed evidence names leftovers without changing status, and that an uncontrollably killed runner can leave a checkout requiring manual removal. Qualify the corresponding unconditional cleanup wording in runner.md and the lifecycle overview.",
        "impact": "A consumer can treat a completed or successful result as proof that no checkout remains, overlooking evidence and required manual cleanup.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/execution/module.md at concept.unbound-checkout, line 404 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “However the run ends, the runner removes the checkout before it writes the result.” req.execution.checkout-removed instead requires an “attempt to remove”; checkout-leftovers-named permits leftovers whose evidence “never changes the result's status.” runner.md also says “Nothing is left behind” after checkout refusal, despite its step 5 describing failed direct removal and SIGKILL leftovers.\n\nThe panel's chair merged r2.3, r3.2 and verified: Verified both cleanup reports against the removal requirements and runner step 5. Medium severity because cleanup failure is an edge case. Preferred-fix aligns the broad explanation with the detailed existing failure policy, without strengthening cleanup guarantees.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "specs/concorde/execution/module.md",
            "description": "concept.unbound-checkout, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.execution",
        "context_id": "sha256:eac005ae890bae382c4be39198d3d1a92864fb525e8d3f82926e09efcac17959",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
