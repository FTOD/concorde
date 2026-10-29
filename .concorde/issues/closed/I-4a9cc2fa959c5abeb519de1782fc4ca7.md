# I-4a9cc2fa959c5abeb519de1782fc4ca7

```json
{
  "schema_version": 4,
  "id": "I-4a9cc2fa959c5abeb519de1782fc4ca7",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:c0f7e86ab5202ccc54d65101b7029699e6a7faff1cc162b357bb69a42d374ac5",
      "created_at": "2026-10-13T19:54:27.752580+00:00",
      "report": {
        "report_key": "spec-panel/module.specification/7",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "The no-code rule conflicts with readable bound inclusions",
        "description": "The no-code rule forbids all readable implementation files, including bound inclusions that Spec core intentionally includes in readable Spec context. No exception or refusal policy reconciles those promises.\n\nSuggested repair: Decide whether specify accepts explicitly selected bound inclusions or refuses Modules requiring them. Prefer retaining their read-only Spec-context access while prohibiting ordinary implementation inspection, and align the requirement and entry.\n\nOther Modules concerned: module.spec, module.method",
        "impact": "For a Module with a bound inclusion, the implementer cannot both preserve the prescribed grant and satisfy the blanket prohibition on readable implementation files.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/specification/requirements.md at req.specification.no-code, line 23 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “The specify worker's grant SHALL NOT give read or write access to the contents of any implementation file.” Spec core's Grants section says Spec context contributes bound-inclusion files and makes them `ro` when implementation scope has no level. Its context definition identifies these as files the Module's realizations bind.\n\nThe panel's chair merged r2.2 and verified: Verified the bound-file definition, grant composition and Method's unchanged effective-grant rule. Medium severity concerns Modules with bound inclusions. The repair needs a decision because an exception or refusal policy changes accepted access or inputs.",
        "owner_target_id": "module.specification",
        "evidence": [
          {
            "path": "specs/concorde/method/specification/requirements.md",
            "description": "req.specification.no-code, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.specification",
        "context_id": "sha256:ce0905a0b37eb1808516eaa1c8160029e96d19b43026433e2ec0580cda53e75e",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "project_review r-20261029T060905-project_review-fa4731e2 (commit 8a5ed4245) found it resolved: req.specification.no-code now permits read-only implementation files selected by bound inclusions and links req.spec.bound-inclusion.",
      "evidence": [
        ".concorde/unbound/r-20261029T060905-project_review-fa4731e2/result.json"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-29T08:32:38.501338+00:00"
    }
  ]
}
```
