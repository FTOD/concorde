# Spec review requirements

The Module-wide obligations of [Spec review](module.md). The headings group them by subject. Each
requirement belongs to the [Module](../../glossary.json#concept.module) as a whole.

## Scope

### req.spec-review.never-edits — Review changes no file of the reviewed worktree

Except for its own run's entries in the [run store](../../glossary.json#concept.run-store), Spec
review SHALL NOT create, change or delete any file of the worktree it reviews.

Whichever worktree the run reviews, the Issue store writes Spec review's
[Issue](../../glossary.json#concept.issue) reports in the primary worktree. An
[unbound run](../../glossary.json#concept.unbound-run) reviews its
[unbound checkout](../../glossary.json#concept.unbound-checkout). It keeps its run store in the
worktree it started in.

### req.spec-review.review-spec-grant — Reviewers read under a review-spec grant

Every reviewer SHALL run under the `review-spec` grant of exactly one reviewed Module, computed
from the Specs of the worktree the run works on.

The chair of a panel without architects runs under the same grant.

### req.spec-review.architect-grant — Architects read under a review-architecture grant

Every architect SHALL run under the `review-architecture` grant of exactly one reviewed Module,
computed from the Specs of the worktree the run works on.

An architect therefore reads every Module's Specs and the names of the project's code, never its
contents. The chair of a panel with architects runs under the same grant, so that it can check an
architect's finding against the other Modules' Specs it cites.

### req.spec-review.own-documents — Only the Module's own documents can block

A finding about a document the reviewed Module does not own SHALL NOT have a blocking
[tier](../../glossary.json#concept.issue-tier).

## Findings, Issues and verdict

### req.spec-review.one-pass — Every blocking finding in one pass

The Reviewer brief SHALL instruct every reviewer and every architect to report every blocking
finding it can establish in one run rather than stopping at the first.

The chair discovers nothing of its own. It audits and accounts for every finding the reviewers and
architects reported, and may not add a problem that none of them reported
([the panel graph](panel.md#the-panel-graph)).

### req.spec-review.earlier-issues — Workers receive the earlier Issues

Before it judges, every worker of a Spec panel SHALL receive the reviewed Module's earlier Issues.

The [definition](panel.md#earlier-issues) says which Issues those are. Where the issues part is
not installed, there are none. In that case, the workers receive none.

### req.spec-review.reports-issues — Every finding that stands becomes an Issue where Issues exist

Wherever the issues part is installed, the Operation SHALL report as an
[Issue report](../../glossary.json#concept.issue-report) through the Issue store every finding of
a completed panel's report, in the order of the report, until the Issue store first refuses a
report.

A completed panel's report holds only the findings that remain after
[normalization](panel.md#normalizing-a-finding) and accounting: a merged finding whose path does not
hold is a rejection, and a panel whose report stays unaccounted stops without reporting. After the
first refusal, the Operation reports no further finding of that Module
([Reporting findings](panel.md#reporting-findings)). Each finding it did not report stays in the
result.

A worker never writes an Issue. The Operation reports in bound and unbound runs alike. Issues is an
[optional integration](../../glossary.json#concept.optional-integration) of the method part. The
review's judgement and its verdict are the same either way. Without Issues, the verdict follows from
the blocking findings that stand. Otherwise, it follows from the Issues they became.

### req.spec-review.nothing-recorded-without-issues — Without Issues, nothing is recorded outside the run

Where the issues part is not installed, the Operation SHALL record nothing outside the run.

Method's requirements for every review then apply. The findings stay in the result with their tier
and severity ([req.method.findings-kept](../requirements.md#req.method.findings-kept)). The result
says that they were not recorded as Issues
([req.method.issues-absent-stated](../requirements.md#req.method.issues-absent-stated)).

### req.spec-review.blank-earlier — An empty earlier names no Issue

The Operation SHALL treat a worker's finding whose `earlier` is empty or blank as naming no earlier
Issue, as if the field were left out.

A worker may write an empty `earlier` for a new finding instead of leaving the field out. Refusing
its whole result for it would lose every other finding of that worker.

### req.spec-review.earlier-checked — Every other earlier is checked against the Issues offered

The Operation SHALL check every `earlier` of a worker's finding that is not empty or blank against
the earlier Issues it offered.

The [definition](panel.md#earlier-issues) says what follows from a name that was not offered.

### req.spec-review.finding-path-resumed — A worker is resumed once to correct its paths

When findings of a worker name a path that does not [hold](panel.md#normalizing-a-finding), the
Operation SHALL resume that worker once, with those paths to correct.

A path that does not hold is a slip of one finding. The worker gets one chance to correct it.

### req.spec-review.finding-path — A finding whose path does not hold is not reported

The Operation SHALL report no finding whose path still does not
[hold](panel.md#normalizing-a-finding) after the worker's
[resume round](../../glossary.json#concept.resume-round).

Afterwards, a path that does not hold costs only that finding. The Module is not made `incomplete`
for it.

### req.spec-review.finding-path-listed — A finding rejected for its path is listed

The Operation SHALL list each finding that it does not report because of its path as rejected,
with the reason.

### req.spec-review.finding-path-others-stand — The worker's other findings stand

When the Operation rejects a finding of a worker because of its path, it SHALL still report every
other finding of that worker.

### req.spec-review.never-disposes — Review closes no Issue

Spec review SHALL NOT close or reopen an Issue.

The earlier Issues a review finds resolved are listed in its result for the task to close.

### req.spec-review.issue-failure-not-issue — A failing Issue system is not an Issue

Spec review SHALL NOT report a refusal of the Issue store as an Issue.

The refusal makes the Module's review `incomplete`. It travels in the result's
[error chain](../../glossary.json#concept.error-chain).

### req.spec-review.host-verdict — The Operation derives the verdict

The [Operation](../../glossary.json#concept.operation) SHALL derive the
[Spec](../../glossary.json#concept.spec) panel's verdict by the rule of its payload contract, never
from a worker's statement.

### req.spec-review.no-structural-substitute — Structural errors stop a Module's review

When Spec core reports a structural error for a Module's Specs, the Operation SHALL NOT launch a
worker for that Module.

### req.spec-review.bound-verdict — The verdict names what was read

Every reviewed Module's outcome SHALL carry the
[context identity](../../glossary.json#concept.context-identity) of the grant its reviewers read
under when that grant was computed, and null when the Module stopped before a reviewer grant
existed.

A Module that failed structural validation, or whose grant could not be computed, has no reviewer
grant. Its outcome then names none rather than an identity nobody read under, as the
[panel payload](panel.md#panel-payload) says.

### req.spec-review.claims-stay-claims — Worker claims stay claims

The [run result](../../glossary.json#concept.run-result) SHALL keep worker findings, severities, tiers,
the chair's merges, notes and rejections and the resolutions apart from the evidence the Operation
produced itself.

## Panel

### req.spec-review.panel-accounted — A panel report accounts for every worker finding

A Spec panel SHALL NOT complete a Module when its panel report does either of these:

- Fails to account for every reviewer and architect finding exactly once.
- Names a label no such finding has.

The [accounting](panel.md#the-panel-graph) rule says how a report accounts for a finding.

### req.spec-review.panel-independent — Panel workers review independently

A panel reviewer's or architect's brief SHALL NOT contain another worker's findings.
