# I-d0e67ee6eaae595f9ee627a0a0b1b1b6

```json
{
  "schema_version": 4,
  "id": "I-d0e67ee6eaae595f9ee627a0a0b1b1b6",
  "status": "open",
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
    }
  ],
  "dispositions": []
}
```
