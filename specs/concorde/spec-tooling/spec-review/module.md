# Spec review

## Purpose

Spec review judges whether the Specs of one or more Modules are good enough for their reader, which
no deterministic check can establish. It is the `spec_review` Operation: a headless `review-spec`
worker per named Module reads its Spec context, works through one checklist, and returns every
blocking finding in one pass with a verdict the host derives. It never edits a Spec, repairs a
finding or calls another Operation, and does not repeat structural validation (Spec core) or judge
code (Code review). Its second Operation, `spec_debate`, is a pilot of a review in which a reviewer
and a challenger argue over each finding until they agree or run out of turns, so that what
reaches the developer is either agreed by two workers or an explicit disagreement.

## Terminology

| Term | Definition |
| --- | --- |
| Spec review | One run of the `spec_review` Operation, which judges the Specs of the named Modules of one task worktree and returns findings and a verdict. |
| Review finding | One problem a reviewer establishes in a reviewed Module's documents, with its location, dimension, severity, evidence and a suggested repair. |
| Review verdict | The outcome of a Spec review or a Spec debate, derived by the host from the findings: `accepted`, `changes_required` or `incomplete`, and for a debate also `undecided`. |
| Review memory | The findings the Spec reviews of one Module have kept, open or resolved, each under a stable id, tracked with the project so that a repeated review builds on them. |
| Spec debate | One run of the `spec_debate` Operation, in which a reviewer and a challenger take turns on the Specs of each named Module and the host settles each finding by their stances. |
| Debate item | One finding under debate, proposed by one debater, with each debater's position on it and the history of their stances; it ends agreed, withdrawn or contested, or stays open when its Module's debate stopped. |
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

<a id="concept.spec-review.debate"></a><a id="concept.spec-review.debate-item"></a>

A **Spec debate** is for a review whose findings the main agent wants tested before acting on
them. It is a pilot beside `spec_review`, run the same way:

```text
concorde run spec_debate [--task <task-id>] --modules module.checkout [--challenges 2]
```

A reviewer reviews the Module as in a Spec review. A challenger, a second worker on the same grant,
then answers each finding: it agrees, amends it (say, to a lower severity) or objects that it does
not hold, and adds the findings the reviewer missed. The reviewer answers in turn, and they go back
and forth until nothing is in dispute or the challenge turns run out. The result lists every
**debate item** with its state: `agreed` findings stand, `withdrawn` ones were dropped by both, and
`contested` ones are the developer's to decide, each with both positions and the arguments. A
Module's outcome is `changes_required` when an agreed finding is blocking, `undecided` when only a
contested item keeps a blocking position, and `accepted` otherwise. A debate writes nothing, not
even a review memory, so it can be compared with a Spec review of the same Specs
([definition](debate.md)).

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
  debater: Debater brief {
    "prompts/workers/debate-spec.md"
  }
  host -> checklist: hands reviewers
  host -> debater: hands debaters
  debater -> checklist: shares the checklist of
}
```

<a id="realization.spec-review.operation"></a>

**Review host** runs that sequence through the Harness and returns the Operation result, reviewing
Modules one after another in this version. It runs the Spec debate as well, sharing the first step
and the finding normalization with the Spec review.

<a id="realization.spec-review.checklist"></a>

**Reviewer brief** is the checklist every reviewer and checker receives — dimensions, what counts
as blocking, the one-pass rule, a finding's shape — plus, from the host, the role, the reviewed
Module's own documents, the task's goal and, for a checker, the numbered findings to check. The
checklist itself is a shared part, so that a debater judges by exactly the same bar.

<a id="realization.spec-review.debater"></a>

**Debater brief** is what every debater receives: the shared checklist, the three stances and how
the host applies them, plus, from the host, the role, the turn, and every item awaiting the debater
with both positions and the history so far.

The host, not the worker, derives the verdict, keeping it deterministic: findings stay worker
claims, host-counted. One reviewer per Module keeps its context exactly that Module's Spec context,
and its judgment to that Module's own documents; a problem noticed in a provider's document becomes
an advisory finding naming the provider, never blocking this verdict — the host enforces this
itself, re-filing any such blocking finding as advisory.

### The debate

The debate's control flow is a small state machine: whose turn it is depends on which items await
which side, and it loops. It is written as a LangGraph graph with typed state and conditional
edges rather than as a hand-written loop, so that its edges and its bound are declared in one place
and its state is plain data between steps, which a later version can checkpoint and resume; the
[definition](debate.md#the-debate-graph) draws it. The graph lives inside the host: to its caller
`spec_debate` is an ordinary Operation with one result, and every turn is an ordinary worker run.

Each turn is a new worker rather than a resumed session. A debater therefore rereads the Specs each
turn and sees the debate only as the host wrote it down, so no side can rely on a claim the record
does not hold. It costs more tokens than resuming, which the pilot accepts in exchange for turns
that are independent and bounded.

The host settles items only by the debaters' stances and never judges a finding. Agreement is the
only way a finding stands or falls; a disagreement that survives the last turn is not resolved by
the host but reported, since whether the Spec is clear enough is then a judgment for the developer.
The bound on challenge turns keeps a debate that will not converge from running on.

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
checker and debate turn with only its [brief](../../agents/workers/module.md#concept.workers.brief),
return its [worker result](../../agents/workers/module.md#concept.workers.worker-result) extended
with findings, checks or a debater's responses, audit for changes, and keep a
[run record](../../agents/workers/module.md#concept.workers.run-record). A `blocked`/`failed`
worker, or an audit finding a change, makes that Module's review or debate `incomplete`, its error
link travelling in the result's error chain unchanged.

<a id="uses-operations"></a>

**Operations** defines the [Operation](../../operations/module.md#concept.operations.operation)
concept, runs its [host](../../operations/module.md#concept.operations.host) from `concorde run`,
and fixes the [Operation result](../../operations/module.md#concept.operations.result) envelope in
which Spec review returns its verdict and findings. Spec review relies on it to be launched with a
task and its arguments and to hand its payload back; its duty is to fill the envelope honestly,
keeping worker claims apart from the host's own evidence.
