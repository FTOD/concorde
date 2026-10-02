# I-9ca2860afd5e50f4b5de7fb806f32adb

```json
{
  "schema_version": 3,
  "id": "I-9ca2860afd5e50f4b5de7fb806f32adb",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:d779205a0a489df193fa8b5b615d75a4a40a8149d9f2b376ef76ea420a3c6aa8",
      "created_at": "2026-10-01T05:22:40.880271+00:00",
      "report": {
        "report_key": "module.concorde/18",
        "tier": "preferred-fix",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "The agent decision policy is outside the root's selected context",
        "description": "The root relies on Main session's canonical decision and escalation policy without selecting its defining documents into the root's own context.\n\nSuggested repair: Explicitly select Main session's entry and the defining decision/escalation requirements, with a reason naming the root's reliance, while retaining policy ownership in Main session.\n\nOther Modules concerned: module.coordination, module.main-session",
        "impact": "A root-bound task working on agent guidance cannot consult the policy that determines which decisions may be taken autonomously.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/module.md at The people and agents, line 48 by the context criterion of the Protocol's Evaluating a Spec; the Specs read: \"[Main session](coordination/main-session/module.md) explains its working method and decision policy.\" The root later invokes ordinary versus major decisions. Its metadata selects Coordination but has empty uses and includes, and selection is one level deep. Main session's escalation-policy requirement defines major impact in detail.\n\nThe panel's chair merged r3.4 and verified: Verified root selection, Coordination's explanation, and Main session's actual decision policy. Coordination refers readers onward rather than supplying that defining policy; architectural access during this audit does not repair root Module context.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/module.md",
            "description": "The people and agents, cited by the context finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261001T051011-spec_panel-91e80034",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.concorde",
        "context_id": "sha256:305c8527376219b0846ea77dd1408f9fab3dc7a2668b3da9791a000f3b49a771",
        "change_id": null,
        "head": "eb6687427361c480d7a7eb0d9a022b0c2c9f5dbb"
      }
    },
    {
      "id": "sha256:f73bc5b9f6c40801d1556ec7158034d187fec18ff18b003d89b3b1e499921588",
      "created_at": "2026-10-01T14:47:29.986827+00:00",
      "report": {
        "report_key": "module.concorde/18--severity",
        "tier": "preferred-fix",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "The agent decision policy is outside the root's selected context",
        "description": "The root relies on Main session's canonical decision and escalation policy without selecting its defining documents into the root's own context.\n\nSuggested repair: Explicitly select Main session's entry and the defining decision/escalation requirements, with a reason naming the root's reliance, while retaining policy ownership in Main session.\n\nOther Modules concerned: module.coordination, module.main-session",
        "impact": "A root-bound task working on agent guidance cannot consult the policy that determines which decisions may be taken autonomously.",
        "basis": "spec_panel run r-20261001T051011-spec_panel-91e80034 judged specs/concorde/module.md at The people and agents, line 48 by the context criterion of the Protocol's Evaluating a Spec; the Specs read: \"[Main session](coordination/main-session/module.md) explains its working method and decision policy.\" The root later invokes ordinary versus major decisions. Its metadata selects Coordination but has empty uses and includes, and selection is one level deep. Main session's escalation-policy requirement defines major impact in detail.\n\nThe panel's chair merged r3.4 and verified: Verified root selection, Coordination's explanation, and Main session's actual decision policy. Coordination refers readers onward rather than supplying that defining policy; architectural access during this audit does not repair root Module context. Severity medium assessed by the main agent on 2026-10-01: A root-bound task on agent guidance cannot consult the decision policy from its selected context, a gap that slows the work.",
        "owner_target_id": "module.concorde",
        "evidence": [
          {
            "path": "specs/concorde/module.md",
            "description": "The people and agents, cited by the context finding"
          }
        ],
        "severity": "medium",
        "issue_id": "I-9ca2860afd5e50f4b5de7fb806f32adb",
        "expected_revision": "sha256:2d730656c8c16419d42101ee3f88a0718f228ee0dcd11e04cda76a0f6dbd61cf"
      },
      "source": {
        "invocation_id": "cli-1508fd33-bb0e-4a39-8bdb-25cab1c9b58f",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.concorde",
        "context_id": "sha256:faf611ab5bdd47f3ab93968932072ec605e527fb468e96a4f6c20a419e8f0f8c",
        "change_id": null,
        "head": "df98c745ca1687b5ead6aaedbba297d02a7d4f38"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-root-module, merged into the primary branch at 92403a4083871bbf528a78d8f5dc2976ab81f9ca.",
      "evidence": [
        "merge commit 92403a4083871bbf528a78d8f5dc2976ab81f9ca",
        "task fix-root-module"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-02T02:17:29.139665+00:00"
    }
  ]
}
```
