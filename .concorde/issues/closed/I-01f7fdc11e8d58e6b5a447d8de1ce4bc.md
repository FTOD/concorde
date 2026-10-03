# I-01f7fdc11e8d58e6b5a447d8de1ce4bc

```json
{
  "schema_version": 4,
  "id": "I-01f7fdc11e8d58e6b5a447d8de1ce4bc",
  "status": "closed",
  "reports": [
    {
      "id": "sha256:142b5053419f4a3b4d5848e3c5e1a151be01023e1fac4274838903bb3fe09cf7",
      "created_at": "2026-10-03T07:55:01.097008+00:00",
      "report": {
        "report_key": "module.execution/3",
        "tier": "decision-needed",
        "severity": "medium",
        "type": "bug",
        "subtype": null,
        "title": "Invalid-result recovery can reproduce the invalid error",
        "description": "Invalid-result recovery unconditionally preserves the earlier error as a structured cause even when that error caused validation to fail. Changing status and output cannot repair that malformed nested error.\n\nSuggested repair: Construct a fresh valid failure envelope. Preserve the earlier error as a cause only if it satisfies the error contract; preserve rejected values as diagnostic artifacts with validation locations instead. State this exception to unchanged-cause preservation and require validation of the replacement result.",
        "impact": "When the original error is malformed, following the prescribed recovery embeds the invalid value again and cannot produce the promised contract-valid failure result.",
        "basis": "spec_panel run r-20261003T074406-spec_panel-0a7388d8 judged specs/concorde/execution/runner.md at Composing the result, line 227 by the obligations criterion of the Protocol's Evaluating a Spec; the Specs read: \"A result or an `ok` output that breaks its contract becomes `failed` with output null and the runner's `invalid_result` link, its earlier error as the cause.\" The Errors table likewise retains \"the error the run had, if any\". contract.execution.run-result recursively checks every causes element against the same closed error schema.\n\nThe panel's chair merged r2.3, r3.1 and verified: Verified both recovery statements against the recursive error schema and unchanged-causes semantics. Medium because this is an invalid-provider-result edge case. Decision-needed because the repair must settle how the unconditional cause-preservation promise applies to rejected values.",
        "owner_target_id": "module.execution",
        "evidence": [
          {
            "path": "specs/concorde/execution/runner.md",
            "description": "Composing the result, cited by the obligations finding"
          }
        ]
      },
      "source": {
        "invocation_id": "r-20261003T074406-spec_panel-0a7388d8",
        "agent": "operation",
        "operation": "spec_panel",
        "phase": "report",
        "target_id": "module.execution",
        "context_id": "sha256:5f735f88697ff6604c75aad4f90ea8f92f999c62ddc37bcfd005c5444e51fcfb",
        "change_id": "parts-review-specs",
        "head": "959c856c3a7732af1420829a271f59dd21ba837c"
      }
    }
  ],
  "dispositions": [
    {
      "reason": "duplicate",
      "note": "Same root cause as I-2f6e: the invalid_result replacement keeps parts of the rejected result (here the earlier error as cause; there host_evidence and worker) and is not revalidated. runner.md 'Composing the result' ('its earlier error as the cause') and the Errors table row are identical on main, so pre-existing; the code (runner.py _envelope) keeps the earlier error only when it is a dict with 'level', so a malformed link with a level would survive. The repair of I-2f6e (build and validate a fresh failed envelope, keep invalid data only as diagnostic text) must also reword runner.md to keep the earlier error as cause only when it satisfies contract.tracing.error. Edge case reachable only through a step bug: medium at most, low in practice.",
      "evidence": [
        "specs/concorde/execution/runner.md#composing-the-result",
        "src/concorde/execution/runner.py",
        ".concorde/issues/I-2f6e27e808e5528ab8088fd1b667b3d9.md"
      ],
      "duplicate_of": "I-2f6e27e808e5528ab8088fd1b667b3d9",
      "actor": "task-session",
      "created_at": "2026-10-03T08:47:53.526186+00:00"
    }
  ]
}
```
