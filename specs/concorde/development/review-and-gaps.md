```concorde-document
{
  "id": "document.development.review-and-gaps",
  "owner": "module.development",
  "main_visible": true
}
```
# Attributed gaps and host history


Review owns [independent review and task relevance](../review/review.md).
Development Flow owns its [review ordering and repair](../dev-loop/development.md);
Specification Flow owns [Spec-only completion](../specify-loop/specify-loop.md).
This document owns common gap retention, provenance and explicit capture semantics.

Any necessary missing/ambiguous contract encountered during explanation, planning, task authoring or
implementation uses the same gap fields. Queries report gaps; development records and deduplicates
them by target/task/phase/question/blocked step/needed contract in the existing change state, with
Spec revision and observed contexts. Unrelated work cannot erase unresolved gaps. Retrying an unchanged
blocked step waits for its contract repair. After a Spec change, a fresh successful assessment resolves
that step's old gaps and retains history. Changed admitted review inputs, including reviewer
instructions, also permits fresh review without first erasing its old gaps. Only an accepted,
completed review without gaps or blocking findings resolves that phase's old gaps from a different
review input digest; failed or incomplete reassessment leaves them open, and a repeated gap records
its new observation and review input digest on that gap's own history entry. Lifecycle status,
snapshot context IDs and replacement of the latest review record do not change that identity.
An unchanged-input standalone review may report its own findings but cannot resolve the required
gap. Legacy gap entries without a recorded review input digest retain their Spec-revision gate;
the Host does not infer their original identity from a mutable latest-review record. Unchanged
review inputs still wait, and other phases' prerequisite gaps remain gates.
Spec authoring can itself supply the repair. A durable gap
can be discovered through reflections-triage `status` gap_records and explicitly captured by
`record-gaps` using those returned IDs; capture does not resolve the gap,
change its owner, approve a fix or start implementation.

Review results are invalidated by changed relevant Spec, registered code, task/focus/constraints,
configuration, role instructions or host review runtime, candidate HEAD/base/change identity, or
scoped patches. Required evidence is rechecked at readiness/delivery, using the same worktree
lifecycle. A failed process or incomplete review never becomes an empty successful review.

Read-only reflection investigation receives the selected Module contract and explicitly granted
code files. It receives no write permission for those files.
Code-writing tasks separately receive the Module's own listed implementation entries, with write
authority limited to exactly those paths: an exact file, or the whole directory a directory prefix
names, so a new file below it needs no separate declaration.

The review input identity includes `review_mode` and the selected reviewer worker's Agent binding
digest. Changes to that worker's task contract, common or selected instructions, authority ceiling
or recorded build invalidate review evidence. Sharing a definition with an author does not admit
the author conversation or artifacts.

Canonical interface edits invalidate review for the owner and each old/candidate context consumer,
including those that reference the whole provider Module. Each reviewer retains foreign definition
ownership and assesses local reliance/obligations. Repairing that definition belongs to its sole
owner; inclusion grants no write permission or provider code. Reference-only changes also require
fresh evidence even when the complete file set is unchanged.
