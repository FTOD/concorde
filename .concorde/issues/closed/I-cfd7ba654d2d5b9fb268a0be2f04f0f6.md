# I-cfd7ba654d2d5b9fb268a0be2f04f0f6

```json
{
  "schema_version": 4,
  "id": "I-cfd7ba654d2d5b9fb268a0be2f04f0f6",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:f62821315fa9f1f4730c2602295d4078d95567c35a6dc0aa8b463183577cd08b",
      "created_at": "2026-10-02T19:35:27.015277+00:00",
      "report": {
        "report_key": "module.worker-harness/4",
        "tier": "preferred-fix",
        "severity": "high",
        "type": "bug",
        "subtype": null,
        "title": "The part entry omits material limits of grant confinement",
        "description": "The part's entry presents grant confinement without explaining the threat model or material read-confinement limits. Those qualifications appear only in its children's entries.\n\nSuggested repair: State that enforcement guards against scope drift and mistakes rather than malicious agents, and is not complete host isolation. Briefly identify readable host paths and the Claude Code late-created-file limitation, linking Harness's known limits and Workers' explanation for the precise boundaries.\n\nOther Modules concerned: module.harness, module.workers",
        "impact": "A consumer choosing the standalone part may treat its grant as complete host isolation or a confidentiality boundary, although the children explicitly do not support that use.",
        "basis": "spec_panel run r-20261002T190724-spec_panel-89d5bab4 judged specs/concorde/worker-harness/module.md at Purpose, line 7 by the design criterion of the Protocol's Evaluating a Spec; the Specs read: The entry says it \"bounds what the worker may read, write and run\" without qualification. specs/concorde/worker-harness/harness/module.md says enforcement \"guards against scope drift and mistakes, not a malicious agent\" and that \"system directories and other paths outside them stay readable to every tool\". Workers' entry explains that a Git-ignored file another process creates during a Claude Code run may be read \"without anything failing\".\n\nThe panel's chair merged r3.2 and verified: Verified Harness's purpose and known limits and Workers' late-created-file explanation. These are consumer-facing limits absent from the part entry. High severity because choosing the wrong confinement guarantee is consequential; preferred-fix because the existing limits can be explained without redefining enforcement.",
        "owner_target_id": "module.worker-harness",
        "evidence": [
          {
            "path": "specs/concorde/worker-harness/module.md",
            "description": "Purpose, cited by the design finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261002T190724-spec_panel-89d5bab4",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.worker-harness",
        "context_id": "sha256:6578f8863df3ca507b68a925fd9f51989aaa566a8261fc015fbc481106707e21",
        "change_id": "parts-spec",
        "head": "5c717b606e11e429829ec27129610d7a6d21916a"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task parts-spec, merged into the primary branch at d58b087c8b71f65237c094b073ead80c24605a1c.",
      "evidence": [
        "merge commit d58b087c8b71f65237c094b073ead80c24605a1c",
        "task parts-spec"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-02T20:09:50.439530+00:00"
    }
  ]
}
```
