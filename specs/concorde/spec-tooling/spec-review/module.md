# Spec review

## Purpose

Spec review judges whether the Specs of one or more Modules are good enough for their reader, which
no deterministic check can establish. It is the `spec_review` Operation: a headless `review-spec`
worker per named Module reads its Spec context, works through one checklist, and returns every
blocking finding in one pass with a verdict the host derives. It never edits a Spec, repairs a
finding or calls another Operation, and does not repeat structural validation (Spec core) or judge
code (Code review). Its second Operation, `spec_panel`, has several reviewers review each Module
independently and a chair audit and merge their reviews into one report, so that one reviewer's
blind spots and false alarms do not decide what reaches the developer.

## Terminology

| Term | Definition |
| --- | --- |
| Spec review | One run of the `spec_review` Operation, which judges the Specs of the named Modules of one task worktree and returns findings and a verdict. |
| Review finding | One problem a reviewer establishes in a reviewed Module's documents, with its location, dimension, severity, evidence and a suggested repair. |
| Review verdict | The outcome of a Spec review or a Spec panel, derived by the host from the findings: `accepted`, `changes_required` or `incomplete`. |
| Review memory | The findings the Spec reviews of one Module have kept, open or resolved, each under a stable id, tracked with the project so that a repeated review builds on them. |
| Spec panel | One run of the `spec_panel` Operation, in which several reviewers review each named Module independently and a chair audits and merges their findings into one panel report. |
| Panel report | The chair's merged findings of one Module, each naming the reviewer findings it merges, and the reviewer findings it rejected with their reasons, accounting for every reviewer finding exactly once. |
| [Operation](../../operations/module.md#concept.operations.operation) | |
| [Operation host](../../operations/module.md#concept.operations.host) | |
| [Operation result](../../operations/module.md#concept.operations.result) | |
| [Brief](../../agents/workers/module.md#concept.workers.brief) | |
| [Worker result](../../agents/workers/module.md#concept.workers.worker-result) | |
| [Run record](../../agents/workers/module.md#concept.workers.run-record) | |
| [Grant](../spec/module.md#concept.spec.grant) | |
| [Context identity](../spec/module.md#concept.spec.context-identity) | |
| [Structural check](../spec/module.md#concept.spec.structural-check) | |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |

Findings and one verdict travel inside an ordinary Operation result; the verdict is evidence bound
to the context identities the reviewers read.

## Usage

<a id="concept.spec-review.review"></a>

The main agent runs a **Spec review** when a Spec change is ready to be judged, typically after
`specify` and before implementation, or when it doubts that an existing Spec is clear enough to
hand to workers:

```text
concorde run spec_review [--task <task-id>] --modules module.checkout,module.inventory [--check-findings]
```

It runs in the background and writes a result when it ends. Each named Module is reviewed on its
own from the task worktree's Specs, so what gets judged is the branch's own change, committed or
not. Status is `ok` whenever every Module could be reviewed, `blocked`/`failed` only when the
verdict is `incomplete` — still carrying every reviewed Module's findings.

<a id="concept.spec-review.finding"></a>

Each **review finding** names the Module, document and anchor or line concerned, one checklist
dimension (`readability`, `obligations`, `design`, `views`, `terminology`), a severity, the problem,
its evidence and a suggested repair. It is `blocking` when a reader or bound worker could not rely
on the Spec as written, `advisory` otherwise. A reviewer reports every blocking finding it can
establish in one pass, so one round of changes can address them all.
`--check-findings` has a second worker mark each finding `confirmed` or `disputed` with a reason; a
Module without findings needs no checker.

<a id="concept.spec-review.verdict"></a>

The **review verdict** is `accepted` when no blocking finding stands in any reviewed Module's
review memory, `changes_required` when one does, whether this review reported it or an earlier
one did and it still stands, and `incomplete` when a Module could not be reviewed — failed
structural validation, a blocked/failed worker, or an audit-found change. It carries every
reviewed Module's context identity and stops applying once any of those Specs changes. The main
agent decides what to act on, logs that decision, and reruns `specify` for changes; Spec review
itself changes no Spec.

<a id="concept.spec-review.memory"></a>

The **review memory** keeps a Module's review history, so that a repeated review neither forgets
earlier findings nor reports them again as new
([contract](operation.md#contract.spec-review.memory)). It is one file per Module,
`.concorde/reviews/spec/<module>.json`, tracked with the project and committed by the task's
delivery, so every task and every collaborator reviews against the same history. The reviewer
receives the Module's open earlier findings and returns only new findings, earlier findings that
changed (naming their id) and earlier findings the Specs no longer have (with the reason); an
earlier finding it leaves out still stands. The host merges that into the memory, giving each new
finding the next id, keeps out a finding the checker disputed, and reports what was new, updated,
resolved and carried. The reviewer compares every finding with the earlier ones first, since a
model sees the same Specs a little differently each time: the same problem, however worded, is
the earlier finding. A completed review also records the context identity of the Specs it judged;
while a Module's context identity is still that one, a review launches no reviewer and the memory
decides its outcome, unless `--force` asks for a new look. A review without a task reads the
memory and writes nothing.

<a id="concept.spec-review.panel"></a><a id="concept.spec-review.panel-report"></a>

A **Spec panel** is for a review the main agent wants to rely on more than on one reviewer, whose
findings vary from run to run and are sometimes wrong. It is run the same way as a Spec review:

```text
concorde run spec_panel [--task <task-id>] --modules module.checkout [--reviewers 3]
```

Three reviewers, by default, review the Module at the same time, each on its own and with the same
checklist. The chair then reads all their findings, checks each against the Specs, merges the ones
that describe the same problem and rejects the ones that do not hold. The result is the **panel
report**: every merged finding names the reviewer findings it came from and how many reviewers
reported it, and every rejection gives its reason. The host checks that the report accounts for
every reviewer finding exactly once, so nothing a reviewer found is silently lost, and gives the
chair one more attempt when it does not. The Module's outcome is `changes_required` when a report
finding is blocking, `accepted` otherwise. A panel writes nothing, not even a review memory
([definition](panel.md)).

## Design

Spec review follows the ordinary host sequence of a worker-backed Operation, minus the writing
steps a `review-spec` grant makes moot. It validates Modules first, marking one `incomplete` on a
Spec core structural error rather than send a worker to judge a Spec that won't load; freezes one
grant per Module; launches one reviewer per Module; audits for changes; optionally runs the
checker; and derives the verdict ([step table](operation.md#host-sequence)).

```d2
review: Spec review {
  host: Review host {
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

**Review host** runs that sequence through the Harness and returns the Operation result, reviewing
Modules one after another in this version. It runs the Spec panel as well, sharing the first step
and the finding normalization with the Spec review.

<a id="realization.spec-review.checklist"></a>

**Reviewer brief** is the checklist every reviewer and checker receives — dimensions, what counts
as blocking, the one-pass rule, a finding's shape — plus, from the host, the role, the reviewed
Module's own documents, the task's goal and, for a checker, the numbered findings to check. The
checklist itself is a shared part, so that a panel judges by exactly the same bar.

<a id="realization.spec-review.panel"></a>

**Panel brief** is what every panel worker receives: the shared checklist and the roles of the
reviewers and the chair, plus, from the host, the role and seat or attempt, and for the chair every
labelled reviewer finding and, on its second attempt, its previous report and what it left
unaccounted.

### The panel

A single reviewer's findings vary from run to run: two reviews of the same Specs agree on most
problems but each finds real ones the other misses, and occasionally one reports a problem the Specs
do not have. The panel therefore takes several independent reviews, which widens what is found, and
a chair that checks each finding against the Specs, which removes what does not hold. The reviewers
never see each other's work, so their agreement is evidence; the chair merges and judges but adds
nothing, so every report finding traces back to a reviewer.

The panel's control flow fans out to the reviewers in parallel, joins them, and loops back to the
chair at most once. It is written as a LangGraph graph with typed state and conditional edges, so
that the fan-out, the join and the bounded repair are declared in one place and its state is plain
data between steps, which a later version can checkpoint and resume; the
[definition](panel.md#the-panel-graph) draws it. The graph lives inside the host: to its caller
`spec_panel` is an ordinary Operation with one result, and every reviewer and chair is an ordinary
worker run.

The host keeps what no worker may decide: it labels each reviewer finding, normalizes every finding
as a Spec review does, checks the chair's accounting and derives the outcome. A report that loses a
reviewer finding is sent back rather than repaired by the host, since only the chair judges
findings; after its second attempt the Module is `incomplete` with the reviews still in the result.
A reviewer that does not finish stops the panel before the chair, so that a report never silently
rests on fewer reviews than asked for.

A reviewer cannot widen its own view: lacking a needed document, it reports a `context` finding
naming it, and the main agent decides whether the Spec lacks a relation or the review needs another
Module. In this version, reviewers read Specs directly under their grant, not the Spec MCP server,
on one checklist covering all dimensions; splitting by dimension and server queries are future
work.

### Around it

Spec review stays inside Spec tooling but reaches outside it for everything a Spec cannot judge on
its own: it asks Spec core whether a Module can be reviewed at all, and it reaches an agent only
through Workers.

```d2
tooling: Spec tooling {
  review: Spec review
  core: Spec core
  review -> core
}
agents: Agents {
  workers: Workers
}
operations: Operations
tooling.review -> agents.workers
tooling.review -> operations
```

Operations also uses Spec review in turn, since `spec_review` is one of its own Operations —
declared and explained there, not here.

<a id="uses-spec"></a>

**Spec core**'s [structural checks](../spec/module.md#concept.spec.structural-check) decide whether
a Module can be reviewed at all; its [grants](../spec/module.md#concept.spec.grant) with
[context identities](../spec/module.md#concept.spec.context-identity) fix, per Module and task type
`review-spec`, exactly which Specs a reviewer may read and bind the verdict to. A load failure fails
the Operation as host evidence; a rejected grant makes that Module's review `incomplete`.

<a id="uses-workers"></a>

**Workers**, in the Harness, turn a frozen grant into a running worker: launch each reviewer,
checker, panel reviewer and chair with only its [brief](../../agents/workers/module.md#concept.workers.brief),
return its [worker result](../../agents/workers/module.md#concept.workers.worker-result) extended
with findings, checks or a panel report, audit for changes, and keep a
[run record](../../agents/workers/module.md#concept.workers.run-record). A `blocked`/`failed`
worker, or an audit finding a change, makes that Module's review or panel `incomplete`, its error
link travelling in the result's error chain unchanged.

<a id="uses-operations"></a>

**Operations** defines the [Operation](../../operations/module.md#concept.operations.operation)
concept, runs its [host](../../operations/module.md#concept.operations.host) from `concorde run`,
and fixes the [Operation result](../../operations/module.md#concept.operations.result) envelope in
which Spec review returns its verdict and findings. Spec review relies on it to be launched with a
task and its arguments and to hand its payload back; its duty is to fill the envelope honestly,
keeping worker claims apart from the host's own evidence.
