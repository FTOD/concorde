# I-479cad16fe2b5d0bbefdec5b32c7e9b1

```json
{
  "schema_version": 4,
  "id": "I-479cad16fe2b5d0bbefdec5b32c7e9b1",
  "status": "open",
  "reports": [
    {
      "id": "sha256:476d5ec9d90be191d3400f3166e8a9465fcaa773f4a39432306094fd4703926b",
      "created_at": "2026-10-13T20:05:55.088226+00:00",
      "report": {
        "report_key": "spec-panel/module.tasks/7",
        "tier": "suggestion",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Make requirement conditions, lists and actors easier to read",
        "description": "Several requirement statements put exceptions after the actions they limit, run lists together, or use passive subjects despite established actors in nearby prose.\n\nSuggested repair: Move whole-obligation conditions before their statements, use vertical lists for enumerations, and name the already established Task store and operating-system actors where appropriate. Preserve each condition's scope and all exceptions.",
        "impact": "Readers must disentangle trailing exceptions and recover actors from nearby explanations.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/coordination/tasks/requirements.md at req.tasks.merge-exact-commit, line 382 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: merge-exact-commit ends its obligation with \"unless the primary branch already contains that head, when it makes no merge commit\". merge-incomplete-refused chains commands and required refusal details in one sentence. record-transactions says \"Every change to a task record SHALL be one [file transaction]\"; merge-lock-released says \"the merge lock SHALL be released\".\n\nThe panel's chair merged r1.7, r2.13 and verified: Verified the semantic style examples rather than sentence lengths or keyword counts. Merged the overlapping passive-voice report. Low and advisory because the surrounding text establishes the actors and conditions.",
        "owner_target_id": "module.tasks",
        "evidence": [
          {
            "path": "specs/concorde/coordination/tasks/requirements.md",
            "description": "req.tasks.merge-exact-commit, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.tasks",
        "context_id": "sha256:f497bc164eba45dad39aa87bce07d7df8632247026c710b423b2a3e9bcb91301",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
