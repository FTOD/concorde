# I-4abca839abf758ada2708cd1613dffa3

```json
{
  "schema_version": 4,
  "id": "I-4abca839abf758ada2708cd1613dffa3",
  "status": "open",
  "reports": [
    {
      "id": "sha256:acdfb868a1718069776cf34090f66364f75484d1304fe8f0fa4b14a7e4f4a982",
      "created_at": "2026-10-06T19:50:51.267613+00:00",
      "report": {
        "report_key": "code-review/module.project-review/5",
        "tier": "obvious-fix",
        "severity": "high",
        "type": "gap",
        "subtype": "implementation-spec-mismatch",
        "title": "A check-execution failure hides a later Issue-store refusal",
        "description": "The deterministic step retains only its first failure. An Issue-system refusal is dropped from the result's error chain if checks already failed to run.\n\nSuggested repair: Retain all deterministic failures, or combine them into a stop with both causes, and include each in the final error chain. Add a regression with simultaneous check-execution and Issue-store failures.",
        "impact": "When checks cannot run and a subsequent coverage or unowned Issue write also fails, callers receive no Issue-store error chain and cannot see every failure they must repair.",
        "basis": "project_review run r-20261006T193742-project_review-4cbffb26 (module review) judged src/concorde/method/project_review/operation.py:558-560, src/concorde/method/project_review/operation.py:596-601, src/concorde/method/project_review/operation.py:1050-1051 against req.project-review.issue-failures and reported a violation: The check exception handler assigns state.deterministic_stop. When settle_and_report later returns an Issue-store refusal, operation.py:600 assigns 'state.deterministic_stop = state.deterministic_stop or stop', retaining only the check failure. derive_verdict adds just that single deterministic_stop to its error causes.",
        "owner_target_id": "module.project-review",
        "evidence": [
          {
            "path": "src/concorde/method/project_review/operation.py",
            "description": "lines 558-560, shown by the violation finding"
          },
          {
            "path": "src/concorde/method/project_review/operation.py",
            "description": "lines 596-601, shown by the violation finding"
          },
          {
            "path": "src/concorde/method/project_review/operation.py",
            "description": "lines 1050-1051, shown by the violation finding"
          },
          {
            "path": "specs/concorde/method/project-review/requirements.md",
            "description": "defines req.project-review.issue-failures, the finding's basis"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261006T193742-project_review-4cbffb26",
        "agent": "operation",
        "operation": "project_review",
        "phase": "code-review",
        "target_id": "module.project-review",
        "context_id": "sha256:b034ae5ba5ca8df96579c4ff52ba04aa5288b798fa8ae7fb5030c986d900b8d3",
        "change_id": "project-review",
        "head": "f2dc3642f7043679b5f21a6dce8503155a151042"
      }
    }
  ],
  "dispositions": []
}
```
