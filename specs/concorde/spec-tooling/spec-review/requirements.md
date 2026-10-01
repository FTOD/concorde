# Spec review requirements

The Module-wide obligations of [Spec review](module.md). The headings group them by subject; each
requirement belongs to the [Module](../../glossary.json#concept.module) as a whole.

## Scope

### req.spec-review.never-edits — Review changes no file of the reviewed worktree

Spec review SHALL NOT create, change or delete any file of the worktree it reviews other than its own run's entries in the [run store](../../glossary.json#concept.run-store).

Its [Issue](../../glossary.json#concept.issue) reports are written by the Issue store in the
primary worktree, whichever worktree the run reviews. An
[unbound run](../../glossary.json#concept.unbound-run) reviews its
[unbound checkout](../../glossary.json#concept.unbound-checkout) and keeps its run store in the
worktree it started in.

### req.spec-review.review-spec-grant — Reviewers read under a review-spec grant

Every reviewer and checker SHALL run under the `review-spec` grant of exactly one reviewed Module,
computed from the Specs of the worktree the run works on.

### req.spec-review.architect-grant — Architects read under a review-architecture grant

Every architect SHALL run under the `review-architecture` grant of exactly one reviewed Module,
computed from the Specs of the worktree the run works on.

An architect therefore reads every Module's Specs and the names of the project's code, never its
contents.

### req.spec-review.own-documents — Only the Module's own documents can block

A finding about a document the reviewed Module does not own SHALL NOT have a blocking
[tier](../../glossary.json#concept.issue-tier).

## Findings, Issues and verdict

### req.spec-review.one-pass — Every blocking finding in one pass

The Reviewer brief SHALL instruct every worker that judges a Module to report every blocking finding
it can establish in one run rather than stopping at the first.

### req.spec-review.earlier-issues — Workers receive the earlier Issues

Every worker of a Spec review or a Spec panel SHALL receive the reviewed Module's earlier Issues before it judges.

The [definition](operation.md#earlier-issues) says which Issues those are.

### req.spec-review.reports-issues — Every finding that stands becomes an Issue

The Operation SHALL report every finding its checker did not dispute, or its chair merged into the panel report, as an [Issue report](../../glossary.json#concept.issue-report) through the Issue store.

A worker never writes an Issue; the Operation reports in bound and unbound runs alike.

### req.spec-review.never-disposes — Review closes no Issue

Spec review SHALL NOT close or reopen an Issue.

The earlier Issues a review finds resolved are listed in its result for the task to close.

### req.spec-review.issue-failure-not-issue — A failing Issue system is not an Issue

Spec review SHALL NOT report a refusal of the Issue store as an Issue.

The refusal makes the Module's review `incomplete` and travels in the result's
[error chain](../../glossary.json#concept.error-chain).

### req.spec-review.host-verdict — The Operation derives the verdict

The verdict of a [Spec](../../glossary.json#concept.spec) review or a Spec panel SHALL be
derived by the [Operation](../../glossary.json#concept.operation) by the rule of that Operation's
payload contract, never taken from a worker's statement.

### req.spec-review.no-structural-substitute — Structural errors stop a Module's review

The Operation SHALL NOT launch a worker for a Module whose Specs Spec core reports a structural
error for.

### req.spec-review.bound-verdict — The verdict names what was read

Every reviewed Module's outcome SHALL carry the [context identity](../../glossary.json#concept.context-identity) of the grant its reviewers read
under.

### req.spec-review.claims-stay-claims — Worker claims stay claims

The [run result](../../glossary.json#concept.run-result) SHALL keep worker findings, severities, tiers,
checker statuses and resolutions apart from the evidence the Operation produced itself.

## Panel

### req.spec-review.panel-accounted — A panel report accounts for every worker finding

A Spec panel SHALL NOT complete a Module whose panel report does not account for every reviewer and
architect finding exactly once or names a label no such finding has.

The [accounting](panel.md#the-panel-graph) rule says how a report accounts for a finding.

### req.spec-review.panel-independent — Panel workers review independently

A panel reviewer's or architect's brief SHALL NOT contain another worker's findings.
