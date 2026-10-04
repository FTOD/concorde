# Spec review

## Purpose

Spec review judges whether the Specs of one or more Modules are good enough for their reader.
No deterministic check can establish this. Where the issues part is installed, Spec review records
every problem it finds as an [Issue](../../glossary.json#concept.issue) of the project.
Where it is not installed, Spec review records every problem in its run result alone. It provides
two Operations.

A Spec review is one run of the `spec_review` Operation. For each named
[Module](../../glossary.json#concept.module), a headless `review-spec` worker reads its
[Spec context](../../glossary.json#concept.spec-context). The worker judges it by the Protocol's
criteria of Module quality. It returns every blocking finding in one pass.

A Spec panel is one run of `spec_panel`. Several reviewers review each Module independently.
From every Module's Specs, two architects judge it by the criteria of architecture quality.
A chair audits all their findings. It merges them into one report. Thus, one worker's blind spots and
false alarms do not decide what reaches the project.

Where Issues exist, both Operations report every finding that stands as an Issue. Both derive a
verdict from the blocking findings and Issues that stand. Neither Operation does any of these things:

- Edit a [Spec](../../glossary.json#concept.spec).
- Repair a finding.
- Close an Issue.
- Call another Operation.
- Repeat structural validation (Spec core).
- Judge code (Code review).

## Core concepts

A Spec review and a Spec panel both return findings. They report each as an Issue. They derive a
verdict from the Issues that stand.

<a id="concept.review-finding"></a>

Each **[review finding](../../glossary.json#concept.review-finding)** names these details:

- The Module, document and anchor or line concerned.
- One dimension of the Protocol's *Evaluating a Spec* (`protocol/evaluation.md`).
- A short title.
- The problem.
- Its impact.
- Its evidence.
- A suggested repair.
- Its [tier](../../glossary.json#concept.issue-tier).
- Its [severity](../../glossary.json#concept.issue-severity).

The dimension is one of these:

- A Module quality dimension for a reviewer.
- An architecture quality dimension for an architect.
- `context` for a document or promise the worker needed but was not given.

When the Spec can be relied upon but could serve its reader better, the tier is `suggestion`.
Otherwise, the blocking tier says who may fix it: `obvious-fix`, `preferred-fix` or
`decision-needed`. The severity says how much the problem matters to a reader or a task relying on
the Spec. It ranges from `critical` down to `low`. A worker reports every blocking finding it can
establish in one pass. Thus, one round of changes can address them all. `--check-findings` has a
second worker mark each finding of a Spec review `confirmed` or `disputed` with a reason. A Module
without findings needs no checker.

**Earlier Issues** are the open Issues of a reviewed Module that an earlier Spec review or Spec
panel reported. Every worker receives them before it judges. A problem already recorded is
therefore reported again only when it changed, as a finding naming that Issue and never as a new
one. As **resolved**, the worker lists every earlier Issue the Specs no longer have.
It gives its reason for each. An earlier Issue it neither names nor resolves still stands,
**carried**. The Operation, never a worker, writes the Issues. When a finding names an earlier
Issue, the Operation appends it to that Issue. It records any other finding as a new Issue. It
closes none. The Operation lists the resolved Issues in the result for the task to close.

Earlier Issues exist only where the issues part is installed. Without it, a review does the
following:

- It reads no earlier Issues.
- It reports nothing outside the run.
- It keeps every finding in its result with its tier and severity.
- It lists no Issue as carried or resolved.
- It says in its result that its findings were not recorded as Issues
  ([req.spec-review.reports-issues](requirements.md#req.spec-review.reports-issues)).

Without the issues part, its verdict follows from the findings it reports. It follows exactly as
it would from the Issues those findings would have become.

<a id="concept.review-verdict"></a>

The **[review verdict](../../glossary.json#concept.review-verdict)** has these values:

- When no Issue of a blocking tier stands for any reviewed Module, it is `accepted`.
- When such an Issue stands, whether this review reported it or carried it as an earlier Issue,
  it is `changes_required`.
- When a Module could not be reviewed or its Issues could not be written, it is `incomplete`.

Examples of the last case include these:

- Failed structural validation.
- A blocked or failed worker.
- An audit-found change.
- A refusal of the Issue store.

The [step table](operation.md#host-sequence) gives every cause. The verdict carries every reviewed
Module's context identity. Once any of those Specs changes, the verdict stops applying. Acting on
the Issues is later work of the task, by their tier. It is never the review's work. Spec review
itself changes no Spec.

The **panel report** is what a Spec panel's chair returns. Every merged finding names the reviewer
and architect findings it came from. Every rejection gives its reason. The Operation checks that
the report accounts for every such finding exactly once. Thus, nothing a worker found is silently
lost ([definition](panel.md)).

## Overview

### A Spec review

Spec review follows the ordinary step sequence of a worker-backed Operation. It omits the writing
steps a `review-spec` grant makes moot. For each named Module, it takes these steps:

- It validates first.
- It freezes one grant.
- It reads the Module's earlier Issues.
- It launches one reviewer.
- It audits for changes.
- It optionally runs the checker.
- It reports the findings as Issues.
- It derives the Module's outcome.

The numbers in the diagram are those of the [step table](operation.md#host-sequence):

```d2 illustrative
direction: down
core: "Spec core" {
  validate: "1. Load the Specs,\nvalidate the Module"
  grant: "2. Compute and freeze the\nreview-spec grant with\nits context identity"
}
op: "Operation" {
  earlier: "3. Read the Module's\nearlier Issues"
  audit: "5. Audit: nothing changed"
  report: "7. Normalize the findings,\nreport each as an Issue,\noutcome from the Issues that stand"
  verdict: "Verdict over\nevery named Module" {shape: page}
}
workers: "Worker runs" {
  reviewer: "4. Reviewer: one pass,\nevery blocking finding"
  checker: "6. Checker, with --check-findings:\nconfirmed or disputed"
}
issues: "Issues of the project" {shape: cylinder}
core.validate -> core.grant
core.grant -> op.earlier
issues -> op.earlier: "open Issues\nreviews reported"
op.earlier -> workers.reviewer
workers.reviewer -> op.audit
op.audit -> workers.checker: "findings\nto check"
workers.checker -> op.report: "after its audit"
op.audit -> op.report: otherwise
op.report -> issues: "append or create"
op.report -> op.verdict: "after the\nlast Module"
```

The diagram shows the normal path. On a Spec core structural error, the Operation marks the Module
`incomplete`. It does not send the Module to a worker to judge a Spec that won't load. The Module
is also `incomplete` in any of these cases:

- No grant can be computed for it.
- Its earlier Issues cannot be read.
- The reviewer or checker ends `blocked`/`failed`.
- An audit finds a change.
- The Issue store refuses a report.

Only a loading error fails the whole run. Otherwise, the Operation still reviews the other Modules.

### A Spec panel

A **Spec panel** serves a caller who wants to rely on a review more than on one reviewer.
One reviewer's findings vary from run to run and are sometimes wrong. A Spec panel also judges how
the Module fits the project. One Module's context cannot give that.

By default, three reviewers review the Module at the same time. Each reviews it on its own by the
Module quality criteria. By the architecture quality criteria, two architects each judge the
Module's place among all Modules on their own. The chair then reads all their findings. It does
these things:

- Checks each finding against the Specs.
- Merges the findings that describe the same problem.
- Rejects the findings that do not hold.
- Gives every merged finding its tier.

The Operation checks the chair's accounting. When the report does not account for every finding,
the Operation gives the chair one more attempt. It then reports the merged findings as Issues:

```d2 illustrative
direction: down
workers: "Reviewer and architect runs, in parallel" {
  r1: "Reviewer 1 … N\n(review-spec)"
  a1: "Architect 1, 2\n(review-architecture)"
}
op: "Operation" {
  gather: "Gather: every\nworker finished?" {shape: diamond}
  account: "Accounting: every\nfinding accounted once?" {shape: diamond}
  retry: "An attempt left?" {shape: diamond}
  report: "Report the merged\nfindings as Issues;\noutcome from the Issues\nthat stand" {shape: page}
  short: "Module incomplete:\npanel_short" {shape: page}
  unaccounted: "Module incomplete:\nreport_unaccounted" {shape: page}
}
chair: "Chair run" {
  merge: "Check each finding against the Specs,\nmerge duplicates, reject what\ndoes not hold, give each its tier"
}
workers.r1 -> op.gather
workers.a1 -> op.gather
op.gather -> chair.merge: yes
op.gather -> op.short: no
chair.merge -> op.account
op.account -> op.report: yes
op.account -> op.retry: no
op.retry -> chair.merge: "yes, with the problems"
op.retry -> op.unaccounted: no
```

The [definition](panel.md#the-panel-graph) gives the exact graph and its control rules.

### Its parts

```d2
review: Spec review {
  host: Review Operations {
    "src/concorde/method/spec_review/"
  }
  checklist: Reviewer brief {
    "prompts/workers/review-spec.md"
    "prompts/workers/spec-review/"
  }
  panel: Panel brief {
    "prompts/workers/panel-spec.md"
  }
  host -> checklist: hands reviewers
  host -> panel: hands the panel
  panel -> checklist: shares the checklist of
}
```

<a id="realization.spec-review.operation"></a>

**Review Operations** runs that sequence through Workers. It reports through the Issue store.
It returns the run's output. In this version, it reviews Modules one after another. It runs the Spec
panel as well. It shares these parts with the Spec review:

- The first step.
- The earlier Issues.
- The finding normalization.
- The reporting.

<a id="realization.spec-review.checklist"></a>

**Reviewer brief** is the checklist every worker of both Operations receives. It includes these
items:

- The Protocol's *Evaluating a Spec* as the criteria.
- A finding's shape and its tiers.
- The one-pass rule.
- How to treat earlier Issues.

The Operation also supplies these items:

- The role.
- The reviewed Module's own documents.
- The workspace's goal.
- The earlier Issues.
- For a checker, the numbered findings to check.

The criteria are the Protocol's. The brief does not restate them. Thus, every worker judges by the
same bar as a Spec's author reads. The Operation appends them from the project's
[Protocol copy](../../glossary.json#concept.protocol-copy). It includes the *Writing guidance* and
the *Sentence style* the criteria build on.

The `readability` dimension covers the Sentence style. Spec core's style checks already report
these problems as warnings:

- Long sentences.
- Semicolons.
- Sentences with several requirement keywords.

A reviewer therefore does not report them again. A reviewer reports what no check decides, such as
a requirement that hides its actor in the passive voice. It groups the instances of one kind in one
document into one finding. While a reader still understands the text correctly, such a finding is
a `suggestion`.

<a id="realization.spec-review.panel"></a>

**Panel brief** is what every panel worker receives. It includes the shared checklist. It also
includes the roles of the reviewers, the architects and the chair. The Operation also supplies the
role and seat or attempt. For the chair, it supplies these items:

- Every labelled finding.
- Every resolution the workers claimed.
- On its second attempt, its previous report and what it left unaccounted.

## Running a review

The caller runs a **Spec review** in either case:

- A [Spec change](../../glossary.json#concept.spec-change) is ready to be judged, typically after
  `specify` and before implementation.
- The caller doubts that an existing Spec is clear enough to hand to workers.

```text
concorde run spec_review --modules module.checkout,module.inventory [--check-findings]
```

The command waits for the result. With `--detach`, it is a
[detached run](../../glossary.json#concept.detached-run). It prints its run identity at once. When
it ends, it writes the result. In a task worktree, it reviews the
[workspace](../../glossary.json#concept.workspace) whose binding lies there. In that case,
`--modules` defaults to the binding's Modules. From that worktree's Specs, the Operation reviews
each named Module on its own. Thus, what gets judged is the branch's own change, committed or not.
In a worktree without a binding, such as the primary worktree, it is an
[unbound run](../../glossary.json#concept.unbound-run). It judges the Specs of that worktree's
`HEAD`. It reads them from its [unbound checkout](../../glossary.json#concept.unbound-checkout).
Either way its Issues go to the project's Issues. The primary worktree keeps them. Whenever every
Module could be reviewed and its Issues written, status is `ok`. When the verdict is `incomplete`,
status is `blocked`/`failed`. No other verdict gives that status. The result still carries every
reviewed Module's findings.

A Spec panel is run the same way as a Spec review:

```text
concorde run spec_panel --modules module.checkout [--reviewers 3] [--architects 2]
```

The result names these Issues:

- Each finding's Issue.
- The earlier Issues carried.
- The resolved ones.

The task handles them by their tier as the
[main-session guidance](../../coordination/main-session/module.md#issues) says:

- It fixes an `obvious-fix` or `preferred-fix` Issue with later `specify` work.
- It escalates a `decision-needed` one by its identity.
- It leaves a `suggestion`.
- It closes each resolved Issue.

## Why it is built this way

### Issues are the review's memory

A single worker's findings vary from run to run. A review that forgot the one before it would
report again, in other words, problems the task already saw. It would also drop the ones it
happened not to notice this time. The project's Issues carry a Module's problems from one review
to the next. They have these properties:

- They are project-level.
- The primary worktree keeps them.
- Every task, session and run, bound and unbound alike, sees them at once.
- They are the same records a session reads when it looks for work.

A review therefore records a problem where every other concrete problem of the project is. Its
tier says who may fix it. Its severity says how much it matters. Nothing review-specific needs any
of these things:

- To be merged.
- To be carried by a delivery.
- To be kept in step with the Issues.

The worker, not the Operation, matches a finding with an earlier Issue. Two reviews describe the
same problem in these ways:

- In other words.
- At another anchor.
- With other evidence.

Only a reader of the Specs can tell that it is the same problem. A textual comparison would keep
duplicates or merge distinct problems. So every worker receives the earlier Issues with these
details:

- Their identity.
- Their severity.
- Their tier.
- Their latest report.

The worker names the Issue a finding updates or the Issue the Specs no longer have. The Operation
keeps what no worker may decide:

- It accepts a match only with an earlier Issue it offered.
- It ignores any other match.
- It lists any other match.
- It reports nothing a checker disputed.
- It records the Issues itself with the run's provenance.
- It derives the outcome from the Issues that stand.

Thus, until a review finds it resolved and a task closes it, a blocking Issue stands.

The Operation appends to an earlier Issue at the revision it reads just before. Thus, a report
made in between is never overwritten. The store refuses the append instead, as it refuses any
stale write. The review never closes an Issue. A review that no longer sees a problem is evidence
for the closure, not the closure itself. The task that fixed it names it. Its merge closes it.
Or the session closes it by hand, answering for the evidence.

A failure of the Issue system while reporting is not a problem of the reviewed Specs. The review
never reports it as an Issue. When an Issue system fails, it cannot be trusted to record its own
failure. The Module's review is `incomplete` with the store's refusal in the result's
[error chain](../../glossary.json#concept.error-chain). Its findings stay in the result, each naming
the Issue it was written to or none. Once the store works again, the task can report the rest.

Without a per-Module record of what was last judged, there is nothing to compare with. Even for
unchanged Specs the last review judged, each run reviews again. A repeated review of unchanged
Specs costs a worker run. When it does not find an Issue changed, it changes no such Issue.

For each Module, a review runs through its Issues like this
([step table](operation.md#host-sequence)):

```d2 illustrative
direction: down
read: "Read the Module's open Issues\nthat reviews reported"
launch: "Launch the workers with the\nearlier Issues, then audit"
check: "Checker, with --check-findings\nand at least one finding"
match: "Each kept finding:\nnames an earlier Issue?" {shape: diamond}
append: "Append it to that Issue"
create: "Record a new Issue"
failed: "Store refused?" {shape: diamond}
outcome: "Outcome from the Issues that\nstand: reported now or carried" {shape: page}
unreported: "Module incomplete:\nissues_unreported" {shape: page}

read -> launch -> check -> match
match -> append: yes
match -> create: no
append -> failed
create -> failed
failed -> unreported: yes
failed -> outcome: "no, after the last"
```

### The panel

A single reviewer's findings vary from run to run. Two reviews of the same Specs agree on most
problems. Each finds real ones the other misses. Occasionally, one reports a problem the Specs do
not have. The panel therefore takes several independent reviews. This widens what is found. Its
chair checks each finding against the Specs. This removes what does not hold. The workers never
see each other's work. Thus, their agreement is evidence. The chair does these things:

- Merges findings.
- Judges findings.
- Gives each finding its tier.

It adds nothing. Thus, every report finding traces back to a reviewer or an architect.

A reviewer reads only what the reviewed Module's declarations select. This is right for judging
whether its own documents serve their reader. It is blind to how the Module fits the project, such
as these problems:

- A responsibility two Modules both claim.
- A dependency relied on but not declared.
- A consumer that knows its provider's internals.

The architects cover that. Each runs under a `review-architecture` grant of the reviewed Module.
The grant reads every Module's Specs and no code. By the Protocol's architecture criteria, each
architect judges these aspects:

- The Module's relations with the others.
- The Module's degree of decoupling.
- The clarity of the Module's boundaries.

Two architects on different models make that judgment independent as the reviewers' is. When only
the Module's own Specs are in question, `--architects 0` leaves it out. A problem between Modules
concerns each of them. So an architect's finding names the other Modules it concerns besides the
document it cites.

The panel's control flow follows these steps. It is written as a LangGraph graph with typed state
and conditional edges:

- It fans out to the reviewers and architects in parallel.
- It joins them.
- It loops back to the chair at most once.

Thus, the following are declared in one place:

- The fan-out.
- The join.
- The bounded repair.

Its state is plain data between steps. A later version can checkpoint and resume that state. The
[definition](panel.md#the-panel-graph) draws it. The graph lives inside the Operation's steps. To
its caller, `spec_panel` is an ordinary Operation with one result. Every reviewer, architect and
chair is an ordinary worker run.

The Operation keeps what no worker may decide:

- It labels each finding.
- It normalizes every finding as a Spec review does.
- It checks the chair's accounting.
- It reports the Issues.
- It derives the outcome.

When a report loses a finding, the Operation sends it back rather than repairing it, since only the
chair judges findings. When the report still loses a finding after the chair's second attempt, the
Module is `incomplete`. The reviews still stay in the result, and the Operation reports nothing. When a worker does not finish, the panel stops
before the chair. Thus, a report never silently rests on fewer reviews than asked for.

### What a worker sees

A worker cannot widen its own view. When it lacks a needed document of another Module, a reviewer
reports a `context` finding naming it. It then goes on. The task decides whether the Spec lacks a
relation or the review needs another Module. A worker ends `blocked` only when it cannot review at
all, for example because the reviewed Module's own documents cannot be read.
Only the reviewed Module's own documents can carry a blocking finding. A problem in another Module's
document is a `suggestion` naming that Module. That Module's own review judges it. In this
version, workers read Specs directly under their grant, not the Spec MCP server. They use one
checklist covering all dimensions. Splitting by dimension and server queries are future work.

## Around it

Spec review is part of Method, the part that composes the others. It has these relations:

- It asks Spec core whether a Module can be reviewed at all.
- It reaches an agent only through Workers in the worker harness.
- Where the issues part is installed, it records its findings through Issues.
- Like every Operation, it runs through the Execution runner.
- Method registers its two Operations with that runner.

```d2
review: Spec review
spec: Spec core
workers: Workers
operations: Operations
execution: Execution
issues: Issues
review -> spec
review -> workers
review -> operations
review -> execution
review -> issues
```

<a id="uses-spec"></a>

**Spec core**'s [structural checks](../../glossary.json#concept.structural-check) decide whether a
Module can be reviewed at all. Its [grants](../../glossary.json#concept.grant) with
[context identities](../../glossary.json#concept.context-identity) fix exactly which Specs a worker
may read. They bind the verdict to those Specs. They do so per Module and
[task type](../../glossary.json#concept.task-type):

- `review-spec` for a reviewer, checker and chair.
- `review-architecture` for an architect.

When loading fails, the run fails with the loading error as host evidence. When a grant is
rejected, that Module's review is `incomplete`.

<a id="uses-workers"></a>

**Workers**, in the worker harness, turn a frozen grant into a running worker. Method hands the
grant over as data through its
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence). Workers do these
things:

- Launch each reviewer, checker, architect and chair with only its
  [brief](../../glossary.json#concept.brief).
- Return its [worker result](../../glossary.json#concept.worker-result) extended with findings,
  checks or a panel report.
- Audit for changes.
- Keep a [run record](../../glossary.json#concept.run-record).

When a worker ends `blocked`/`failed` or an audit finds a change, that Module's review or panel is
`incomplete`. Its error link travels in the result's
[error chain](../../glossary.json#concept.error-chain) unchanged.

<a id="uses-issues"></a>

**Issues** is an [optional integration](../../glossary.json#concept.optional-integration). Where
the issues part is installed, it keeps the project's [Issues](../../glossary.json#concept.issue)
in the primary worktree. This applies whichever worktree the run works in. Where it is not installed,
the review keeps its findings in its result alone, as [its core concepts](#core-concepts) say. Spec
review reaches Issues only through the issues part's
[bookkeeping command](../../issues/interface.md#bookkeeping-command), `concorde issues`, never its
code. Through that command, it relies on the store to do these things:

- List the open Issues of a Module with their latest
  [report](../../glossary.json#concept.issue-report) and
  [revision](../../glossary.json#concept.issue-revision).
- Record a new Issue or append a report at the revision read.
- Before answering, commit it.
- Refuse a stale append rather than overwrite it.

It relies on the [tiers](../../glossary.json#concept.issue-tier) for what a finding blocks. It
relies on the [severities](../../glossary.json#concept.issue-severity) for how much a finding
matters. The Operation supplies each report's provenance itself, as an Operation's host may. It
uses `report --provenance` for this. When the store refuses, the Module's review is `incomplete`.
The store's error is the cause. The Operation never retries it. It never records it as an Issue.

<a id="uses-operations"></a>

**Operations**, Execution's Operation framework, defines the
[Operation](../../glossary.json#concept.operation) concept. Method registers `spec_review` and
`spec_panel` with it as Operations. They may run unbound. They change nothing in the workspace.
Method registers their [worker ids](../../glossary.json#concept.worker-id) too
([Method](../module.md#the-operations-and-commands-it-provides)). Spec review relies on that
definition for dispatch with its arguments. By the rules every review shares, it relies on Method's
review Issue helpers to do these things with its [earlier Issues](operation.md#earlier-issues):

- Read them.
- Settle them.
- Report them.

It supplies only these things:

- Its two Operations.
- The disputed findings it reports nowhere.
- The Issue report of a finding.

<a id="uses-execution"></a>

**Execution**'s [runner](../../glossary.json#concept.execution-runner) runs both Operations' steps
from `concorde run`. It does these things:

- Reads the [workspace binding](../../glossary.json#concept.workspace-binding).
- Settles the Modules.
- Admits the inputs.
- Fixes the [run result](../../glossary.json#concept.run-result) envelope in which Spec review
  returns its verdict and findings.

Spec review relies on it for these things:

- The workspace's goal and Modules.
- The worktree the run started in, whose primary worktree keeps the Issues.
- Whether the run is unbound, whose Issues carry no task.

Spec review's duty is to fill the envelope honestly. It keeps worker claims apart from its own
evidence.
