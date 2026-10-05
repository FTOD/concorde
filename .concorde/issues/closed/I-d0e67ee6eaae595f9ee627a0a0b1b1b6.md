# I-d0e67ee6eaae595f9ee627a0a0b1b1b6

```json
{
  "schema_version": 4,
  "id": "I-d0e67ee6eaae595f9ee627a0a0b1b1b6",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:941e84da4788fea07a89ff0c33c2710d167f070f400839cbab1479802c83a420",
      "created_at": "2026-10-04T09:43:34.400439+00:00",
      "report": {
        "title": "A task wait can miss a close that happens just after it starts",
        "type": "bug",
        "owner_target_id": "module.tasks",
        "report_key": "task-wait-missed-close",
        "tier": "decision-needed",
        "severity": "medium",
        "subtype": null,
        "description": "tests/concorde/tasks/test_wait.py::WaitTests::test_a_task_that_ended_elsewhere_ends_the_wait failed once in a full parallel suite run (`.venv/bin/python -m pytest -q`, 16 workers, 2026-10-04, task restyle-coordination) with `AssertionError: 'wait_unreachable' != 'wait_timeout'`. The test closes the task 0.3 s after starting `concorde task wait t1 --until delivered --timeout 30`, so the wait ran its whole 30 s without noticing the close. Run alone three times right after, it passed each time.",
        "impact": "If the cause is in the wait rather than the test, a `concorde task wait --until` started just before the task ends can miss the end and block until its timeout, or for ever without one. A session waiting in background Bash would then never be woken for that task.",
        "basis": "The task's change touches only Markdown and guidance test strings, which this test does not read. A 30 s timeout is far beyond any load delay for a close made 0.3 s later, which suggests a lost wake-up, such as the close landing between the wait's first read of the state and the start of its watch on the lock or the record. This is not established, so the fix is uncertain.",
        "evidence": [
          {
            "path": "tests/concorde/tasks/test_wait.py",
            "description": "test_a_task_that_ended_elsewhere_ends_the_wait: closes the task 0.3 s after a --until delivered wait with --timeout 30 and expects wait_unreachable"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-9b0fb4e1-dc24-4574-b401-83a70839ecbc",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.tasks",
        "context_id": "sha256:6f38070545b3d2a852c73beb9aa15f865ddaf138dfcdd06c23d0ea55c4a7bc01",
        "change_id": "restyle-coordination",
        "head": "002084c07c804a4fa7df93adf57f26c28740c93c"
      }
    },
    {
      "id": "sha256:7ba765d28fb899129046e2e5135467705e337a6725d61418a0d3d5c291ccca37",
      "created_at": "2026-10-05T03:56:57.446478+00:00",
      "report": {
        "issue_id": "I-d0e67ee6eaae595f9ee627a0a0b1b1b6",
        "expected_revision": "sha256:a9c3e1c35c8b3a9f81a8173720a331404bd69df0a42afeff9a74fc5c304bec3c",
        "report_key": "task-close-races-status-reader",
        "type": "bug",
        "subtype": null,
        "tier": "obvious-fix",
        "severity": "high",
        "owner_target_id": "module.tasks",
        "title": "A reader's plain git status in a task worktree makes a concurrent task close fail with worktree_failed",
        "description": "Investigation on main 6f3b8fbd (2026-10-05) found no lost wake-up in the wait. src/concorde/coordination/tasks/wait.py:106-130 creates its inotify watch before its first state read, and every interleaving re-reads the state after the lock is released. The actual cause is this. When the close takes the workspace lock, the waiter wakes and computes derived_state. derived_state runs store._changes (src/concorde/coordination/tasks/store.py:1648-1664), which runs plain `git status` in the task worktree. Plain git status refreshes the index: it writes `.git/worktrees/<id>/index.lock` and renames it over the index. The close runs `git worktree remove` under its locks at the same moment. Git then fails with `error: failed to delete '.git/worktrees/t1': Directory not empty` (exit 255), and _close_held raises worktree_failed before it updates the record. The working tree is removed but the record stays open, so the wait correctly keeps waiting until its timeout. In the test, the close's exception dies in the threading.Timer thread (tests/concorde/tasks/test_wait.py:48-51, 76-84), which hides the real failure behind `'wait_unreachable' != 'wait_timeout'`.",
        "impact": "Any reader that computes derived_state during a close can make the close or merge of a task fail and leave its worktree half removed while its record says open. Such readers include `task show`, `task list`, a `task wait` and the MCP register_wait thread. It also breaks req.tasks.wait-bounded, whose wait must end 'without changing anything', because the wait rewrites the worktree index.",
        "basis": "This was reproduced with scratch harnesses under xdist -n 16 on git 2.43.0. With the exact test scenario and the close's exceptions captured, 1 of 64 runs and 3 of 300 runs failed, each a wait_timeout with the close failing worktree_failed. With `git status` looping in the worktree during close_task, 5 of 61 and 14 of 201 closes failed. With GIT_OPTIONAL_LOCKS=0, both harnesses showed 0 of 300 and 0 of 201. After a tracked file was touched, plain git status replaced the worktree index inode, and `--no-optional-locks` left it unchanged. The fix is obvious: run `git --no-optional-locks status` in store._changes and deliver._special (deliver.py:282), as the read-only status calls in audit.py:31, placement.py:41, idle.py:55, checkout.py:55, issues/store.py:639 and both review operations already do. Add a deterministic test that store._changes leaves the index inode unchanged and creates no index.lock. Also make test_wait's delayed close record its exception and assert that the close succeeded.",
        "evidence": [
          {
            "path": "src/concorde/coordination/tasks/store.py",
            "description": "_changes runs plain git status (around line 1655), the index-writing reader; _close_held raises worktree_failed before update()"
          },
          {
            "path": "src/concorde/coordination/tasks/wait.py",
            "description": "wait_task: watch created before the first read; no lost wake-up"
          },
          {
            "path": "tests/concorde/tasks/test_wait.py",
            "description": "delayed close in a Timer thread swallows the close's exception"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-1a41dad9-6fb4-4e80-8bc9-25bfd441322a",
        "agent": "main-agent",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.tasks",
        "context_id": "sha256:6f38070545b3d2a852c73beb9aa15f865ddaf138dfcdd06c23d0ea55c4a7bc01",
        "change_id": null,
        "head": "6f3b8fbdf650f633a5577a00437b62346636797f"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "resolved",
      "note": "Fixed by task fix-status-locks, merged into the primary branch at 463dd137d5b63fdfe1636bd910ac8deea6a2b687.",
      "evidence": [
        "merge commit 463dd137d5b63fdfe1636bd910ac8deea6a2b687",
        "task fix-status-locks"
      ],
      "duplicate_of": null,
      "actor": "main-agent",
      "created_at": "2026-10-05T04:48:08.549198+00:00"
    }
  ]
}
```
