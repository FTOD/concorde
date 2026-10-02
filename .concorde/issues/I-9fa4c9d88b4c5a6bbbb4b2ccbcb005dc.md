# I-9fa4c9d88b4c5a6bbbb4b2ccbcb005dc

```json
{
  "schema_version": 4,
  "id": "I-9fa4c9d88b4c5a6bbbb4b2ccbcb005dc",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:4867fca4573bd8d4bb84eb7d2fd5920067fbcb5cf54bc9236c339537e4b653f5",
      "created_at": "2026-10-01T17:14:38.572338+00:00",
      "report": {
        "report_key": "fix-main-session/task-brief/module.concorde",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Link the task brief where the root Module names it",
        "description": "The root entry says the main agent \"records its brief in the\" decision log and its diagram reads \"Record the brief, start a task session\", without linking the glossary's Task brief (concept.task-brief, owned by module.main-session), while the glossary's Brief (concept.brief) means the prompt an Operation generates for one worker. Line 122's \"the brief with the task and its constraints\" (Protocol task material) is a third sense worth checking at the same time.\n\nSuggested repair: link the task handoff as [task brief](glossary.json#concept.task-brief) at its first use and say \"task brief\" in the diagram label.",
        "impact": "A reader can take the task's handoff for a worker's Brief.",
        "basis": "Main session named the task handoff Task brief to resolve I-5e92991bb60258a48b3290526e2e5396 (task fix-main-session). specs/concorde/module.md line 197 says \"records its brief in the\" decision log and line 215 \"Record the brief\".",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/module.md",
            "description": "lines 197 and 215 use \"brief\" for the task's handoff without a term link"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-08b38129-4b13-4c21-85fc-bc4a34eae4b6",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.concorde",
        "context_id": "sha256:97937d61c7a771227088ca2d122c54413bec7083eebc4bacb7c996b99320d7a0",
        "change_id": "fix-main-session",
        "head": "6f72e88820339bd632240a53b699e5c168da14d0"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-execution-root, merged into the primary branch at 9ebd93d8898fce86bc0fc951e88580b22a491226.",
      "evidence": [
        "merge commit 9ebd93d8898fce86bc0fc951e88580b22a491226",
        "task fix-execution-root"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-02T02:47:21.244391+00:00"
    }
  ]
}
```
