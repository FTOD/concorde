---
name: concorde-code-review
description: "Operation: independently review or diagnose a Module's granted implementation against its Spec and return scoped read-only findings."
operation: code_review
---

# concorde-code-review

@include prompts/workflow-host/invoke-operation-opener.md ACTION="review or diagnose the selected implementation against its Spec"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-code-review
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-code-review

The request requires task. A new task may supply target_id and focus_id (a scenario ID) as routing
hints, plus constraints. The router selects the owning Module. When resuming a bound review with
change_id, supply its target_id and current-worktree change_id. There is no review_mode selector;
use concorde-spec-review to review the specification itself. No positional task arguments or domain
flags are accepted.

@include prompts/workflow-host/main-may-inspect.md WORKERS="a fresh read-only code reviewer"

Review runs in the current worktree without creating a development change or requiring a preexisting
Issue. It reads the complete selected Module contract and only its admitted implementation files,
external references and scoped changes. Reviewers have no write, network or credential grants.
The host persists review reports separately from reviewer authority.

A managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.
Do not claim this compares against another branch or a merge base. Report the returned review
coverage, Issue judgments and limitations, preserving incomplete or failed outcomes. Findings do
not authorize repairs. describe-policy previews grants without launching agents or persisting
review results. A separate review intent cannot replace another task's required lifecycle review.
