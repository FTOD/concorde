# I-4aa68b8b2b5e5eaaaa5a0dd333103eb1

```json
{
  "schema_version": 4,
  "id": "I-4aa68b8b2b5e5eaaaa5a0dd333103eb1",
  "status": "open",
  "reports": [
    {
      "id": "sha256:056ee2cb24d6d9deec10f5644773c3ab70041cd64cf625ae1eca7305385852a6",
      "created_at": "2026-10-13T12:01:00.535995+00:00",
      "report": {
        "report_key": "r3-workflows-issues-root/method-concorde-fallback",
        "tier": "suggestion",
        "severity": "low",
        "type": "limitation",
        "subtype": null,
        "title": "Method's Issue calls rely on Workflows' fallback to the caller's Concorde",
        "description": "src/concorde/method/review_issues.py runs `concorde issues` through workflows.step.concorde_command, which falls back to `python -m concorde` of the caller's package (with PYTHONPATH pointed at it) when the worktree has neither .concorde/bin/concorde nor scripts/concorde.py. Task r3-workflows-issues-root removed that fallback from Workflows' own step launch (I-9c638fd93341516998d05f61e2f7c252) and kept concorde_command only as a thin wrapper for this Method caller.\n\nSuggested repair: Method resolves its own launcher for its Issue calls (and states in its Spec whether it may fall back to the running package, e.g. in an unbound checkout), so that the wrapper in workflows.step can go.",
        "impact": "No wrong behaviour is known today. Method depends on a Workflows helper whose fallback Workflows no longer uses itself, so the fallback has no owner promising it.",
        "basis": "Read in task r3-workflows-issues-root: src/concorde/method/review_issues.py imports concorde_command from concorde.workflows.step and duplicates the PYTHONPATH injection; src/concorde/workflows/step.py keeps concorde_command as a wrapper of workspace_concorde with the old fallback, documented as kept for this caller.",
        "owner_target_id": "module.method",
        "evidence": [
          {
            "path": "src/concorde/method/review_issues.py",
            "description": "imports and uses workflows.step.concorde_command"
          },
          {
            "path": "src/concorde/workflows/step.py",
            "description": "concorde_command kept as a wrapper for Method"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-6a38c385-dbb0-4deb-8ccf-42172d5f920d",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.method",
        "context_id": "sha256:780ba259e3211f0ce9ffcf3f4ad5150ddade3f8f7758e8affa2950087a52c2ee",
        "change_id": "r3-workflows-issues-root",
        "head": "6906d624784b7bafd4f999c28e60cf965935811a"
      }
    }
  ],
  "dispositions": []
}
```
