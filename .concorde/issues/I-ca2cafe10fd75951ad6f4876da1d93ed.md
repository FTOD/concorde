# I-ca2cafe10fd75951ad6f4876da1d93ed

```json
{
  "schema_version": 4,
  "id": "I-ca2cafe10fd75951ad6f4876da1d93ed",
  "status": "open",
  "reports": [
    {
      "id": "sha256:eb7291a1a793f0445fb01bed4ac5a337bc4955fbcfc87b174d06510fce2b2838",
      "created_at": "2026-10-13T18:36:56.831851+00:00",
      "report": {
        "report_key": "spec-panel/module.general-work/5",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Correct the rewrite scenario's writable boundary",
        "description": "The rewrite scenario excludes every writable resource except Spec documents, although a specify grant also includes the project glossary subject to entry ownership.\n\nSuggested repair: State that the worker may change only what the specify grant makes writable, explicitly including the bound Module's permitted glossary entries as well as its Spec documents.\n\nOther Modules concerned: module.spec, module.method",
        "impact": "A tester could assert that the glossary is not writable, or an implementer could narrow the specify grant incorrectly.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/general-work/scenarios.md at scenario.general-work.rewrite, line 12 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: The rewrite scenario says, \"THEN the worker may change the Module's Spec documents and nothing else.\" Spec core's contracts.md defines Spec scope as \"both members of each owned document, and the project glossary, of whose entries only those the Module owns or adds are its to change.\"\n\nThe panel's chair merged r1.7 and verified: Verified the scenario against Spec core's boundary definition and General work's grant-by-type requirement. Upgraded from advisory because the stated boundary contradicts the canonical grant. Medium severity reflects the glossary edge case; the existing grant definition makes the repair obvious. The source's separate observation about two alternative WHEN commands is editorial and is not the basis of this finding.",
        "owner_target_id": "module.general-work",
        "evidence": [
          {
            "path": "specs/concorde/method/general-work/scenarios.md",
            "description": "scenario.general-work.rewrite, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.general-work",
        "context_id": "sha256:08e4b8be556eb6ab31bb6e0687cd9a3d954a78d15f98ad2b96471176f8c54178",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
