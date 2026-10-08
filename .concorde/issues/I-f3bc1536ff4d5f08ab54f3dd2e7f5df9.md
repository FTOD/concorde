# I-f3bc1536ff4d5f08ab54f3dd2e7f5df9

```json
{
  "schema_version": 4,
  "id": "I-f3bc1536ff4d5f08ab54f3dd2e7f5df9",
  "status": "open",
  "reports": [
    {
      "id": "sha256:1930ca7f408f94f4b60ac2379641c7f206234bc6d22f1e64dbb35f3e7bc67df4",
      "created_at": "2026-10-08T08:37:59.630084+00:00",
      "report": {
        "report_key": "code-review/module.scaffold/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Parts insertion ignores Markdown heading and fence syntax",
        "description": "The parent-section insertion logic treats raw heading-like lines as Markdown sections. It misidentifies existing Parts sections such as '## Parts {#parts}' and section boundaries inside fenced examples.\n\nSuggested repair: Use Spec core's Markdown section parsing to locate the real Parts section and its end while preserving the original text. Add cases for an explicitly anchored Parts heading and a fenced example containing '## Example' within Parts.",
        "impact": "A valid parent with an anchored Parts heading can acquire a duplicate section. A fenced example containing a level-two heading can receive the generated paragraphs inside its code block, causing missing relation meanings and rollback with scaffold_invalid.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged src/concorde/method/scaffold/command.py:337-355, src/concorde/spec/syntax.py:103-129 against req.scaffold.contained and reported a violation: parent_reading finds Parts only with line.strip() == '## Parts' and ends it at the next raw line starting '## '. It does not distinguish fenced example text from headings or recognize heading anchors. The Spec requires child paragraphs at the end of the parent's Parts section and a new section only when none exists. Spec core's syntax.py:103-111 recognizes prose headings and strips their explicit anchors.",
        "owner_target_id": "module.scaffold",
        "evidence": [
          {
            "path": "src/concorde/method/scaffold/command.py",
            "description": "lines 337-355, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/syntax.py",
            "description": "lines 103-129, shown by the violation finding"
          },
          {
            "path": "specs/concorde/method/scaffold/requirements.md",
            "description": "defines req.scaffold.contained, the finding's basis"
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
