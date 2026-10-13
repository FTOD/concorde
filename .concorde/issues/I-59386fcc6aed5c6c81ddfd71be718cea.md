# I-59386fcc6aed5c6c81ddfd71be718cea

```json
{
  "schema_version": 4,
  "id": "I-59386fcc6aed5c6c81ddfd71be718cea",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9eb157e5d3592c6d9f605d037c6d3cf6432560a316e1285127fa9df10046a304",
      "created_at": "2026-10-13T17:32:23.124210+00:00",
      "report": {
        "report_key": "spec-panel/module.adoption/3",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Disambiguate answer identities across admitted runs",
        "description": "Answers address run-local identities while a later run may admit several source runs. Neither the answer contract nor its validation rules define how conflicting identities across those runs are disambiguated.\n\nSuggested repair: Define answer provenance across inputs. Either qualify an answer by its originating run or reject conflicting occurrences of an answered identity. Explain how repeated occurrences of the same question across reruns are recognized, and add collision and repeated-question scenarios.\n\nOther Modules concerned: module.workflows",
        "impact": "Two admitted runs can reuse q.payment-retry for different questions or Modules. A caller cannot qualify the intended source, and the host has no stated rule for rejecting or resolving the collision.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/adoption/contracts.md at contract.adoption.answers, line 1573 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The answers contract permits only `id`, `question`, `answer` and `answered_by`, and says “id names the decision or question” and “question repeats its text so the file is readable on its own.” The entry permits repeated `--input` arguments. contract.workflows.step-output describes decision-point identities as “unique within the run.”\n\nThe panel's chair merged r2.3, r3.2 and verified: Verified the complete answers contract, input syntax, answers-first requirement and Workflows' identity scope. Medium severity for multiple-input collisions; decision-needed because source qualification or rejection policy changes the interface.",
        "owner_target_id": "module.adoption",
        "evidence": [
          {
            "path": "specs/concorde/method/adoption/contracts.md",
            "description": "contract.adoption.answers, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.adoption",
        "context_id": "sha256:9f91a9083aa5a25dd5b8613c94f830f11513195394a5776d0abf8187e3c2ae1b",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
