# I-0c1af497f12b5c588c7d17d7bbbcfed9

```json
{
  "schema_version": 4,
  "id": "I-0c1af497f12b5c588c7d17d7bbbcfed9",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:53d39317b9f4fb741745f2511ebfec50e2a5c7f56cc6c1a60f6320f48ba22caa",
      "created_at": "2026-10-13T16:50:31.897458+00:00",
      "report": {
        "report_key": "spec-panel/module.understanding/2",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "Carry the new-promise exception into the gap scenario",
        "description": "The missing-promise scenario covers new promises with known ownership, although the requirement and assessment contract permit planning those changes.\n\nSuggested repair: Limit the GIVEN to an existing promise the goal relies on, or explicitly exclude new promises whose ownership the Specs establish. Add a concrete case showing a new promise with known ownership becoming a specify step.",
        "impact": "A task could implement or test ordinary feature requests as insufficient even when ownership is established and a specify step is allowed.",
        "basis": "project_review run r-20261013T163902-project_review-dfe5114c judged specs/concorde/method/understanding/scenarios.md at scenario.understanding.gap, line 23 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The GIVEN says “a goal that needs a promise the bound Module's Spec does not state” and the THEN requires “an assessment marked insufficient”. req.understanding.gaps-reported excludes a new promise for which the Specs already say where it belongs; the assessment contract illustrates a sufficient assessment with a specify step adding severity.\n\nThe panel's chair merged r2.1 and verified: Verified the scenario against the requirement's explicit exception and the contract's example. High because planning changes is a main use; preferred-fix because narrowing the scenario to an existing relied-upon promise preserves the canonical rule.",
        "owner_target_id": "module.understanding",
        "evidence": [
          {
            "path": "specs/concorde/method/understanding/scenarios.md",
            "description": "scenario.understanding.gap, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T163902-project_review-dfe5114c",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.understanding",
        "context_id": "sha256:da348b1e52e4f85be2b0a66a4e14ec2c264ffac26aa2865dd4e428fc9ae66057",
        "change_id": null,
        "head": "1e5ce2576250630071825f0e00ce7f342e2f153d",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task r4-method-work, merged into the primary branch at fbd1a1e92b64d950338cd035fc9adac07bcde8d2.",
      "evidence": [
        "merge commit fbd1a1e92b64d950338cd035fc9adac07bcde8d2",
        "task r4-method-work"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-23T09:02:28.644252+00:00"
    }
  ]
}
```
