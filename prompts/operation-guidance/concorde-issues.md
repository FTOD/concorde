---
name: concorde-issues
description: "Host bookkeeping or native solve workflow: inspect, report, reopen or assess branch-local Issues; return needed repairs to the caller or verify current work without automatic delivery."
operation: issues
---

# concorde-issues

@prompts/workflow-host/invoke-operation-opener.md ACTION="manage or solve explicitly selected Issues"

Choose action list, show, report, reopen or solve. Show, reopen and solve require one issue_id;
expected_revision optionally rejects a changed selection. Report requires target_id and a classified
report; an append also names its issue_id and expected_revision inside the report. Reopen requires
a note. Only solve starts the bounded decision and verification lifecycle; other actions are
current-worktree bookkeeping. An Issue is not an implementation task, and reporting it neither
stops a running agent nor approves a repair.

Solve returns needed implementation or Spec repair to the calling agent with the selected target,
intended behavior and rationale. It does not author Specs, change implementation or start planning
or child development. The caller performs authorized Spec, paired metadata and registry edits or
selects the supported planning/implementation capabilities explicitly, then requests fresh verification with current inputs.
A return-to-caller result preserves the open Issue and is not completed repair or readiness.
Solve can run Issue-specific read-only verification, resolve, identify a duplicate or reject a
mistaken report from evidence without mandatory human approval. Unresolved product/design choices
are returned as needs-decision. Respect the host's bounded iteration limit and distinct execution
failures. Do not retry by widening permissions.

From the primary worktree the host copies the selected Issue's exact bytes, including an uncommitted
report, into the candidate worktree it creates, without copying unrelated edits, and solves there;
this session receives the candidate's result and continues the change with its change_id.
A successful solve ends at ready with the disposition included in verification. It does not deliver,
merge primary or claim another branch is fixed. Closed Issues remain recorded. Legacy Reflections
are archived history, never automatically converted or used as current approval.

## Native solve invocation

List/show/report/reopen finish as finite Host calls. Solve action run prepares an exact named
`concorde.issue.<ticket>` native workflow. Invoke its returned `call` with subagent unchanged, then
poll concorde-issues action result. The workflow uses fresh terminal Issue decisions and flattened
independent Issue-specific/ordinary reviewers; Host services own attempts, currentness, closure
journal/recovery and separate final validation. There is no nested workflow, coordinator model or
legacy Graph/RPC fallback. Accepted failed/conflicting/unsupported results are not ready candidates;
stage-only gates and native terminal success alone never authorize disposition or delivery.
