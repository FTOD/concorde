# I-c7a493ac83ee5bdab70d10b3faf02e14

```json
{
  "schema_version": 4,
  "id": "I-c7a493ac83ee5bdab70d10b3faf02e14",
  "status": "open",
  "reports": [
    {
      "id": "sha256:c87832b302db33e6a7a20d1cbc7bb21b2ab7a490eae133645bfcc86a224c2248",
      "created_at": "2026-10-13T18:50:33.630753+00:00",
      "report": {
        "report_key": "spec-panel/module.implementation/5",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Code-change output has no policy for an unavailable audit",
        "description": "The code-change contract promises observed net file changes even when the audit supplying those observations is unavailable. No output policy or recovery rule covers this retained-result case.\n\nSuggested repair: Decide whether audit_unavailable withholds the code change while retaining worker claims and error evidence, or produces an explicitly incomplete representation. Align the output-presence rule and contract, and add a scenario.\n\nOther Modules concerned: module.workers",
        "impact": "An implementer must either omit a promised output, emit incomplete file lists as complete, or invent an unspecified measurement recovery procedure.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/implementation/contracts.md at contract.implementation.code-change, line 46 by the design criterion of the Protocol's Evaluating a Spec; the Specs read: The contract requires file lists describing \"the net change from the workspace before the run to the workspace the run left\". The entry promises a code change whenever a valid worker result exists. Workers' launch.md, Audit, says an unavailable audit is null, ends the run with audit_unavailable, and still retains a valid worker result.\n\nThe panel's chair merged r2.3 and verified: Verified the output-presence rule, net-change semantics and Workers' unavailable-audit behavior. Medium severity for an exceptional measurement failure. Decision-needed because withholding output or introducing unknown/incomplete file lists changes the public promise.",
        "owner_target_id": "module.implementation",
        "evidence": [
          {
            "path": "specs/concorde/method/implementation/contracts.md",
            "description": "contract.implementation.code-change, cited by the design finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.implementation",
        "context_id": "sha256:f270a0ecf7862e867dc819dff226842f8fef9ea1fe8cebbe8265d58d9523719b",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
