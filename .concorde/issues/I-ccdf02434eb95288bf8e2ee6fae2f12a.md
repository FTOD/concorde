# I-ccdf02434eb95288bf8e2ee6fae2f12a

```json
{
  "schema_version": 4,
  "id": "I-ccdf02434eb95288bf8e2ee6fae2f12a",
  "status": "open",
  "reports": [
    {
      "id": "sha256:b2a78366b7f79ce5fd80ddbe11cbe355084898e1f6b74e8125df8529e26cb786",
      "created_at": "2026-10-08T07:40:06.055778+00:00",
      "report": {
        "report_key": "spec-panel/module.distribution/8",
        "tier": "suggestion",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Private MCP protocol details obscure the entry's use and design",
        "description": "The entry mixes its design explanation with an extensive second account of private MCP protocol and execution details already specified in contracts.md. This obscures the distinction between explanatory and implementation reading and delays the installation path.\n\nSuggested repair: Keep the flow diagram, fresh-process rationale, routing guarantees, lock ownership, channel limitations and public recovery guidance in the entry. Consolidate exact private command forms, message fields and routing mechanics in contracts.md and link to them.",
        "impact": "Readers seeking the Module's use and design must work through repeated private protocol details, and editors must keep parallel detailed accounts synchronized.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/distribution/module.md at Serving a call, line 488 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: The entry specifies private `concorde project-mcp --call <tool>` and --tools invocations, JSON transfer, routing comparisons, rerouting and thread selection. The contracts document's Calls section separately defines these mechanisms, while the entry itself says 'The contract fixes every message exactly.'\n\nThe panel's chair merged r1.9, r3.8 and verified: Verified the duplicated mechanics while retaining the value of the call-flow diagram, current-code rationale and lock-lifetime explanation. This is advisory because the details remain understandable; medium severity reflects substantial recurring reading and maintenance effort in the entry.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/module.md",
            "description": "Serving a call, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.distribution",
        "context_id": "sha256:351462ae398f78372c5c7be368810d05008976bca7e29394f2664300193a1ece",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
