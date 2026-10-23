# I-eca2a1fa43605c82b01b3b7aab99e1bc

```json
{
  "schema_version": 4,
  "id": "I-eca2a1fa43605c82b01b3b7aab99e1bc",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:1b76afb668370f683d0d1aedc1b54063deca9643011bbb63670ddc6bd02389d0",
      "created_at": "2026-10-13T17:22:11.884264+00:00",
      "report": {
        "report_key": "architecture/project/6",
        "tier": "obvious-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "spec-conflict",
        "title": "Method requires grant recomputation that General work forbids",
        "description": "Method requires every worker-backed step to compute a grant, with no exception for General work's required reuse of the first worker's frozen grant. The parent obligation contradicts both its own sequence explanation and the child's review contract.\n\nSuggested repair: Add the documented frozen-grant reuse exception to req.method.workspace-specs and align req.method.grant-as-data's references to the grant a step computed. State that first computation uses the run worktree's Specs and General work's reviewer reuses the original grant and context identity with writes lowered to read.\n\nOther Modules concerned: module.general-work",
        "impact": "Following the parent requirement leads a task to recompute the reviewer's grant. That can remove its original provider context or prevent review from launching after a malformed metadata edit.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/method/requirements.md at req.method.workspace-specs, line 11 by the consistency criterion of the Protocol's Evaluating a Spec; the Specs read: specs/concorde/method/requirements.md:11 says “Every worker-backed step of a Method Operation SHALL compute grants from these Specs”. method/general-work/requirements.md:76–78 requires the reviewer to reuse the worker's grant, “not under a grant computed from the changed Specs”. method/workers.md:375–379 says the reusing step “then computes no grant”, and scenario.general-work.reviewer-frozen-grant requires review to launch even after the first worker breaks metadata.\n\nThe panel's chair merged a2.5 and verified: Verified the unconditional parent requirement, General work's opposing requirement and scenario, and Method's own reuse explanation. High severity because the contradiction affects General work's normal independent review sequence. Obvious-fix because the intended exception is already precisely specified in both Modules.",
        "owner_target_id": "module.method",
        "evidence": [
          {
            "path": "specs/concorde/method/requirements.md",
            "description": "req.method.workspace-specs, cited by the consistency finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "project",
        "context_id": "sha256:ee7dfda15c5bbed6045f904dbc24b74b9a0b32064af7bda1f4e7f475ba7f4810",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "architecture"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task r4-review-tuning, merged into the primary branch at 8328b239d9971b26dc187c33f366015d0f2ee8fe.",
      "evidence": [
        "merge commit 8328b239d9971b26dc187c33f366015d0f2ee8fe",
        "task r4-review-tuning"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-23T09:21:46.400980+00:00"
    }
  ]
}
```
