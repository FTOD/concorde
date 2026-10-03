# I-ec8615a51f8d5185bedf895cccced0d4

```json
{
  "schema_version": 4,
  "id": "I-ec8615a51f8d5185bedf895cccced0d4",
  "status": "closed",
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
    },
    {
      "id": "sha256:04f442adc941a2626fcf00824feef6cb17d9c103e99f2286c872a108988502d2",
      "created_at": "2026-10-03T08:49:47.350558+00:00",
      "report": {
        "issue_id": "I-ec8615a51f8d5185bedf895cccced0d4",
        "expected_revision": "sha256:9bc86d5989ab6351e25319c69ae14faf41291056c7cde1d0275e3f939945e8a7",
        "report_key": "module.distribution/11-verified",
        "tier": "obvious-fix",
        "severity": "low",
        "title": "after_update is described as a generic report hook but feeds only open_tasks",
        "description": "specs/concorde/distribution/contracts.md: the registration table row says `after_update` answers 'the list the update result carries, such as the open tasks', and the semantics say 'the function whose report an update result carries, such as the open tasks'. contract.distribution.update-result has only `open_tasks` ({id, branch, worktree}), and install.py open_tasks() concatenates every part's after_update answer into it.\n\nFix: drop 'such as' and say what it is: '`after_update` | the project root | the open tasks, each {id, branch, worktree}, which the update result lists under open_tasks after those of earlier parts in the order of the parts table'; same in the semantics (\"after_update the function reporting the part's open tasks for the update result's open_tasks\").",
        "impact": "Only the coordination part registers it; a future part could return a different shape that breaks the update result's schema.",
        "basis": "Compared the contract row and semantics with contract.distribution.update-result and src/concorde/distribution/install.py open_tasks(). Classification: regression — part registrations and after_update are new with the refactor. Lowered to low and obvious-fix: the narrow reading matches the code and the only registrant.",
        "owner_target_id": "module.distribution",
        "type": "bug",
        "subtype": null,
        "evidence": [
          {
            "path": "specs/concorde/distribution/contracts.md",
            "description": "after_update row and registration semantics vs update-result open_tasks"
          },
          {
            "path": "src/concorde/distribution/install.py",
            "description": "open_tasks() concatenates after_update answers"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-b2a34cc8-5f4b-4841-931e-8dd138230b60",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.distribution",
        "context_id": "sha256:dc5a1d8cbf5a69d2834f2ea5f6545ea6067e5caf2e4e3c78dfc4f3342c22cb32",
        "change_id": "parts-review-specs",
        "head": "41bda04db324df4ff913498f023597a72c419955"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task parts-review-specs, merged into the primary branch at 8f6860b42000fa749564007acf84e7faea3d3a2c.",
      "evidence": [
        "merge commit 8f6860b42000fa749564007acf84e7faea3d3a2c",
        "task parts-review-specs"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-03T09:36:12.746537+00:00"
    }
  ]
}
```
