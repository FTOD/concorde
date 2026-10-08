# I-a0acb2fe1daf5420ada0c3f694a1d5f0

```json
{
  "schema_version": 4,
  "id": "I-a0acb2fe1daf5420ada0c3f694a1d5f0",
  "status": "open",
  "reports": [
    {
      "id": "sha256:e3952441872e7dc1579380814081e387185817d56957097c68a6f676ee0aa2d2",
      "created_at": "2026-10-08T04:24:06.400379+00:00",
      "report": {
        "report_key": "code-review/module.views/6",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Scaffold apply accepts an unreadable project configuration",
        "description": "Apply omits the project-initialization check implemented by propose. Proposal validity alone does not establish that the destination project's Spec configuration is readable.\n\nSuggested repair: Apply the same initialization admission before destination handling and transaction creation. Test a valid saved proposal after removing or corrupting the project configuration, asserting invalid and no writes.",
        "impact": "A saved proposal can create a docsite in an uninitialized project, or after the configuration has been removed or corrupted, rather than returning the documented initialization refusal.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged src/concorde/spec/views/docsite_scaffold.py:557-603, src/concorde/spec/views/docsite_scaffold.py:640-647, src/concorde/spec/commands.py:78-93 against specs/concorde/spec-tooling/views/module.md#uses-spec and reported a violation: The Module states: \"When the project's Spec configuration isn't readable, the scaffold returns invalid and asks for initialization.\" apply_docsite checks the package and accepted proposal, then handles destinations and calls apply_files; it never checks the target project's configuration. The command dispatcher calls it directly.",
        "owner_target_id": "module.views",
        "evidence": [
          {
            "path": "src/concorde/spec/views/docsite_scaffold.py",
            "description": "lines 557-603, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/views/docsite_scaffold.py",
            "description": "lines 640-647, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/commands.py",
            "description": "lines 78-93, shown by the violation finding"
          },
          {
            "path": "specs/concorde/spec-tooling/views/module.md",
            "description": "defines specs/concorde/spec-tooling/views/module.md#uses-spec, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.views",
        "context_id": "sha256:694a75b7b53df6199b1e598851e63c9bf43c9da18f3e23215369fca09ba2fa05",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
