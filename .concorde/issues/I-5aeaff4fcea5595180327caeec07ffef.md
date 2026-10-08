# I-5aeaff4fcea5595180327caeec07ffef

```json
{
  "schema_version": 4,
  "id": "I-5aeaff4fcea5595180327caeec07ffef",
  "status": "open",
  "reports": [
    {
      "id": "sha256:c392e5ec70719efe4c73fdb416b3e27c30d08a7f7555bf81d1acb0bf5b29abd9",
      "created_at": "2026-10-08T03:16:47.649318+00:00",
      "report": {
        "report_key": "spec-panel/module.adoption/11",
        "tier": "suggestion",
        "severity": "low",
        "type": "bug",
        "subtype": null,
        "title": "Capability restrictions should name the enforcing actor",
        "description": "The capability restrictions use passive or capability wording instead of naming the actor that imposes them.\n\nSuggested repair: Use active wording naming the already-established responsible host and the tools or grant it supplies, preserving the worker restrictions and Scaffold exception.",
        "impact": "Readers must infer the enforcing actor from the surrounding design rather than finding it in the restriction itself.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 judged specs/concorde/method/adoption/requirements.md at req.adoption.no-bash, line 105 by the readability criterion of the Protocol's Evaluating a Spec; the Specs read: “The survey and code_to_spec workers SHALL NOT be given a tool that runs commands.” req.adoption.modules-by-host likewise says a worker “SHALL NOT be able to add or remove a Module.” The entry explains host grant preparation and worker-tool configuration.\n\nThe panel's chair merged r2.8, r3.8 and verified: Verified both restrictions and the surrounding host/grant explanation. Low severity and advisory because the responsibility is recoverable. Any rewrite should name the established enforcing actor without shifting the promise to the worker.",
        "owner_target_id": "module.adoption",
        "evidence": [
          {
            "path": "specs/concorde/method/adoption/requirements.md",
            "description": "req.adoption.no-bash, cited by the readability finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.adoption",
        "context_id": "sha256:419d153fe4bca21c25de5e5fdb0218f7b6c5b667170c6bb3a6e7cf45ffeaea5d",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
