# I-3b98ba7b22a15c7d9faed1b4fbc62b84

```json
{
  "schema_version": 4,
  "id": "I-3b98ba7b22a15c7d9faed1b4fbc62b84",
  "status": "open",
  "reports": [
    {
      "id": "sha256:736af0611be91273205f29fc2ccc25131b3845e54ed77ae265d07255b1a32f5e",
      "created_at": "2026-10-13T19:27:57.983577+00:00",
      "report": {
        "report_key": "code-review/module.spec-mcp/2",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Deeply nested JSON input terminates the session",
        "description": "A deeply nested JSON array escapes the malformed-message handling as RecursionError and terminates the process. Parsing occurs outside the session loop's exception handler, so the promised recovery never runs.\n\nSuggested repair: Handle decoder depth failures at the input boundary and preserve the specified JSON-RPC error behavior for rejected messages. Add a stdio regression test with a deeply nested array followed by a valid request, asserting both the error response and continued service.",
        "impact": "One deeply nested input line terminates the server, so the next well-formed request receives no answer and the client must restart the connection.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 (module review) judged src/concorde/spec/mcp/server.py:44-60, src/concorde/spec/mcp/server.py:74-80, src/concorde/spec/mcp/server.py:224-228 against scenario.spec-mcp.malformed-message and reported a violation: The session contract promises that a malformed message never ends the session, and the scenario requires JSON arrays to receive -32600 followed by continued service. server.py:49 calls json.loads, which raises RecursionError for sufficiently deeply nested JSON arrays; the parser catches only ValueError at line 50. The receive call at line 225 is outside run's exception handler.",
        "owner_target_id": "module.spec-mcp",
        "evidence": [
          {
            "path": "src/concorde/spec/mcp/server.py",
            "description": "lines 44-60, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/mcp/server.py",
            "description": "lines 74-80, shown by the violation finding"
          },
          {
            "path": "src/concorde/spec/mcp/server.py",
            "description": "lines 224-228, shown by the violation finding"
          },
          {
            "path": "specs/concorde/spec-tooling/spec-mcp/scenarios.md",
            "description": "defines scenario.spec-mcp.malformed-message, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec-mcp",
        "context_id": "sha256:948e6650405553c135cdeb766931c47803f95e95d6fc4606c4ba9624f9e6d3a7",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
