# I-acce1f97db8b5d7fae6b388c8f277cbd

```json
{
  "schema_version": 4,
  "id": "I-acce1f97db8b5d7fae6b388c8f277cbd",
  "status": "open",
  "reports": [
    {
      "id": "sha256:948a80eb68770ad9cbefc4d6be433fb53a3a8e69245c7a060ad49c3236852106",
      "created_at": "2026-10-08T08:13:55.115806+00:00",
      "report": {
        "report_key": "code-review/module.issues/7",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Task-session guidance incorrectly promises CLI session attribution",
        "description": "The task-session guidance describes CLI attribution as equivalent to tool attribution, contrary to the stated command contract and implementation.\n\nSuggested repair: Correct the guidance to say that tools infer task-session provenance, ordinary CLI writes use main-agent, --task supplies the report's task explicitly, and --provenance records caller-vouched provenance.",
        "impact": "Task sessions are told that shell writes preserve their task-session attribution even though shell reports default to main-agent and no task. This makes the guidance misleading when selecting how to record a report.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged prompts/guidance/issues/task-session.md:16-17, src/concorde/issues/command.py:435-444 against req.issues.main-agent-actor and reported a violation: The task-session guidance says, 'These tools record you as the task session of your task. The concorde issues command does the same from your shell. It also does the same for the runs you start.' The requirement explicitly assigns main-agent to command-supplied provenance and dispositions, reserving session attribution for MCP tools.",
        "owner_target_id": "module.issues",
        "evidence": [
          {
            "path": "prompts/guidance/issues/task-session.md",
            "description": "lines 16-17, shown by the violation finding"
          },
          {
            "path": "src/concorde/issues/command.py",
            "description": "lines 435-444, shown by the violation finding"
          },
          {
            "path": "specs/concorde/issues/requirements.md",
            "description": "defines req.issues.main-agent-actor, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.issues",
        "context_id": "sha256:985a655511357d2b9a8f9c799ecb1ace344be22b1cebfc16804d474ab231d869",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
