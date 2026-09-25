# Spec review requirements

The Module-wide obligations of [Spec review](module.md). The headings group them by subject; each
requirement belongs to the Module as a whole.

## Scope

### req.spec-review.never-edits — Review changes no file but its memory

Spec review SHALL NOT create, change or delete any file of the task worktree other than the reviewed Modules' review memories.

### req.spec-review.memory — A repeated review builds on the memory

A Spec review inside a task SHALL merge its findings into each reviewed Module's review memory, keeping every earlier finding it does not update or resolve open.

### req.spec-review.review-spec-grant — Reviewers read under a review-spec grant

Every reviewer and checker SHALL run under the `review-spec` grant of exactly one reviewed Module,
computed from the task worktree's Specs.

### req.spec-review.own-documents — Only the Module's own documents can block

A finding about a document the reviewed Module does not own SHALL NOT be `blocking`.

## Findings and verdict

### req.spec-review.one-pass — Every blocking finding in one pass

The Reviewer brief SHALL instruct a reviewer to report every blocking finding it can establish in
one run rather than stopping at the first.

### req.spec-review.host-verdict — The host derives the verdict

The verdict SHALL be derived by the host from the Modules' outcomes by the rule of the review
payload contract, a Module's outcome from every open finding of its review memory, never taken
from a worker's statement.

### req.spec-review.no-structural-substitute — Structural errors stop a Module's review

The host SHALL NOT launch a reviewer for a Module whose Specs Spec core reports a structural error
for.

### req.spec-review.bound-verdict — The verdict names what was read

Every reviewed Module's outcome SHALL carry the context identity of the grant its reviewer read
under.

### req.spec-review.claims-stay-claims — Worker claims stay claims

The Operation result SHALL keep reviewer findings and checker statuses apart from the evidence the
host produced itself.
