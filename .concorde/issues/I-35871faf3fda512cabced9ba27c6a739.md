# I-35871faf3fda512cabced9ba27c6a739

```json
{
  "schema_version": 4,
  "id": "I-35871faf3fda512cabced9ba27c6a739",
  "status": "open",
  "reports": [
    {
      "id": "sha256:dff136e8dd88f7b32095311533ac79b5c3d769ee72aeb0202107825f230004a6",
      "created_at": "2026-10-08T03:58:57.050606+00:00",
      "report": {
        "report_key": "spec-panel/module.task-session/6",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Give alternate scenario outcomes complete premises",
        "description": "Several scenarios append alternate situations without defining complete changed premises. The malformed-file outcome does not follow from the two-file fixture, and the cost outcome omits a necessary ordering condition.\n\nSuggested repair: Split alternate launch, approval and finalization situations into independent scenarios. Specify which MCP files are unusable and preserve decisions for servers in valid files. For the cost case, state that no assistant record follows the last cost-state record and cover the later-assistant case separately.",
        "impact": "Acceptance tests can discard servers from a remaining valid file or expect a non-null cost where the contract requires null. Test authors must invent changed fixtures for the alternate outcomes.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 judged specs/concorde/coordination/task-session/scenarios.md at scenario.task-session.mcp-approval, line 38 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The MCP scenario supplies two .mcp.json files with distinct servers, then says “a .mcp.json that is missing, not JSON or without an mcpServers object names no server” and “with such a file, the session starts with only concorde disabled.” The node-finished scenario specifies a “last cost-state record of 0.42 USD” without excluding later assistant records, although the contract requires their absence for that cost outcome.\n\nThe panel's chair merged r1.5, r2.4, r3.7 and verified: Verified the two-file fixture, cost-state condition and alternate launch/finalization branches. Medium severity reflects unreliable acceptance outcomes in edge cases. Several fixture rewrites are possible; separate complete situations are the preferred repair.",
        "owner_target_id": "module.task-session",
        "evidence": [
          {
            "path": "specs/concorde/coordination/task-session/scenarios.md",
            "description": "scenario.task-session.mcp-approval, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.task-session",
        "context_id": "sha256:890863ee44b220167ff4778ecf90df850af1bbfeaad300511e8bf57ad06b1a29",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
