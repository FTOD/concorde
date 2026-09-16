---
name: concorde-issues
description: "Inspect, report, reopen or solve branch-local Issues; solving stops at a verified candidate without automatic delivery."
capability: issues
---

# concorde-issues

@include prompts/workflow-host/invoke-capability-opener.md ACTION="manage or solve explicitly selected Issues"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-issues
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-issues

Choose action list, show, report, reopen or solve. Show, reopen and solve require one issue_id;
expected_revision optionally rejects a changed selection. Report requires target_id and a classified
report; an append also names its issue_id and expected_revision inside the report. Reopen requires
a note. Only solve starts development; other actions are current-worktree bookkeeping. An Issue is
not an implementation task, and reporting it neither stops a running agent nor approves a repair.

Solve may use ordinary development, a fresh Spec repair, or Issue-specific read-only verification.
It can resolve, identify a duplicate or reject a mistaken report from evidence without mandatory
human approval. Unresolved product/design choices are returned as needs-decision. Respect the host's
bounded iteration limit and distinct execution failures. Do not retry by widening permissions.

A source-worktree handoff carries the selected Issue's exact bytes, including an uncommitted report,
without copying unrelated edits. Resume in the host-created worktree using its own fresh session.
A successful solve ends at ready with the disposition included in verification. It does not deliver,
merge primary or claim another branch is fixed. Closed Issues remain recorded. Legacy Reflections
are archived history, never automatically converted or used as current approval.
