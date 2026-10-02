# I-32b6af7d5ce95306bcbfdafd06bcc568

```json
{
  "schema_version": 3,
  "id": "I-32b6af7d5ce95306bcbfdafd06bcc568",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:bb8de5b783cabecd370a9e9659496b70ce3b762f59ea71fc7cf2465e6995fe74",
      "created_at": "2026-10-01T05:30:48.810163+00:00",
      "report": {
        "report_key": "module.distribution/2",
        "tier": "obvious-fix",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "The install scenario specifies obsolete workflow permissions",
        "description": "The normal-install scenario specifies permissions for two workflow CLI commands, contradicting the current installation design, which starts steps through MCP and uses Bash only for reporting.\n\nSuggested repair: Replace the two-command assertion with `Workflow(concorde-brownfield)`, `mcp__concorde__workflow_step` and `Bash(.concorde/bin/concorde workflow report:*)`, retaining the assertions about unrelated settings and receipt ownership.\n\nOther Modules concerned: module.workflows, module.main-session",
        "impact": "An implementation or acceptance test could retain the obsolete Bash step permission and omit the MCP permission required to start workflow steps.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/distribution/scenarios.md at scenario.distribution.install, line 100 by the consistency criterion of the Protocol's Evaluating a Spec; the Specs read: The scenario requires settings to allow \"`Workflow(concorde-brownfield)` and the two `concorde workflow` commands\". Installation step 7 instead names `mcp__concorde__workflow_step` and `Bash(.concorde/bin/concorde workflow report:*)`. Workflows says \"a step agent does not run the step command with Bash\".\n\nThe panel's chair merged r1.2, r2.1, r3.1, a2.4 and verified: Verified both Distribution passages and Workflows' explanation of MCP step execution. The current permission set is explicit, making the scenario correction unique.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/scenarios.md",
            "description": "scenario.distribution.install, cited by the consistency finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:763ec486bd954028051a1133a2036e5bb74e9c151d89fed6d611b973b9a9f4a8",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    },
    {
      "id": "sha256:3e95edd0412a489f96526318035f3ba6a1230542a6b1c3c8e56dab251b304927",
      "created_at": "2026-10-01T14:47:25.164354+00:00",
      "report": {
        "report_key": "module.distribution/2--severity",
        "tier": "obvious-fix",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "The install scenario specifies obsolete workflow permissions",
        "description": "The normal-install scenario specifies permissions for two workflow CLI commands, contradicting the current installation design, which starts steps through MCP and uses Bash only for reporting.\n\nSuggested repair: Replace the two-command assertion with `Workflow(concorde-brownfield)`, `mcp__concorde__workflow_step` and `Bash(.concorde/bin/concorde workflow report:*)`, retaining the assertions about unrelated settings and receipt ownership.\n\nOther Modules concerned: module.workflows, module.main-session",
        "impact": "An implementation or acceptance test could retain the obsolete Bash step permission and omit the MCP permission required to start workflow steps.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/distribution/scenarios.md at scenario.distribution.install, line 100 by the consistency criterion of the Protocol's Evaluating a Spec; the Specs read: The scenario requires settings to allow \"`Workflow(concorde-brownfield)` and the two `concorde workflow` commands\". Installation step 7 instead names `mcp__concorde__workflow_step` and `Bash(.concorde/bin/concorde workflow report:*)`. Workflows says \"a step agent does not run the step command with Bash\".\n\nThe panel's chair merged r1.2, r2.1, r3.1, a2.4 and verified: Verified both Distribution passages and Workflows' explanation of MCP step execution. The current permission set is explicit, making the scenario correction unique. Severity high assessed by the main agent on 2026-10-01: An installer or acceptance test following the scenario would omit the MCP permission required to start workflow steps, breaking the installed workflow flow.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/scenarios.md",
            "description": "scenario.distribution.install, cited by the consistency finding"
          }
        ],
        "severity": "high",
        "issue_id": "I-32b6af7d5ce95306bcbfdafd06bcc568",
        "expected_revision": "sha256:8f8c5ca9918fbd4da61caaf4778b4e65337f0765aa4574b196c872099bf8985a"
      },
      "source": {
        "invocation_id": "cli-9f12637d-20d6-45ca-aca6-3a35bd51af4b",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:faf611ab5bdd47f3ab93968932072ec605e527fb468e96a4f6c20a419e8f0f8c",
        "change_id": null,
        "head": "83112f65d45b0932888e9acfeb3261bca4b1844e"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-distribution, merged into the primary branch at 8e89f86c1b36dc5afd1668912f45448e281fb4d4.",
      "evidence": [
        "merge commit 8e89f86c1b36dc5afd1668912f45448e281fb4d4",
        "task fix-distribution"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-02T02:16:43.669915+00:00"
    }
  ]
}
```
