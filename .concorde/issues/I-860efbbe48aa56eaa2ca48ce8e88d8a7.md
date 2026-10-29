# I-860efbbe48aa56eaa2ca48ce8e88d8a7

```json
{
  "schema_version": 4,
  "id": "I-860efbbe48aa56eaa2ca48ce8e88d8a7",
  "status": "open",
  "reports": [
    {
      "id": "sha256:097e2c885153f884c164c327df2d9860933f7ec33e019dc61bd7c291ea273bb0",
      "created_at": "2026-10-29T08:08:07.969370+00:00",
      "report": {
        "report_key": "code-review/module.tracing/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Listing silently omits top nodes whose trace record is missing",
        "description": "listing filters out every top folder without an accessible trace.json before calling view. The reading contract requires a listed top node with a missing or unreadable record to appear as unreadable, with its children still contributing usage.\n\nSuggested repair: Pass top-node folders through view(requested=False) even when their record is missing. Add a regression with a missing top record and a readable child, checking the unreadable reason and rolled-up usage.",
        "impact": "A failed initial trace write can make an entire task or run disappear from list, hiding its readable descendants and their consumption.",
        "basis": "project_review run r-20261029T060905-project_review-fa4731e2 (module review) judged src/concorde/kernel/tracing/reader.py:505-515 against contract.tracing.view and reported a violation: The admission condition is `if (item / layout.TRACE).is_file() and real not in seen:`. The view contract explicitly includes top nodes list lists whose trace.json cannot be read, and Reading traces explicitly includes missing records.",
        "owner_target_id": "module.tracing",
        "evidence": [
          {
            "path": "src/concorde/kernel/tracing/reader.py",
            "description": "lines 505-515, shown by the violation finding"
          },
          {
            "path": "specs/concorde/kernel/tracing/contracts.md",
            "description": "defines contract.tracing.view, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261029T060905-project_review-fa4731e2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.tracing",
        "context_id": "sha256:56f5b2adc4968dd42a02fa9e69721e238b5f021cdf8e95b8ca8ef551092d8489",
        "change_id": null,
        "head": "8a5ed4245ef73b623587ddac67b1b88c13c178b2",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
