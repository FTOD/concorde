# Spec review requirements

The Module-wide obligations of [Spec review](module.md). The headings group them by subject; each
requirement belongs to the [Module](../../glossary.json#concept.module) as a whole.

## Scope

### req.spec-review.never-edits — Review changes no file but its memory

Spec review SHALL NOT create, change or delete any file of the worktree it reviews other than the reviewed Modules' review memories and its own run's entries in the [run store](../../glossary.json#concept.run-store).

Only a Spec review in a bound workspace writes review memories; an
[unbound run](../../glossary.json#concept.unbound-run) reviews its
[unbound checkout](../../glossary.json#concept.unbound-checkout) and keeps its run store in the
worktree it started in.

### req.spec-review.memory — A repeated review builds on the memory

A Spec review in a bound workspace SHALL merge its findings into each reviewed Module's [review memory](../../glossary.json#concept.review-memory), keeping open every open earlier finding it neither updates nor resolves.

An earlier finding that is already resolved keeps its resolution and its reason.

### req.spec-review.review-spec-grant — Reviewers read under a review-spec grant

Every reviewer, checker and chair SHALL run under the `review-spec` grant of exactly one
reviewed Module, computed from the Specs of the worktree the run works on.

### req.spec-review.own-documents — Only the Module's own documents can block

A finding about a document the reviewed Module does not own SHALL NOT be `blocking`.

## Findings and verdict

### req.spec-review.one-pass — Every blocking finding in one pass

The Reviewer brief SHALL instruct a reviewer to report every blocking finding it can establish in
one run rather than stopping at the first.

### req.spec-review.unchanged-not-reviewed — Unchanged Specs are not reviewed again

A Spec review SHALL NOT launch a reviewer for a Module whose [context identity](../../glossary.json#concept.context-identity) is the one its review memory records as last reviewed, unless forced.

### req.spec-review.host-verdict — The Operation derives the verdict

The verdict of a [Spec](../../glossary.json#concept.spec) review or a Spec panel SHALL be
derived by the [Operation](../../glossary.json#concept.operation) by the rule of that Operation's
payload contract, never taken from a worker's statement.

### req.spec-review.no-structural-substitute — Structural errors stop a Module's review

The Operation SHALL NOT launch a reviewer for a Module whose Specs Spec core reports a structural
error for.

### req.spec-review.bound-verdict — The verdict names what was read

Every reviewed Module's outcome SHALL carry the context identity of the grant its reviewer read
under.

### req.spec-review.claims-stay-claims — Worker claims stay claims

The [run result](../../glossary.json#concept.run-result) SHALL keep reviewer findings and checker
statuses apart from the evidence the Operation produced itself.

## Panel

### req.spec-review.panel-accounted — A panel report accounts for every reviewer finding

A Spec panel SHALL NOT complete a Module whose
panel report does not account for every reviewer
finding exactly once or names a label no reviewer finding has.

The [accounting](panel.md#the-panel-graph) rule says how a report accounts for a finding.

### req.spec-review.panel-independent — Panel reviewers review independently

A panel reviewer's brief SHALL NOT contain another reviewer's findings.
