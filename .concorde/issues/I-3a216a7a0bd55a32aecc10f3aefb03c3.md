# I-3a216a7a0bd55a32aecc10f3aefb03c3

```json
{
  "schema_version": 4,
  "id": "I-3a216a7a0bd55a32aecc10f3aefb03c3",
  "status": "open",
  "reports": [
    {
      "id": "sha256:198ad74bccf852e697755c9d9729ef807fa02202b25f75f47a13d60e14a57cae",
      "created_at": "2026-10-13T18:47:04.198617+00:00",
      "report": {
        "report_key": "spec-panel/module.headless-sessions/7",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "LiveSession leaves query results and failure delivery unspecified",
        "description": "LiveSession exposes methods and named failures without defining several return values or how those failures reach callers. Its bounded wait and closing behavior also have no canonical implementation contract.\n\nSuggested repair: Specify each public method's inputs, return value, effects, and failure delivery, including live_timeout and session_failed. Define bounded waiting and close/kill behavior in implementation reading, with scenarios for timeout, process loss, and closing.",
        "impact": "A caller cannot implement event reads or error handling against LiveSession from its Spec, and a task changing the interface has no precise contract to preserve.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/e2e/sessions/module.md at live-sessions, line 323 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “`since`, `turns`, `notifications` and `tool_output` read the events that arrived from a given time on.” “`wait_settled` waits at most the given seconds for a turn to end, with `live_timeout` when none ends.” A process that cannot start or ends during a send or wait “fails with `session_failed`.”\n\nThe panel's chair merged r1.5 and verified: Verified the usage example and surrounding method descriptions. They explain the normal sequence and some return values, but not the cited query results or failure delivery mechanism. Medium severity for incomplete programmatic interface details. Decision-needed rather than preferred-fix because choosing these representations creates promises the Spec does not currently state.",
        "owner_target_id": "module.headless-sessions",
        "evidence": [
          {
            "path": "specs/concorde/e2e/sessions/module.md",
            "description": "live-sessions, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.headless-sessions",
        "context_id": "sha256:93b6e4c52a25a3c80e6aa35d563fd4b9b29870750c499fba5d692444c76f1eb4",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
