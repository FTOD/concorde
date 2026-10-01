# Spec review

## Purpose

Spec review judges whether the Specs of one or more Modules are good enough for their reader, which
no deterministic check can establish, and records every problem it finds as an
[Issue](../../glossary.json#concept.issue) of the project. It provides two Operations. In a Spec
review, one run of the `spec_review` Operation, a headless `review-spec` worker per named
[Module](../../glossary.json#concept.module) reads its
[Spec context](../../glossary.json#concept.spec-context), judges it by the Protocol's criteria of
Module quality and returns every blocking finding in one pass. In a Spec panel, one run of
`spec_panel`, several reviewers review each Module independently, two architects judge it from
every Module's Specs by the criteria of architecture quality, and a chair audits and merges all
their findings into one report, so that one worker's blind spots and false alarms do not decide what
reaches the project. Both Operations report every finding that stands as an Issue and derive a
verdict from the Issues that stand. Neither edits a [Spec](../../glossary.json#concept.spec),
repairs a finding, closes an Issue or calls another Operation, and neither repeats structural
validation (Spec core) or judges code (Code review).

## Core concepts

A Spec review and a Spec panel both return findings, report each as an Issue and derive a verdict
from the Issues that stand.

<a id="concept.review-finding"></a>

Each **[review finding](../../glossary.json#concept.review-finding)** names the Module, document and
anchor or line concerned; one dimension of the Protocol's *Evaluating a Spec*
(`protocol/evaluation.md`), a Module quality dimension for a reviewer, an architecture quality
dimension for an architect, or `context` for a document or promise the worker needed but was not
given; a short title, the problem, its impact, its evidence and a suggested
repair, and its [tier](../../glossary.json#concept.issue-tier): `suggestion` when the Spec can be
relied upon but could serve its reader better, and otherwise the blocking tier that says who may fix
it, `obvious-fix`, `preferred-fix` or `decision-needed`. A worker reports every blocking finding it
can establish in one pass, so one round of changes can address them all. `--check-findings` has a
second worker mark each finding of a Spec review `confirmed` or `disputed` with a reason; a Module
without findings needs no checker.

**Earlier Issues** are the open Issues of a reviewed Module that an earlier Spec review or Spec
panel reported. Every worker receives them before it judges, so that a problem already recorded is
reported again only when it changed, as a finding naming that Issue, and never as a new one; the
worker lists every earlier Issue the Specs no longer have, with its reason, as **resolved**, and an
earlier Issue it neither names nor resolves still stands, **carried**. The Operation, never a
worker, writes the Issues: it appends a finding that names an earlier Issue to that Issue and
records any other finding as a new Issue. It closes none: the resolved Issues are listed in the
result for the task to close.

<a id="concept.review-verdict"></a>

The **[review verdict](../../glossary.json#concept.review-verdict)** is `accepted` when no Issue of a
blocking tier stands for any reviewed Module, `changes_required` when one does, whether this review
reported it or it is an earlier Issue the review carried, and `incomplete` when a Module could not
be reviewed or its Issues could not be written — for example failed structural validation, a
blocked or failed worker, an audit-found change or a refusal of the Issue store; the
[step table](operation.md#host-sequence) gives every cause. It carries every reviewed Module's
context identity and stops applying once any of those Specs changes. Acting on the Issues is later
work of the task, by their tier, never the review's: Spec review itself changes no Spec.

The **panel report** is what a Spec panel's chair returns: every merged finding names the reviewer
and architect findings it came from, and every rejection gives its reason. The Operation checks
that the report accounts for every such finding exactly once, so nothing a worker found is silently
lost ([definition](panel.md)).

## Overview

### A Spec review

Spec review follows the ordinary step sequence of a worker-backed Operation, minus the writing
steps a `review-spec` grant makes moot. For each named Module it validates first, freezes one
grant, reads the Module's earlier Issues, launches one reviewer, audits for changes, optionally
runs the checker, reports the findings as Issues and derives the Module's outcome; the numbers are
those of the [step table](operation.md#host-sequence):

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

The diagram shows the normal path. On a Spec core structural error the Module is marked
`incomplete` rather than sent to a worker to judge a Spec that won't load; it is `incomplete` too
when no grant can be computed for it, its earlier Issues cannot be read, the reviewer or checker
ends `blocked`/`failed`, an audit finds a change, or the Issue store refuses a report. Only a
loading error fails the whole run; otherwise the other Modules are still reviewed.

### A Spec panel

A **Spec panel** is for a review the caller wants to rely on more than on one reviewer, whose
findings vary from run to run and are sometimes wrong, and for a judgment of how the Module fits the
project, which one Module's context cannot give. Three reviewers, by default, review the Module at
the same time, each on its own and by the Module quality criteria, and two architects, each on its
own, judge the Module's place among all the Modules by the architecture quality criteria. The chair
then reads all their findings, checks each against the Specs, merges the ones that describe the same
problem, rejects the ones that do not hold and gives every merged finding its tier, and the
Operation checks its accounting, giving the chair one more attempt when the report does not account
for every finding, before it reports the merged findings as Issues:

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
    "src/concorde/spec_review/"
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

**Review Operations** runs that sequence through Workers, reports through the Issue store and
returns the run's output, reviewing Modules one after another in this version. It runs the Spec
panel as well, sharing the first step, the earlier Issues, the finding normalization and the
reporting with the Spec review.

<a id="realization.spec-review.checklist"></a>

**Reviewer brief** is the checklist every worker of both Operations receives: the Protocol's
*Evaluating a Spec* as the criteria, a finding's shape and its
tiers, the one-pass rule and how to treat earlier Issues; plus, from the Operation, the role, the
reviewed Module's own documents, the workspace's goal, the earlier Issues and, for a checker, the
numbered findings to check. The criteria are the Protocol's and are not restated, so every worker
judges by the same bar as a Spec's author reads.

<a id="realization.spec-review.panel"></a>

**Panel brief** is what every panel worker receives: the shared checklist and the roles of the
reviewers, the architects and the chair, plus, from the Operation, the role and seat or attempt,
and for the chair every labelled finding and every resolution the workers claimed and, on its
second attempt, its previous report and what it left unaccounted.

## Running a review

The caller runs a **Spec review** when a
[Spec change](../../glossary.json#concept.spec-change) is ready to be judged, typically after
`specify` and before implementation, or when it doubts that an existing Spec is clear enough to hand
to workers:

```text
concorde run spec_review --modules module.checkout,module.inventory [--check-findings]
```

The command waits for the result; with `--detach` it is a
[detached run](../../glossary.json#concept.detached-run) that prints its run identity at once and
writes the result when it ends. In a task worktree it reviews the
[workspace](../../glossary.json#concept.workspace) whose binding lies there, and `--modules`
defaults to the binding's Modules; each named Module is reviewed on its own from that worktree's
Specs, so what gets judged is the branch's own change, committed or not. In a worktree without a
binding, such as the primary worktree, it is an
[unbound run](../../glossary.json#concept.unbound-run) that judges the Specs of that worktree's
`HEAD`, read from its [unbound checkout](../../glossary.json#concept.unbound-checkout). Either way
its Issues go to the project's Issues, which the primary worktree keeps. Status is `ok` whenever
every Module could be reviewed and its Issues written, `blocked`/`failed` only when the verdict is
`incomplete` — still carrying every reviewed Module's findings.

A Spec panel is run the same way as a Spec review:

```text
concorde run spec_panel --modules module.checkout [--reviewers 3] [--architects 2]
```

The result names each finding's Issue, the earlier Issues carried and the resolved ones. The task
handles them by their tier as the
[main-session guidance](../../coordination/main-session/module.md#issues) says: it fixes an
`obvious-fix` or `preferred-fix` Issue with later `specify` work, escalates a `decision-needed`
one by its identity, leaves a `suggestion`, and closes each resolved Issue.

## Why it is built this way

### Issues are the review's memory

A single worker's findings vary from run to run, so a review that forgot the one before it would
report again, in other words, problems the task has already seen, and would drop the ones it
happened not to notice this time. The project's Issues are the state that carries a Module's
problems from one review to the next: they are project-level, kept by the primary worktree and seen
at once by every task, session and run, bound and unbound alike, and they are the same records a
session reads when it looks for work. A problem a review finds is therefore recorded where every
other concrete problem of the project is, with a tier that says who may fix it, and nothing
review-specific has to be merged, carried by a delivery or kept in step with them.

The worker, not the Operation, matches a finding with an earlier Issue. Two reviews describe the
same problem in other words, at another anchor or with other evidence, and only a reader of the
Specs can tell that it is the same problem; a textual comparison would keep duplicates or merge
distinct problems. So every worker receives the earlier Issues, with their identity, tier and
latest report, and names the Issue a finding updates or the Issue the Specs no longer have. The
Operation keeps what no worker may decide: it accepts a match only with an earlier Issue it offered,
ignoring and listing any other, reports nothing a checker disputed, records the Issues itself with
the run's provenance, and derives the outcome from the Issues that stand, so a blocking Issue
stands until a review finds it resolved and a task closes it.

The Operation appends to an earlier Issue at the revision it reads just before, so a report made in
between is never overwritten: the store refuses the append instead, as it refuses any stale write.
The review never closes an Issue, because a review that no longer sees a problem is evidence for
the closure, not the closure itself: the task that fixed it names it, and its merge closes it, or
the session closes it by hand, answering for the evidence.

A failure of the Issue system while reporting is not a problem of the reviewed Specs and is never
reported as an Issue: an Issue system that failed cannot be trusted to record its own failure. The
Module's review is `incomplete` with the store's refusal in the result's
[error chain](../../glossary.json#concept.error-chain), and its findings stay in the result, each
naming the Issue it was written to or none, so that the task can report the rest once the store
works again.

Each run reviews again, even Specs the last review judged unchanged: without a per-Module record of
what was last judged there is nothing to compare with, and a repeated review of unchanged Specs
costs a worker run but changes no Issue it does not find changed.

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

A single reviewer's findings vary from run to run: two reviews of the same Specs agree on most
problems but each finds real ones the other misses, and occasionally one reports a problem the Specs
do not have. The panel therefore takes several independent reviews, which widens what is found, and
a chair that checks each finding against the Specs, which removes what does not hold. The workers
never see each other's work, so their agreement is evidence; the chair merges, judges and gives each
finding its tier but adds nothing, so every report finding traces back to a reviewer or an
architect.

A reviewer reads only what the reviewed Module's declarations select, which is right for judging
whether its own documents serve their reader and blind to how it fits the project: a responsibility
two Modules both claim, a dependency relied on but not declared, a consumer that knows its
provider's internals. The architects cover that. Each runs under a `review-architecture` grant of
the reviewed Module, which reads every Module's Specs and no code, and judges the Module's
relations with the others, how well it is decoupled and whether its boundaries are clear, by the
Protocol's architecture criteria. Two architects on different models make that judgment independent
as the reviewers' is; `--architects 0` leaves it out when only the Module's own Specs are in
question. A problem between Modules concerns each of them, so an architect's finding names the other
Modules it concerns besides the document it cites.

The panel's control flow fans out to the reviewers and architects in parallel, joins them, and
loops back to the chair at most once. It is written as a LangGraph graph with typed state and
conditional edges, so that the fan-out, the join and the bounded repair are declared in one place
and its state is plain data between steps, which a later version can checkpoint and resume; the
[definition](panel.md#the-panel-graph) draws it. The graph lives inside the Operation's steps: to
its caller `spec_panel` is an ordinary Operation with one result, and every reviewer, architect and
chair is an ordinary worker run.

The Operation keeps what no worker may decide: it labels each finding, normalizes every finding as a
Spec review does, checks the chair's accounting, reports the Issues and derives the outcome. A
report that loses a finding is sent back rather than repaired by the Operation, since only the
chair judges findings; after its second attempt the Module is `incomplete` with the reviews still
in the result and nothing reported. A worker that does not finish stops the panel before the chair,
so that a report never silently rests on fewer reviews than asked for.

### What a worker sees

A worker cannot widen its own view: lacking a needed document of another Module, a reviewer reports
a `context` finding naming it and goes on, and the task decides whether the Spec lacks a relation or
the review needs another Module. A worker ends `blocked` only when it cannot review at all, for
example because the reviewed Module's own documents cannot be read. Only the reviewed Module's own
documents can carry a blocking finding: a problem in another Module's document is a `suggestion`
naming that Module, which that Module's own review judges. In this version, workers read Specs
directly under their grant, not the Spec MCP server, on one checklist covering all dimensions;
splitting by dimension and server queries are future work.

## Around it

Spec review stays inside Spec tooling but reaches outside it for everything a Spec cannot judge on
its own: it asks Spec core whether a Module can be reviewed at all, it reaches an agent only
through Workers, it records its findings through Issues, and it is run, like every Operation, by
the Execution runner.

```d2
tooling: Spec tooling {
  review: Spec review
  core: Spec core
  review -> core
}
execution: Execution {
  workers: Workers
  operations: Operations
}
issues: Issues
tooling.review -> execution.workers
tooling.review -> execution.operations
tooling.review -> execution
tooling.review -> issues
```

Operations also uses Spec review in turn, since `spec_review` is one of its own Operations —
declared and explained there, not here.

<a id="uses-spec"></a>

**Spec core**'s [structural checks](../../glossary.json#concept.structural-check) decide whether a
Module can be reviewed at all; its [grants](../../glossary.json#concept.grant) with
[context identities](../../glossary.json#concept.context-identity) fix, per Module and
[task type](../../glossary.json#concept.task-type), `review-spec` for a reviewer, checker and chair
and `review-architecture` for an architect, exactly which Specs a worker may read and bind the
verdict to. A load failure fails the run, with the loading error as host evidence; a rejected grant
makes that Module's review `incomplete`.

<a id="uses-workers"></a>

**Workers**, in Execution, turn a frozen grant into a running worker: launch each reviewer, checker,
architect and chair with only its [brief](../../glossary.json#concept.brief), return its
[worker result](../../glossary.json#concept.worker-result) extended with findings, checks or a
panel report, audit for changes, and keep a
[run record](../../glossary.json#concept.run-record). A `blocked`/`failed` worker, or an audit
finding a change, makes that Module's review or panel `incomplete`, its error link travelling in the
result's [error chain](../../glossary.json#concept.error-chain) unchanged.

<a id="uses-issues"></a>

**Issues** keeps the project's [Issues](../../glossary.json#concept.issue) in the primary worktree,
whichever worktree the run works in. Spec review relies on its store to list the open Issues of a
Module with their latest [report](../../glossary.json#concept.issue-report) and
[revision](../../glossary.json#concept.issue-revision), to record a new Issue or append a report at
the revision read, committing it before it answers, and to refuse a stale append rather than
overwrite it; and on its [tiers](../../glossary.json#concept.issue-tier) for what a finding blocks.
The Operation supplies each report's provenance itself, as an Operation's host may. A refusal of
the store makes the Module's review `incomplete`, with the store's error as the cause; the
Operation never retries it and never records it as an Issue.

<a id="uses-operations"></a>

**Operations** defines the [Operation](../../glossary.json#concept.operation) concept and lists
`spec_review` and `spec_panel` in its catalog as Operations that may run unbound and change nothing
in the workspace, with their [worker ids](../../glossary.json#concept.worker-id). Spec review
relies on that entry to be dispatched to with its arguments.

<a id="uses-execution"></a>

**Execution**'s [runner](../../glossary.json#concept.execution-runner) runs both Operations' steps
from `concorde run`: it reads the
[workspace binding](../../glossary.json#concept.workspace-binding), settles the Modules, admits the
inputs and fixes the [run result](../../glossary.json#concept.run-result) envelope in which Spec
review returns its verdict and findings. Spec review relies on it for the workspace's goal and
Modules, the worktree the run started in, whose primary worktree keeps the Issues, and whether the
run is unbound, whose Issues carry no task; its duty is to fill the envelope honestly, keeping
worker claims apart from its own evidence.
