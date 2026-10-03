# I-ec8615a51f8d5185bedf895cccced0d4

```json
{
  "schema_version": 4,
  "id": "I-ec8615a51f8d5185bedf895cccced0d4",
  "status": "open",
  "reports": [
    {
      "id": "sha256:5c68d28c33b75b4396567482c0bde39cccd2ab2c732b87370d448b2f11ecbb7d",
      "created_at": "2026-10-03T08:43:39.639138+00:00",
      "report": {
        "report_key": "module.distribution/11",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "after_update has no defined mapping for generic reports",
        "description": "The registration presents after_update as a generic report hook, but the public update result defines only Coordination's fixed open-task report. The hook's allowable results and multiple-contributor behavior are unspecified.\n\nSuggested repair: Decide whether after_update is specifically an open-task provider or a generic per-part report hook. Prefer the narrower contract if no other reports are intended; define its item shape, contributor rules and combination behavior explicitly.\n\nOther Modules concerned: module.coordination, module.tasks",
        "impact": "Another part registering the hook cannot determine what result it may return or where that result is represented without violating the update-result contract.",
        "basis": "spec_panel run r-20261003T074406-spec_panel-0a7388d8 judged specs/concorde/distribution/contracts.md at contract.distribution.part-registration, line 26 by the interfaces criterion of the Protocol's Evaluating a Spec; the Specs read: after_update answers “the list the update result carries, such as the open tasks”. The update result instead has a fixed open_tasks array of {id, branch, worktree}, with semantics specifically naming Coordination's report and no generic report field.\n\nThe panel's chair merged r1.12 and verified: Verified the entire update-result schema and semantics, which clearly define the present Coordination case but do not resolve the registration's generic wording. Medium severity for extension beyond the existing contributor; decision-needed because narrowing the extension point or broadening its output changes the shared promise.",
        "owner_target_id": "module.distribution",
        "evidence": [
          {
            "path": "specs/concorde/distribution/contracts.md",
            "description": "contract.distribution.part-registration, cited by the interfaces finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T074406-spec_panel-0a7388d8",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:2ff62e1118b212ef9ad5fe6e9d93adf72d0b8ac20908c609971a80ecb027ae5f",
        "change_id": "parts-review-specs",
        "head": "959c856c3a7732af1420829a271f59dd21ba837c"
      }
    }
  ],
  "dispositions": []
}
```
