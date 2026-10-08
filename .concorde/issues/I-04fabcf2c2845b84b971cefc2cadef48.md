# I-04fabcf2c2845b84b971cefc2cadef48

```json
{
  "schema_version": 4,
  "id": "I-04fabcf2c2845b84b971cefc2cadef48",
  "status": "open",
  "reports": [
    {
      "id": "sha256:6e30f3e1ca857c1d4858c2db9ca3546ac37135cf862c05044ece4afd79fd904a",
      "created_at": "2026-10-08T08:43:35.831157+00:00",
      "report": {
        "report_key": "spec-panel/module.spec/6",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "Limit the typed-value description to records that use that format",
        "description": "The entry describes all records as typed values, contradicting the distinct representations of several principal records.\n\nSuggested repair: Limit the explanation to records whose contracts designate them as typed values, such as initialization proposals. State that configuration, registry and grant records retain their separately defined formats.\n\nOther Modules concerned: module.kernel",
        "impact": "A reader can wrap ordinary control records in the typed-value envelope and produce inputs their canonical contracts reject.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/spec-tooling/spec/module.md at Its own data utilities, line 121 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: “The records Spec core reads and writes are typed values {type_id, schema_version, data}.” contracts.md instead defines closed configuration and registry objects and an unenveloped grant value.\n\nThe panel's chair merged r1.10, r2.10, r3.10 and verified: Verified the entry claim against the configuration, registry and grant shapes; Kernel's selected entry also explicitly distinguishes typed values from other records. High because configuration and registry loading are main uses, with exact contracts providing a way out. Preferred-fix preserves those canonical formats.",
        "owner_target_id": "module.spec",
        "evidence": [
          {
            "path": "specs/concorde/spec-tooling/spec/module.md",
            "description": "Its own data utilities, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.spec",
        "context_id": "sha256:b9d71c73a527514a46b9ca3276c669e4c070ce765d7a7c1c3f02e4b4fde5b92b",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
