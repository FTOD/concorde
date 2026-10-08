# I-479e61fbc7d05efe8ef7c9e29ade068b

```json
{
  "schema_version": 4,
  "id": "I-479e61fbc7d05efe8ef7c9e29ade068b",
  "status": "open",
  "reports": [
    {
      "id": "sha256:c1fbb922875d07f74e9c8cb8b093c67f8052ca551da97511cde386e757acb340",
      "created_at": "2026-10-08T03:14:39.365858+00:00",
      "report": {
        "report_key": "code-review/module.checks/1",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Symlink replacements of measured files escape stale-evidence detection",
        "description": "Implementation files and selected test files are hashed through symbolic links. A file replaced during a check by a symlink to identical contents is accepted as unchanged.\n\nSuggested repair: Validate measured implementation and selected-test paths as regular files without symbolic links before hashing, and convert post-run validation failures to stale_evidence. Add regression cases for replacement with a symlink to identical bytes.",
        "impact": "The service can return passing evidence after a measured implementation or test file became a symbolic link, despite the promised stale_evidence refusal.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged src/concorde/execution/checks/checks.py:145-146, src/concorde/execution/checks/checks.py:372, src/concorde/execution/checks/checks.py:453 against req.checks.measured-input-unchanged and reported a violation: service.md step 7 explicitly includes a measured file or selected test file that 'became a symbolic link'. _file_digest uses path.read_bytes() without checking for a symbolic link; both check_revision's implementation measurement and measured_digest's selected-test measurement call it. Replacing either file with a symlink to identical bytes therefore preserves the digest.",
        "owner_target_id": "module.checks",
        "evidence": [
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "lines 145-146, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "line 372, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "line 453, shown by the violation finding"
          },
          {
            "path": "specs/concorde/execution/checks/service.md",
            "description": "defines req.checks.measured-input-unchanged, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.checks",
        "context_id": "sha256:5a17522a86bb9ffcdc0ba49bb41bee402dad2d56750770eed6f551167cc67df5",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
