# I-2d958da33dcb5acd9663f0f3e0ca8a7d

```json
{
  "schema_version": 4,
  "id": "I-2d958da33dcb5acd9663f0f3e0ca8a7d",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:1910a167f2f38b0b04aa8cddce7e0f4e2a1d29043cb1372bf031fa3de9d4db9b",
      "created_at": "2026-10-13T14:51:28.879831+00:00",
      "report": {
        "report_key": "issue-exception-scope/dogfood-scenarios-wording",
        "tier": "obvious-fix",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Dogfood scenarios still say every Issue-system defect goes as a bare error chain",
        "description": "specs/concorde/e2e/dogfood/module.md says a scenario's fault never lies in Concorde's Issue system and that 'Dogfooding sends such a defect as a bare error chain, never as a defect report'. Since task issue-exception-scope, Dogfooding sends only a failure of the Issue system (crash, wrong result, wrong refusal) as a bare error chain; a design limitation of Issues that the working Issue system can record is an ordinary defect report.\n\nSuggested repair: say 'Dogfooding sends a failure of the Issue system as a bare error chain', keeping the exclusion of scenario faults in the Issue store, `concorde issues` and the Issue tools, which are failures.",
        "impact": "A reader of the dogfood scenarios' Module gets the old, wider exception and may believe any Issues design limitation is excluded from defect reports.",
        "basis": "Dogfooding's 'A failure of the Issue system' section and req.dogfooding.issue-design-limitation-reported (task issue-exception-scope, developer decision 2026-10-13) against the second paragraph of specs/concorde/e2e/dogfood/module.md. That file belongs to module.dogfood-scenarios, outside the task's Modules.",
        "owner_target_id": "module.dogfood-scenarios",
        "evidence": [
          {
            "path": "specs/concorde/e2e/dogfood/module.md",
            "description": "the paragraph that begins 'A scenario's fault never lies in Concorde's Issue system'"
          },
          {
            "path": "specs/concorde/dogfooding/module.md",
            "description": "section 'A failure of the Issue system', the narrowed exception"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-9992ff07-4375-4def-ae39-844ac5545f16",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.dogfood-scenarios",
        "context_id": "sha256:78b6217514ba2ddc4cd8a073e8b2438c1ed3f9d1c1736d74b9ec3cbc85ba6ebc",
        "change_id": "issue-exception-scope",
        "head": "57c3209534baedc3e4653a0918c3a7b9296c7d74"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task flaky-and-wording, merged into the primary branch at 4c71410e26f842cce27dab68d2c977c8117c8cd8.",
      "evidence": [
        "merge commit 4c71410e26f842cce27dab68d2c977c8117c8cd8",
        "task flaky-and-wording"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-13T16:18:56.349358+00:00"
    }
  ]
}
```
