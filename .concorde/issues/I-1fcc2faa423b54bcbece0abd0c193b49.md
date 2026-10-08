# I-1fcc2faa423b54bcbece0abd0c193b49

```json
{
  "schema_version": 4,
  "id": "I-1fcc2faa423b54bcbece0abd0c193b49",
  "status": "open",
  "reports": [
    {
      "id": "sha256:7e75c4dd51cc479ee19725f2a3ae96a43adf6d55dbc01f135160e43d98f9bc0f",
      "created_at": "2026-10-08T07:14:12.235510+00:00",
      "report": {
        "report_key": "code-review/module.adoption/4",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "Deleted verifies bindings are still treated as usable",
        "description": "A prior approved verifies definition is considered usable even when an intervening deletion removes it. The linker does not account for deletion when checking whether the inserted decorator can resolve its name.\n\nSuggested repair: Include deletion in the decorator binding analysis and conservatively report links whose binding may have been removed before use. Add a test with an approved helper followed by del verifies and an otherwise valid test function.",
        "impact": "Adoption can turn a working test module into one that fails during import and report the link as successful.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/method/adoption/test_links.py:102-118, src/concorde/method/adoption/test_links.py:206-216, src/concorde/method/adoption/test_links.py:327-345 against specs/concorde/method/adoption/module.md#realization.adoption.code-to-spec and reported a defect: _bound_names() recognizes ast.Store but not ast.Del. _usable_before() accepts any allowed helper/import whose end line precedes the test. Consequently, a file with the no-op helper, then 'del verifies', then an undecorated test passes both checks and receives @verifies even though the name has been deleted. Parsing the resulting source succeeds, but importing it raises NameError. The Spec promises unchanged test execution.",
        "owner_target_id": "module.adoption",
        "evidence": [
          {
            "path": "src/concorde/method/adoption/test_links.py",
            "description": "lines 102-118, shown by the defect finding"
          },
          {
            "path": "src/concorde/method/adoption/test_links.py",
            "description": "lines 206-216, shown by the defect finding"
          },
          {
            "path": "src/concorde/method/adoption/test_links.py",
            "description": "lines 327-345, shown by the defect finding"
          },
          {
            "path": "specs/concorde/method/adoption/module.md",
            "description": "defines specs/concorde/method/adoption/module.md#realization.adoption.code-to-spec, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.adoption",
        "context_id": "sha256:2f179174326ccd8ed2c6a39f70f20983346f3cd314470930b75aa861ee71cf43",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
