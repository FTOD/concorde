---
name: concorde-review
description: "Global review: route a standalone Spec review, code review or source diagnosis to its owning Module and return scoped, read-only findings."
capability: review
---

# concorde-review

@include prompts/workflow-host/invoke-capability-opener.md ACTION="review the selected Spec or implementation"

@include prompts/workflow-host/stdin-invocation-open.md NAME=concorde-review
@include prompts/workflow-host/stdin-invocation-config-input.md NAME=concorde-review

The request requires task and review_mode (spec or code). Use code for code review or source
diagnosis, and spec for contract review. A new task may supply target_id and focus_id (a scenario
ID) as routing hints, plus constraints. The coordinator selects the owning Module. When resuming
a bound review with change_id, supply its target_id and current-worktree change_id.
No positional task arguments or domain flags are accepted.

@include prompts/workflow-host/main-may-inspect.md WORKERS="a fresh read-only reviewer"

Review runs in the current worktree without creating a development change or requiring a
Reflection. Spec review reads the complete selected Module contract; code review also reads only
its admitted implementation files and scoped changes. Reviewers have no write, network or
credential grants. The host persists review reports separately from reviewer authority.

A managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.
Do not claim this compares against another branch or a merge base. Report the returned review
coverage, findings, gaps and limitations, preserving incomplete or failed outcomes. Findings do
not authorize repairs. describe-policy previews grants without launching agents or persisting
review results. A separate review intent cannot replace another task's required lifecycle review.
