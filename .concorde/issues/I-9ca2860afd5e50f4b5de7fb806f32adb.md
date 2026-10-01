# I-9ca2860afd5e50f4b5de7fb806f32adb

```json
{
  "schema_version": 3,
  "id": "I-9ca2860afd5e50f4b5de7fb806f32adb",
  "status": "open",
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
    }
  ],
  "dispositions": []
}
```
