# I-e4a54ecb42e554af9d41cffadba2bc35

```json
{
  "schema_version": 4,
  "id": "I-e4a54ecb42e554af9d41cffadba2bc35",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:be186b17c5574d89dbd971008615a5c49a5ac36c933fd6e6aaa0298fcf6e7f41",
      "created_at": "2026-10-13T19:57:00.722340+00:00",
      "report": {
        "report_key": "code-review/module.task-session/2",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Id-less assistant records can be incorrectly deduplicated",
        "description": "Records without a message ID are deduplicated by record UUID, although the contract requires each such record to count separately. The fallback keys also share the namespace of real message IDs.\n\nSuggested repair: Use separate tagged keys for real message IDs and id-less records; give each id-less record a unique key based on its full source path and record position. Test repeated record UUIDs without message IDs alongside ordinary message-ID deduplication.",
        "impact": "The finished trace can undercount messages and tokens for a transcript containing repeated UUIDs on records without message IDs. Those incorrect figures remain after transcript retention.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/coordination/tasks/session.py:661-662 against contract.task-session.session-trace and reported a violation: The contract says 'an assistant record whose message has no id counts as a message of its own'. Lines 661-662 instead use the key message.get('id') or f\"{path.name}:{record.get('uuid') or number}\" and assign into a dictionary. Two id-less records with the same record uuid therefore overwrite one another.",
        "owner_target_id": "module.task-session",
        "evidence": [
          {
            "path": "src/concorde/coordination/tasks/session.py",
            "description": "lines 661-662, shown by the violation finding"
          },
          {
            "path": "specs/concorde/coordination/task-session/contracts.md",
            "description": "defines contract.task-session.session-trace, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.task-session",
        "context_id": "sha256:7f597ae0a2df2b7b10d6f0d7a9874c2693d554ab0bb52f17b9454a308822c491",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task coordination-high, merged into the primary branch at 01c7734fd8aa4314762640e88c9f462c72307e0a.",
      "evidence": [
        "merge commit 01c7734fd8aa4314762640e88c9f462c72307e0a",
        "task coordination-high"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-29T09:23:04.783060+00:00"
    }
  ]
}
```
