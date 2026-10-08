# I-3979db33bbab5ec1bd48bc3dcb37dd57

```json
{
  "schema_version": 4,
  "id": "I-3979db33bbab5ec1bd48bc3dcb37dd57",
  "status": "open",
  "reports": [
    {
      "id": "sha256:5ec147670f49fb3481e5b8590a02081171f46ce1c657fe0b920af857a73d6521",
      "created_at": "2026-10-08T03:11:02.194885+00:00",
      "report": {
        "report_key": "architecture/project/8",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "missing-contract",
        "title": "SWE-bench cases does not select its grading reference",
        "description": "SWE-bench cases assumes its parent's external inclusion makes the grading standard available. External context is not inherited through an included parent entry.\n\nSuggested repair: Add a direct external inclusion of the relevant pinned references/swe-bench/ material to SWE-bench cases, with a reason identifying the dataset and grading semantics it relies on.\n\nOther Modules concerned: module.e2e",
        "impact": "A task bound to SWE-bench cases cannot consult the pinned dataset and grading reference needed to assess its promised compatibility.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 judged specs/concorde/e2e/cases/module.md at Around it, line 278 by the context criterion of the Protocol's Evaluating a Spec; the Specs read: SWE-bench cases says: \"SWE-bench is external material, included by End-to-end testing.\" Its declarations include only document.e2e.module and no external material. The root states: \"Only the bound Modules' own inclusions count. A Module their relations select brings none.\" The cases entry promises grading \"the way SWE-bench grades it.\"\n\nThe panel's chair merged a1.8 and verified: Verified the grading reliance, cases' complete inclusion list and the root's external-context rule. Medium severity reflects the grading reference gap in this auxiliary Module. Preferred-fix selects the existing reference directly without altering grading behavior.",
        "owner_target_id": "module.swe-bench-cases",
        "evidence": [
          {
            "path": "specs/concorde/e2e/cases/module.md",
            "description": "Around it, cited by the context finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "project",
        "context_id": "sha256:43658a6822fc5d55e13ba89679ad39e4244612f565000b6cecb03098887a977d",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "architecture"
      }
    }
  ],
  "dispositions": []
}
```
