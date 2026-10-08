# I-5df335beaacb58178eeab2f6a387f41d

```json
{
  "schema_version": 4,
  "id": "I-5df335beaacb58178eeab2f6a387f41d",
  "status": "open",
  "reports": [
    {
      "id": "sha256:876f3dd57c4ff6e4db08fcb58e0f24643a7706632aaec549212403bd8f1ce91e",
      "created_at": "2026-10-08T14:16:25.098311+00:00",
      "report": {
        "report_key": "task-session/r2-distribution/execution-flaky-merge-wait-test",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Runner test removes its project while the detached run still writes",
        "description": "tests/concorde/execution/test_runner.py::RunnerTests::test_a_run_waiting_behind_a_merge_names_the_merge starts a detached task-validation run and returns once that run's result.json exists. The runner process can still write under the temporary project's .concorde (progress file, lock, trace) after the result appears. The test's TemporaryDirectory cleanup then races it and fails with OSError: [Errno 39] Directory not empty: '.concorde'.\n\nSuggested repair: before the test ends, wait for the detached runner to end, for example until its run lock is released or its process has exited, then let the cleanup run.",
        "impact": "check.execution.tests fails at random, which blocks a delivery or task-validation that is otherwise ready; the delivery of task r2-distribution was refused once by it.",
        "basis": "Seen in delivery run r-20261008T140441-delivery-5821b502 of task r2-distribution: check.execution.tests failed with 1 failed, 69 passed, the traceback ending in tempfile cleanup at shutil.rmtree on /tmp/.../project/.concorde. The same test passed in the full suite and in task-validation r-20261008T135335-task_validation-3d02c3b7 on the same input, and in 6 isolated reruns. The test (lines 1071-1089) awaits only the result file of the detached run, never the runner's end.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "tests/concorde/execution/test_runner.py",
            "description": "test_a_run_waiting_behind_a_merge_names_the_merge, lines 1044-1089: waits for the result file only"
          }
        ]
      },
      "source": {
        "invocation_id": "cli-db5cabfd-8d8a-4689-9d18-17587573d1c5",
        "agent": "task-session",
        "operation": "issues",
        "phase": "report",
        "target_id": "module.execution",
        "context_id": "sha256:33fa611a86ddb26bb34f49dbad9519ffdaa60d86d7a93d3ef0264c6db36ccd5f",
        "change_id": "r2-distribution",
        "head": "e325b5615a4ad22fdbd85286c8ea3c89d899e8fd"
      }
    }
  ],
  "dispositions": []
}
```
