# I-0a6d5b689aef5d1abc81d6ce318f05cb

```json
{
  "schema_version": 4,
  "id": "I-0a6d5b689aef5d1abc81d6ce318f05cb",
  "status": "open",
  "reports": [
    {
      "id": "sha256:b26a2827f4c506348ed245533a192efd7eb6a82fada615f2ee70aa6334bb6c25",
      "created_at": "2026-10-03T04:30:55.352338+00:00",
      "report": {
        "report_key": "module.checks/9",
        "tier": "obvious-fix",
        "severity": "medium",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "Relative trace directories produce nonconforming relative log paths",
        "description": "Returned log paths remain relative when the caller supplies a relative trace directory, although the result contract requires absolute paths.\n\nSuggested repair: Normalize the caller's trace directory to an absolute path at admission and use it consistently for nodes and returned logs. Test a relative trace_directory.",
        "impact": "Consumers operating from another working directory cannot reliably open the returned log or construct the promised failure evidence.",
        "basis": "code_review run r-20261003T041234-code_review-72e86ad6 (module review) judged src/concorde/execution/checks/checks.py:539-540, src/concorde/execution/checks/checks.py:573-574, src/concorde/execution/checks/checks.py:632-639 against specs/concorde/execution/checks/service.md#check-result and reported a violation: The Check result table defines log as 'The absolute path of the check node’s output.log'. run_checks applies only Path(trace_directory), layout.check_folder preserves that path, and the result uses '\"log\": log.as_posix()'. A relative trace_directory therefore produces a relative log path.",
        "owner_target_id": "module.checks",
        "evidence": [
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "lines 539-540, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "lines 573-574, shown by the violation finding"
          },
          {
            "path": "src/concorde/execution/checks/checks.py",
            "description": "lines 632-639, shown by the violation finding"
          },
          {
            "path": "specs/concorde/execution/checks/service.md",
            "description": "defines specs/concorde/execution/checks/service.md#check-result, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T041234-code_review-72e86ad6",
        "agent": "operation",
        "operation": "code_review",
        "phase": "report",
        "target_id": "module.checks",
        "context_id": "sha256:77e099b4ca7b15a1f207f7287da98dd30de50d893652c99a76bfca00e46658c3",
        "change_id": "parts-review",
        "head": "43871f64ab7162b4b32fd566e2f81ec15aba06d2"
      }
    }
  ],
  "dispositions": []
}
```
