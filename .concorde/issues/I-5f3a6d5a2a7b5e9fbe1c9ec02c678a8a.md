# I-5f3a6d5a2a7b5e9fbe1c9ec02c678a8a

```json
{
  "schema_version": 4,
  "id": "I-5f3a6d5a2a7b5e9fbe1c9ec02c678a8a",
  "status": "open",
  "reports": [
    {
      "id": "sha256:385e7f05d7d20581144ae4828db0c9aba4579c22e70bbaa4c410ddbe32b70b40",
      "created_at": "2026-10-13T18:11:48.120325+00:00",
      "report": {
        "report_key": "code-review/module.dogfood-scenarios/5",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Quoted worktree paths cause false workaround findings",
        "description": "The no-workaround check misreads Git-quoted worktree paths. It attempts to read a path containing the quoting syntax instead of the actual worktree path and consequently treats the expected file as absent.\n\nSuggested repair: Request NUL-delimited worktree porcelain output with -z and parse its fields without line splitting or quoting ambiguity. Test an unchanged worktree with a tab or newline in its directory name, then a changed file in that same worktree.",
        "impact": "An unchanged project in a worktree whose path contains a tab or newline is falsely reported as having a workaround, and the actual worktree files are not inspected.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged scripts/e2e/dogfood.py:447-453, scripts/e2e/dogfood.py:464-472 against scenario.dogfood-scenarios.no-workaround and reported a defect: unchanged invokes `git worktree list --porcelain` without -z, splits lines, and treats the substring after `worktree ` as a literal filesystem path. Git's non-NUL porcelain format quotes and escapes unusual worktree paths; the code performs no decoding before `Path(tree) / path`.",
        "owner_target_id": "module.dogfood-scenarios",
        "evidence": [
          {
            "path": "scripts/e2e/dogfood.py",
            "description": "lines 447-453, shown by the defect finding"
          },
          {
            "path": "scripts/e2e/dogfood.py",
            "description": "lines 464-472, shown by the defect finding"
          },
          {
            "path": "specs/concorde/e2e/dogfood/scenarios.md",
            "description": "defines scenario.dogfood-scenarios.no-workaround, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.dogfood-scenarios",
        "context_id": "sha256:a98f3d8632fed7f7642337ec3440756d64b8d8aa784dc64e0aab87af29ec61f8",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
