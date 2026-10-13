# I-bb2680af0cab57bb9dbaa34c4ed78159

```json
{
  "schema_version": 4,
  "id": "I-bb2680af0cab57bb9dbaa34c4ed78159",
  "status": "open",
  "reports": [
    {
      "id": "sha256:fa26ff76fea4e7fa86be85fb66d10720379eac0166d80b21719793d90c277a6a",
      "created_at": "2026-10-13T20:24:41.801892+00:00",
      "report": {
        "report_key": "spec-panel/module.views/10",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The d2 override lacks an input and failure contract",
        "description": "CONCORDE_D2 is listed as an input without defining its kind, accepted value or behavior when set but unusable.\n\nSuggested repair: Define CONCORDE_D2 as the intended environment input and specify its value format, path resolution and unusable-value behavior. State that the installed fallback is resolved from the project root.",
        "impact": "Users cannot configure the override confidently, and implementers must choose executable-path interpretation and whether an invalid override fails or falls through.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/spec-tooling/views/requirements.md at req.views.d2-program, line 112 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The ordered lookup sources are “From `CONCORDE_D2`,” “Else from `.concorde/tools/d2`,” and “Else from `PATH`.” The scenario says a set CONCORDE_D2 is used, without defining its value or unusable-value handling.\n\nThe panel's chair merged r1.4 and verified: Checked the entry, requirement, contracts and d2 scenarios. Medium because the ordinary installed path is explained but override behavior is not. Decision-needed, rather than the proposed preferred-fix, because the invalid-override policy is not determined by the Specs.",
        "owner_target_id": "module.views",
        "evidence": [
          {
            "path": "specs/concorde/spec-tooling/views/requirements.md",
            "description": "req.views.d2-program, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.views",
        "context_id": "sha256:01a9df9628d7d7a1f6b71425e7ea1c59f4d7ac51d895d9e83cec9f58727bcbcc",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
