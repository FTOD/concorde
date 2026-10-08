# I-46aa193fee6155de9b9cdbbbe90329fd

```json
{
  "schema_version": 4,
  "id": "I-46aa193fee6155de9b9cdbbbe90329fd",
  "status": "open",
  "reports": [
    {
      "id": "sha256:40aa4a1e03589ff5aff8440acdfe604902bdd8ab1c124e1c7a8c97861567cfc6",
      "created_at": "2026-10-08T08:38:00.171701+00:00",
      "report": {
        "report_key": "code-review/module.scaffold/4",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Scaffold rewrites existing parent prose despite the preservation promise",
        "description": "Scaffold rewrites the parent's initialization paragraph instead of preserving existing prose. The Spec grants no exception for initialization text.\n\nSuggested repair: Remove the replacement of INIT_PARTS and preserve the existing prose when inserting child paragraphs. Add a preservation assertion for a parent containing that exact initialization paragraph.",
        "impact": "Scaffolding changes existing parent prose beyond the promised additions. Because the replacement is global, matching text outside Parts is also rewritten.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/method/scaffold/command.py:69-78, src/concorde/method/scaffold/command.py:328-336 against specs/concorde/method/scaffold/module.md#what-it-writes and reported a violation: The Spec says scaffold adds child paragraphs and 'leaves the existing prose unchanged.' command.py:336 instead executes text.replace(INIT_PARTS, SCAFFOLDED_PARTS, 1) before even locating Parts. The constants replace the existing initialization paragraph with different assertions about the survey and unspecified collaborations.",
        "owner_target_id": "module.scaffold",
        "evidence": [
          {
            "path": "src/concorde/method/scaffold/command.py",
            "description": "lines 69-78, shown by the violation finding"
          },
          {
            "path": "src/concorde/method/scaffold/command.py",
            "description": "lines 328-336, shown by the violation finding"
          },
          {
            "path": "specs/concorde/method/scaffold/module.md",
            "description": "defines specs/concorde/method/scaffold/module.md#what-it-writes, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.scaffold",
        "context_id": "sha256:bc468d6e76da360f307ce29908cc1d9395619b8c276c8f0072da75440f292c49",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
