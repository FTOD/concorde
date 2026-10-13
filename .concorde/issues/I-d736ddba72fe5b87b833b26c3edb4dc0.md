# I-d736ddba72fe5b87b833b26c3edb4dc0

```json
{
  "schema_version": 4,
  "id": "I-d736ddba72fe5b87b833b26c3edb4dc0",
  "status": "open",
  "reports": [
    {
      "id": "sha256:8d05b1d80f8eb23cf2effba1b71e0ce97275ac402bad54285896dab2992c3f58",
      "created_at": "2026-10-13T20:02:06.692634+00:00",
      "report": {
        "report_key": "spec-panel/module.task-session/1",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Explain the failed-launch exception to safe session retries",
        "description": "The entry presents one-working-session protection and safe retry without explaining the contract's explicit exception for an unrecorded background job after session_failed.\n\nSuggested repair: Explain the unrecorded-launch hazard beside the retry instructions and in the one-working requirement's explanation. Tell callers to inspect claude agents --json --all for task-<task-id> and stop any surviving job before retrying. Preserve the requirement's recorded-session scope unless a stronger guarantee is explicitly approved.",
        "impact": "A caller can retry a failed launch under the entry's assurance and start a second writer in the same worktree; ordinary task cleanup cannot discover the unrecorded session.",
        "basis": "project_review run r-20261013T165054-project_review-b4db00b2 judged specs/concorde/coordination/task-session/module.md at starting-a-session, line 229 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: module.md says, \"One task worktree has one working task session at a time\" and promises refusal for a retry whose answer was lost. contracts.md:198 says, \"A launch that failed this way may still have started a background job that no node records, and so no later start sees\".\n\nThe panel's chair merged r1.1 and verified: Verified the entry, session_failed contract, and req.task-session.one-working. The requirement actually limits refusal to recorded sessions, so the finding concerns the entry's broader assurance and missing recovery instructions, not an unconditional requirement. Medium because this occurs on a failed-launch edge case; preferred-fix because explaining the existing limitation avoids changing the contract.",
        "owner_target_id": "module.task-session",
        "evidence": [
          {
            "path": "specs/concorde/coordination/task-session/module.md",
            "description": "starting-a-session, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261013T165054-project_review-b4db00b2",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.task-session",
        "context_id": "sha256:7f597ae0a2df2b7b10d6f0d7a9874c2693d554ab0bb52f17b9454a308822c491",
        "change_id": null,
        "head": "5c6e630a5dab6d5d4656f12198c1cc2289a1f99e",
        "phase": "spec-panel"
      }
    }
  ],
  "dispositions": []
}
```
