# Decision log: operations-briefs-outcomes

Goal: Developer-approved panel-review decisions for Understanding, Implementation and Code review: (understanding F10) the understand Operation also fails extra or duplicate modules entries, with a test; (understanding F2) define sufficiency for a change goal as: the existing Specs state every promise the change relies on and say where its new promises belong, so the change can be planned (new promises become the plan's specify steps; a gap is a relied-on promise the Specs do not state), in the contract semantics, Usage and prompts/workers/understand.md; (implementation F17) the implement and test briefs also carry the workspace's goal as context, as specify does (--goal stays implement's task, --focus narrows test); remove the unreachable not_started outcome from code_review's and implement's contracts and code (contract version bumps, CHECK_SCHEMA/OUTCOMES). Specs, prompts and tests.

## Decisions (task session, 2026-09-29)

- **Understanding contract version bumped 2 → 3.** Options: keep version 2 (schema unchanged) or
  bump. Chose bump: the semantics changed (sufficiency for a change goal; exactly one `modules`
  entry per bound Module and none for another), so accepted assessments differ. Also fixed the
  stale contract path in the code comment.
- **Where a new promise belongs, when no bound Module's Spec says so, is reported as a Spec gap.**
  Options: leave it undefined, or treat it as a relied-on promise the Specs do not state. Chose
  the latter because the host requires gaps exactly when insufficient; an insufficient assessment
  with no gap would fail `inconsistent_assessment`. Stated in Usage, the contract semantics and
  the understand prompt.
- **Glossary `concept.spec-gap` and `req.understanding.gaps-reported` changed "needs" to "relies
  on"**, with a note that a new promise of a change goal is not a gap, so the definition agrees
  with the new sufficiency rule. Both are owned by module.understanding.
- **Workspace's goal heading in the implement and test briefs.** Named "The workspace's goal"
  (glossary term `workspace` has the goal) instead of specify's "The task's own goal", since
  Execution knows nothing of tasks; the implement and test prompts explain it is context only.
- **`OUTCOMES[...]` indexed strictly** in both check projections instead of `.get(..., "failed")`,
  since Check execution's statuses are exactly passed, failed and timeout; an unknown status now
  raises rather than being silently mislabelled.
- Extra/duplicate-entry test is tagged `scenario.understanding.inconsistent` (no new scenario:
  the scenario already covers "one of the consistency rules").
- Non-ok results: `uvx ruff` initially failed on the sandbox's read-only `~/.local/share/uv`;
  reran with `UV_TOOL_DIR` under `$TMPDIR`. `ruff check` reports pre-existing import-order and
  unused-variable findings in the touched files, not introduced here; left as is (outside goal).

## Closed: merged, 2026-09-28T17:34:26Z
