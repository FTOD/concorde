# I-09c7ff1ad6e15bff9b57c8ed0878c3fc

```json
{
  "schema_version": 4,
  "id": "I-09c7ff1ad6e15bff9b57c8ed0878c3fc",
  "status": "open",
  "reports": [
    {
      "id": "sha256:c43f34d99005e0616661cec8db54fdfe84b203bd7399fbd58acea5d865b51dd7",
      "created_at": "2026-10-08T09:04:32.138851+00:00",
      "report": {
        "report_key": "code-review/module.swe-bench-cases/4",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Timed-out grading runs lose their pytest log",
        "description": "Timeouts bypass the promised pytest log, retaining only short output tails in the exception. The command supplies a log path, but grade never writes it on this error path.\n\nSuggested repair: Persist the full captured stdout and stderr to the supplied log before propagating grade_timeout, and identify that log in the error. Extend the timeout test to pass a log path and verify retention of output longer than 3000 characters.",
        "impact": "A timed-out grading run leaves no log of its output, or leaves a previous run's log at the same path. Output beyond the retained tails is lost, making the failing case harder to diagnose.",
        "basis": "project_review run r-20261008T063808-project_review-9851e69f (module review) judged scripts/e2e/cases.py:249-269, scripts/e2e/e2e.py:654-665 against specs/concorde/e2e/cases/module.md#grading-a-case and reported a violation: The timeout handler raises grade_timeout with only `_text(error.stdout)[-3000:]` and `_text(error.stderr)[-3000:]`. Log creation and writing occur at lines 266-269, after that exception has propagated through finally, so they are never reached on timeout. The Spec says 'The pytest output is kept under `.concorde/runs/e2e/`' and requires timeout errors to include the test run's output.",
        "owner_target_id": "module.swe-bench-cases",
        "evidence": [
          {
            "path": "scripts/e2e/cases.py",
            "description": "lines 249-269, shown by the violation finding"
          },
          {
            "path": "scripts/e2e/e2e.py",
            "description": "lines 654-665, shown by the violation finding"
          },
          {
            "path": "specs/concorde/e2e/cases/module.md",
            "description": "defines specs/concorde/e2e/cases/module.md#grading-a-case, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261008T063808-project_review-9851e69f",
        "agent": "operation",
        "operation": "project_review",
        "target_id": "module.swe-bench-cases",
        "context_id": "sha256:3281dc02a6ab21d9180cb063c21ae6305d077f36282313a4896dc10cf590623a",
        "change_id": null,
        "head": "ce20cc74890dd20fae25a0a858f03eeb91514ac0",
        "phase": "code-review"
      }
    }
  ],
  "dispositions": []
}
```
