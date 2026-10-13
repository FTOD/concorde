# I-9b51f7daab885aa895bbd64edb00de18

```json
{
  "schema_version": 4,
  "id": "I-9b51f7daab885aa895bbd64edb00de18",
  "status": "open",
  "reports": [
    {
      "id": "sha256:7a03b5457ffd369fd2a99117c1e74758c881403be094a2d609abd2f0098f5137",
      "created_at": "2026-10-13T17:45:56.090892+00:00",
      "report": {
        "report_key": "spec-panel/module.code-review/10",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Reviewer completeness obligations lack decidable acceptance criteria",
        "description": "These requirements depend on what the reviewer could establish or privately judges, without an observable criterion for deciding compliance. The Specs do not distinguish an instruction obligation from a guaranteed result.\n\nSuggested repair: Decide whether these are obligations to provide reviewer instructions or guarantees about review results. If they are instruction obligations, name the Operation's duty to supply those instructions and retain reviewer behavior as explanatory guidance. If they are result guarantees, define observable compliance criteria.",
        "impact": "A task cannot determine from observable results whether the reviewer withheld another finding it could establish or privately judged a promise unrealizable. It cannot use these as decidable acceptance criteria for the Operation.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/code-review/requirements.md at req.code-review.one-pass, line 52 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “A reviewer SHALL report every blocking finding it can establish in a single run.” Also: “A reviewer that judges a requirement, scenario or contract ... unreasonable or unrealizable SHALL report it” as a Spec challenge. The entry says the Operation verifies citations and verdicts but otherwise keeps findings as reviewer claims.\n\nThe panel's chair merged r1.5 and verified: Verified the two statements and the explicit limits of host verification. The concern is their unobservable completeness and judgment predicates, not a blanket prohibition on requirements for workers. Medium severity reflects acceptance ambiguity. Decision-needed replaces preferred-fix because assigning the duty to instructions instead of the reviewer changes the bearer and strength of the promise.",
        "owner_target_id": "module.code-review",
        "evidence": [
          {
            "path": "specs/concorde/method/code-review/requirements.md",
            "description": "req.code-review.one-pass, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.code-review",
        "context_id": "sha256:7eb19425e1277ec68204b38a48ae66ee807ec2b29bc9c5d0af8470432224d3d3",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
