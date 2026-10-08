# I-07da60bcefbf5cb0847d191cda399be1

```json
{
  "schema_version": 4,
  "id": "I-07da60bcefbf5cb0847d191cda399be1",
  "status": "open",
  "reports": [
    {
      "id": "sha256:dfdbf486c0a5ecb6da73ebe6ce95067e14b1f180320413fcac51f4d07a1a21ab",
      "created_at": "2026-10-08T04:09:48.112766+00:00",
      "report": {
        "report_key": "code-review/module.task-session/3",
        "tier": "preferred-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Test closed-task and fail-closed write-hook behavior",
        "description": "Boundary tests do not exercise decision-log writes after the task folder has moved or failures while interpreting hook input.\n\nSuggested repair: Test a saved generated hook after the task folder is moved, asserting a denial naming the closed task and no folder recreation. Also send malformed input through the hook entry point and assert a deny decision.",
        "impact": "The guarantee that a stale session cannot recreate a closed task's decision log, and the hook's fail-closed behavior, have no regression coverage.",
        "basis": "project_review run r-20261008T024839-project_review-a7857ff6 (module review) judged tests/concorde/tasks/test_session.py:335-367, src/concorde/coordination/tasks/session_hook.py:34-40, src/concorde/coordination/tasks/session_hook.py:48-52 against specs/concorde/coordination/task-session/contracts.md#task-session-settings and reported a missing-test: The settings contract explicitly requires denial of a decision-log write after its task folder moves to history and says 'Any failure denies.' The boundary test exercises an existing decision log and inside/outside symlinks, but never removes the task folder or supplies malformed hook input.",
        "owner_target_id": "module.task-session",
        "evidence": [
          {
            "path": "tests/concorde/tasks/test_session.py",
            "description": "lines 335-367, shown by the missing-test finding"
          },
          {
            "path": "src/concorde/coordination/tasks/session_hook.py",
            "description": "lines 34-40, shown by the missing-test finding"
          },
          {
            "path": "src/concorde/coordination/tasks/session_hook.py",
            "description": "lines 48-52, shown by the missing-test finding"
          },
          {
            "path": "specs/concorde/coordination/task-session/contracts.md",
            "description": "defines specs/concorde/coordination/task-session/contracts.md#task-session-settings, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T024839-project_review-a7857ff6",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.task-session",
        "context_id": "sha256:890863ee44b220167ff4778ecf90df850af1bbfeaad300511e8bf57ad06b1a29",
        "change_id": null,
        "head": "a5d10ce4554159cc1f8ca09d5a84e182608a6036",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
