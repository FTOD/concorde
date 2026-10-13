# I-c4dcac9e04f05a6188a5d05ced55fd8a

```json
{
  "schema_version": 4,
  "id": "I-c4dcac9e04f05a6188a5d05ced55fd8a",
  "status": "open",
  "reports": [
    {
      "id": "sha256:838e2330d70ed4ca59fc57cf2a6dfdefb135c1ef2b5bb75d283535e9daaebf90",
      "created_at": "2026-10-13T18:33:26.498367+00:00",
      "report": {
        "report_key": "spec-panel/module.execution/5",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The status explanation conflicts with decision-needing refusals",
        "description": "The status explanation says that needing a decision produces blocked, but workspace_busy needs a decision and produces failed. The broad rule does not distinguish step outcomes from runner refusals.\n\nSuggested repair: Explain that runner refusals before steps produce failed regardless of their reason, while blocked is a status a definition reports. Tell consumers to inspect the error reason for a decision-needing refusal. Align the run-result contract's semantics with this distinction.",
        "impact": "A consumer cannot use the entry's rule to predict status for a decision-needing refusal, and a definition author receives inconsistent guidance on choosing blocked versus failed.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/execution/module.md at concept.run-result, line 105 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: module.md: “When it needs a decision above it, `status` is `blocked`.” The same passage lists “a refusal” under failed outcomes. runner.md's lock row makes workspace_busy failed, and its error table assigns that refusal reason decision. scenario.execution.workspace-busy explicitly expects both failed and decision.\n\nThe panel's chair merged r1.3 and verified: Verified the entry, runner table, error table and scenario. contracts.md repeats the broad blocked definition in the run-result semantics. Medium severity because this concerns a refusal case. Preferred-fix preserves the specific and repeatedly stated workspace_busy behavior while qualifying the broad explanation.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "specs/concorde/execution/module.md",
            "description": "concept.run-result, cited by the obligations finding"
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
