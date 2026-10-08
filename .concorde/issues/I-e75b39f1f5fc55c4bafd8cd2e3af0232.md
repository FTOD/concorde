# I-e75b39f1f5fc55c4bafd8cd2e3af0232

```json
{
  "schema_version": 4,
  "id": "I-e75b39f1f5fc55c4bafd8cd2e3af0232",
  "status": "open",
  "reports": [
    {
      "id": "sha256:6345a31673833fa320d73b1295ac303f660227b116ddf173cd074c56ed04e225",
      "created_at": "2026-10-08T03:28:16.134881+00:00",
      "report": {
        "report_key": "code-review/module.e2e/1",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Project names can escape the E2E root",
        "description": "The developer-provided project name is treated as an unrestricted path. Validating the root alone does not keep the resulting project under that root.\n\nSuggested repair: Require the project name to be one directory component and check the resolved project destination is directly under the resolved root before creating anything. Add coverage for parent traversal and symlinked destinations.",
        "impact": "Preparation can create a repository outside the designated throwaway root, including under the checkout where sessions inherit Concorde's development instructions.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged scripts/e2e/common.py:67-69, scripts/e2e/e2e.py:184-193 against concept.test-project and reported a violation: The Spec places each project at `test-<name>` under the end-to-end root and excludes projects inside this checkout. `test_directory` simply returns `root / f\"{TEST_PREFIX}{name}\"`; `prepare` checks only whether that path exists before cloning. A name such as `x/../../elsewhere/new-project` escapes the root, and enough parent components can target a new directory inside the checkout despite e2e_root accepting the external root.",
        "owner_target_id": "module.e2e",
        "evidence": [
          {
            "path": "scripts/e2e/common.py",
            "description": "lines 67-69, shown by the violation finding"
          },
          {
            "path": "scripts/e2e/e2e.py",
            "description": "lines 184-193, shown by the violation finding"
          },
          {
            "path": "specs/concorde/e2e/module.md",
            "description": "defines concept.test-project, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.e2e",
        "context_id": "sha256:ec4d827650a5bbe4f9df87290753474cb70570866332ad2a91b7cf17b35822b5",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
