---
name: concorde-code-review
description: "Operation: independently review or diagnose a Module's granted implementation against its Spec and return scoped read-only findings."
operation: code_review
---

# concorde-code-review

@prompts/workflow-host/invoke-operation-opener.md ACTION="review or diagnose the selected implementation against its Spec"

The request requires target_id and task. The calling agent selects the Module explicitly;
optional focus_id must name its scenario. Constraints and a current-worktree change_id may be
supplied. There is no implicit routing or review_mode selector. The host deterministically checks
the target and freezes its complete context before starting a fresh read-only reviewer.

Review runs in the current worktree without creating a development change or requiring a preexisting
Issue. It reads the complete selected Module contract and only its admitted implementation files,
external references and scoped changes. Reviewers have no write, network or credential grants.
The host persists review reports separately from reviewer authority.

A managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.
Do not claim this compares against another branch or a merge base. Report the returned review
coverage, Issue judgments and limitations, preserving incomplete or failed outcomes. Findings do
not authorize repairs. describe-policy previews grants without launching agents or persisting
review results. A separate review intent cannot replace another task's required lifecycle review.
