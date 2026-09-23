---
name: concorde-spec-review
description: "Workflow: independently review a Module's complete Spec, including terminology semantic consistency, and return scoped read-only findings."
operation: spec_review
---

# concorde-spec-review

@prompts/workflow-host/invoke-operation-opener.md ACTION="review the selected Spec, including terminology semantic consistency"

The request requires target_id and task. The calling agent selects the Module explicitly;
optional focus_id must name its scenario. Constraints and a current-worktree change_id may be
supplied. There is no implicit routing. The host deterministically checks
the target and freezes its complete context before starting a fresh read-only reviewer.

Review runs in the current worktree without creating a development change or requiring a preexisting
Issue. It reads the Module's complete Spec context, its own documents and those its `contains`,
`uses` and `includes` select (reading and metadata), but no implementation. Import rows are
link-only; it checks every local explanation of an imported term in that collection against the
owner's canonical definition for semantic consistency; wording need not match. Report coverage
and unresolved comparisons rather than assuming consistency. Reviewers have no write, network or
credential grants. The host persists review reports separately from reviewer authority.

A managed change uses its recorded base commit for the diff; an unmanaged Git checkout uses HEAD.
Do not claim this compares against another branch or a merge base. Report the returned review
coverage, Issue judgments and limitations, preserving incomplete or failed outcomes. Findings do
not authorize repairs. describe-policy previews grants without launching agents or persisting
review results. A separate review intent cannot replace another task's required lifecycle review.

## Native execution

Run prepares an exact named async native review workflow. Invoke returned `call` unchanged, then
poll this same capability with action `result`. Only full independently admitted scope can be accepted;
native success/staging alone is not accepted review. Each reviewer has fresh separate context.
The workflow uses two fixed Host steps regardless of reviewer count; native budgets remain enforced.
No public Graph/Pi-RPC fallback or automatic downstream readiness/integration occurs.
