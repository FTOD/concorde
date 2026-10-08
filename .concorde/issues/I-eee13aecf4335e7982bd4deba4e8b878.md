# I-eee13aecf4335e7982bd4deba4e8b878

```json
{
  "schema_version": 4,
  "id": "I-eee13aecf4335e7982bd4deba4e8b878",
  "status": "open",
  "reports": [
    {
      "id": "sha256:9255d6fc12ab388f388c6aea82f72a1c92ebd2be411b3d4ebc347751414c867e",
      "created_at": "2026-10-08T09:01:34.683035+00:00",
      "report": {
        "report_key": "code-review/module.specification/1",
        "tier": "preferred-fix",
        "severity": "critical",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Proposed document creation can escape the Module through symlinks",
        "description": "The proposal boundary is checked lexically, while creation follows filesystem symlinks. For example, a pre-existing `specs/a/details` symlink to another directory lets a proposal for `specs/a/details/rules.md` pass and write into that directory.\n\nSuggested repair: Validate every proposal's reading and metadata paths with the existing safe-path facilities, rejecting symlink components and dangling symlinks before any write. Use creation that cannot follow a link or replace an existing target, and test that one unsafe proposal refuses the entire list.",
        "impact": "A proposal through an existing directory symlink can make the host create files outside the bound Module or worktree. A dangling file symlink can likewise redirect a host write. These writes occur outside the worker audit.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/method/specification/operation.py:298-306, src/concorde/method/specification/operation.py:348-355 against req.specification.created-documents and reported a violation: document_refusal checks lexical ancestry with `folder not in candidate.parents` and existence with `Path.exists()`, but never rejects symlink components. create_documents then uses `reading.parent.mkdir(...)` and `reading.write_text(...)`, which follow symlinks. The requirement permits creation only in the bound Module's entry folder or below it.",
        "owner_target_id": "module.specification",
        "evidence": [
          {
            "path": "src/concorde/method/specification/operation.py",
            "description": "lines 298-306, shown by the violation finding"
          },
          {
            "path": "src/concorde/method/specification/operation.py",
            "description": "lines 348-355, shown by the violation finding"
          },
          {
            "path": "specs/concorde/method/specification/requirements.md",
            "description": "defines req.specification.created-documents, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.specification",
        "context_id": "sha256:6e4668e879e4a1c01d7c787744154d34aa66eebf92b1609332a2c9a7ce9c8e3e",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
