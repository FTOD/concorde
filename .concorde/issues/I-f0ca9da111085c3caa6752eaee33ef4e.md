# I-f0ca9da111085c3caa6752eaee33ef4e

```json
{
  "schema_version": 4,
  "id": "I-f0ca9da111085c3caa6752eaee33ef4e",
  "status": "open",
  "reports": [
    {
      "id": "sha256:44e124e1f3ae30eaec6d0d5c2ffad2bf0bb21d11a0f8070e5dc2692677c8052b",
      "created_at": "2026-10-29T07:43:46.095604+00:00",
      "report": {
        "report_key": "spec-panel/module.spec/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Existing-file binding omits the contract's submodule exclusion",
        "description": "The requirement excludes document members, control records and generated outputs, but the initialization contract also excludes paths inside submodules. The two scopes of the existing-files realization differ.\n\nSuggested repair: Align the requirement's exceptions with the initialization contract, explicitly including paths inside submodules and build outputs.",
        "impact": "An implementer or test author encounters incompatible binding expectations for a project with submodules.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 judged specs/concorde/spec-tooling/spec/requirements.md at req.spec.init-binds-existing-files by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The requirement says “bind every existing project file” apart from “Document members. Control records. Generated outputs.” The contract's exception list also includes “Paths inside submodules.”\n\nThe panel's chair merged r1.2 and verified: Verified both exception lists. This affects an edge case, so medium. Preferred-fix rather than obvious-fix because alignment requires choosing the canonical scope, with the contract providing the clearest existing policy.",
        "owner_target_id": "module.spec",
        "evidence": [
          {
            "path": "specs/concorde/spec-tooling/spec/requirements.md",
            "description": "req.spec.init-binds-existing-files, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec",
        "context_id": "sha256:b2be97d90e5fb191176eb5703bae2c0912d3a81f8be62219ab72593bad605446",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
