# I-34ad0d2d5a1255149bb3f12a8acdafdf

```json
{
  "schema_version": 4,
  "id": "I-34ad0d2d5a1255149bb3f12a8acdafdf",
  "status": "open",
  "reports": [
    {
      "id": "sha256:378f30ad32fb3f355c2bb66033551d5fca9e9ba037fef46719fb9de62cb6d12d",
      "created_at": "2026-10-08T08:00:09.217402+00:00",
      "report": {
        "report_key": "spec-panel/module.harness/3",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Distinguish extension policy from sandbox inputs",
        "description": "The entry incorrectly limits the permission extension's inputs to sandbox lists, contradicting the detailed policy contract. It conflates the extension's direct file checks with the sandbox engine's filesystem configuration.\n\nSuggested repair: State that the sandbox engine receives the filesystem configuration, while the permission extension also receives the grant and other policy inputs specified in pi.md for its direct file-tool decisions.",
        "impact": "A maintainer relying on the entry can omit policy inputs required by direct file checks or incorrectly assume those decisions must be reconstructed from sandbox lists.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f judged specs/concorde/worker-harness/harness/module.md at Known limits of v1, line 420 by the design criterion of the Protocol's Evaluating a Spec; the Specs read: module.md states: “The pi permission extension receives only the sandbox lists.” pi.md's Permission extension section says its embedded policy contains the grant's rw, ro and names lists, runtime paths, Git administrative paths, the primary worktree and the user's real home directory, as well as sandbox configuration.\n\nThe panel's chair merged r1.3, r2.4 and verified: Verified the exclusive claim against the explicit embedded-policy inventory and direct path checks in pi.md. Medium severity reflects misleading maintenance guidance with a clear corrective contract available; obvious-fix applies because distinguishing the extension policy from sandbox inputs resolves the contradiction without a policy decision.",
        "owner_target_id": "module.harness",
        "evidence": [
          {
            "path": "specs/concorde/worker-harness/harness/module.md",
            "description": "Known limits of v1, cited by the design finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.harness",
        "context_id": "sha256:9a3e9b9f367f7b8d2473b76d52c4f1d6c93178fc8fab1efc143a338d7bfab1f2",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
