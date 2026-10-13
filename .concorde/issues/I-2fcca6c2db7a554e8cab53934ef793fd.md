# I-2fcca6c2db7a554e8cab53934ef793fd

```json
{
  "schema_version": 4,
  "id": "I-2fcca6c2db7a554e8cab53934ef793fd",
  "status": "open",
  "reports": [
    {
      "id": "sha256:caeafbecc73ba3183afa3630cc5eb9e985f9d83b2e60facbee97054f87993b26",
      "created_at": "2026-10-13T19:25:05.776391+00:00",
      "report": {
        "report_key": "spec-panel/module.spec/23",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Grant scenarios omit the bound-inclusion exception",
        "description": "Several scenarios prohibit implementation-file reads categorically without excluding files also selected as Spec through bound inclusions.\n\nSuggested repair: Qualify the affected names-only and no-read outcomes with the bound-inclusion exception, or explicitly exclude inclusions from the fixtures. For architecture review, account for inclusions of every registered Module.",
        "impact": "A task could suppress readable bound-inclusion files or reject correct grants, including an architecture review's selected Protocol files.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/spec-tooling/spec/scenarios.md at scenario.spec.grant-specify, line 616 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: grant-specify says “BUT no implementation file is `ro` or `rw`”; grant-project-implementation promises “no read access to A's own code”; grant-review-architecture says “BUT no implementation file is `ro`”. The bound-inclusion scenario explicitly grants src/a/one.py ro, and ProjectSpecification includes every Module's bound inclusions.\n\nThe panel's chair merged r3.3 and verified: Verified the affected scenarios against the bound-inclusion scenario and highest-level contract. Medium because the conflict is conditional on inclusions; preferred-fix because the inclusion rule clearly supplies the exception.",
        "owner_target_id": "module.spec",
        "evidence": [
          {
            "path": "specs/concorde/spec-tooling/spec/scenarios.md",
            "description": "scenario.spec.grant-specify, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec",
        "context_id": "sha256:9a8205f3d9b7372077a103ac4774b7e0aa10ec031c1fc770920c798b246c0ad7",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
