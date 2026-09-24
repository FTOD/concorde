# Spec review

## Purpose

Spec review judges whether the Specs of one or more Modules are good enough for their reader, which
no deterministic check can establish. It is the `spec_review` Operation: a headless `review-spec`
worker per named Module reads its Spec context, works through one checklist, and returns every
blocking finding in one pass with a verdict the host derives. It never edits a Spec, repairs a
finding or calls another Operation, and does not repeat structural validation (Spec core) or judge
code (Code review).

## Terminology

| Term | Definition |
| --- | --- |
| Spec review | One run of the `spec_review` Operation, which judges the Specs of the named Modules of one task worktree and returns findings and a verdict. |
| Review finding | One problem a reviewer establishes in a reviewed Module's documents, with its location, dimension, severity, evidence and a suggested repair. |
| Review verdict | The outcome of a Spec review, derived by the host from the findings: `accepted`, `changes_required` or `incomplete`. |
| [Operation](../../operations/module.md#concept.operations.operation) | |
| [Operation host](../../operations/module.md#concept.operations.host) | |
| [Operation result](../../operations/module.md#concept.operations.result) | |
| [Brief](../../harness/workers/module.md#concept.workers.brief) | |
| [Worker result](../../harness/workers/module.md#concept.workers.worker-result) | |
| [Run record](../../harness/workers/module.md#concept.workers.run-record) | |
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
concorde run spec_review --task <task-id> --modules module.checkout,module.inventory [--check-findings]
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

The **review verdict** is `accepted` when no blocking finding stands (none existed, or the checker
disputed every one), `changes_required` when one does, and `incomplete` when a Module could not be
reviewed — failed structural validation, a blocked/failed worker, or an audit-found change. It
carries every reviewed Module's context identity and stops applying once any of those Specs
changes. The main agent decides what to act on, logs that decision, and reruns `specify` for
changes; Spec review itself changes nothing.

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
  }
  host -> checklist: hands reviewers
}
```

<a id="realization.spec-review.operation"></a>

**Review host** runs that sequence through the Harness and returns the Operation result, reviewing
Modules one after another in this version.

<a id="realization.spec-review.checklist"></a>

**Reviewer brief** is the checklist every reviewer and checker receives — dimensions, what counts
as blocking, the one-pass rule, a finding's shape — plus, from the host, the role, the reviewed
Module's own documents, the task's goal and, for a checker, the numbered findings to check.

The host, not the worker, derives the verdict, keeping it deterministic: findings stay worker
claims, host-counted. One reviewer per Module keeps its context exactly that Module's Spec context,
and its judgment to that Module's own documents; a problem noticed in a provider's document becomes
an advisory finding naming the provider, never blocking this verdict — the host enforces this
itself, re-filing any such blocking finding as advisory.

A reviewer cannot widen its own view: lacking a needed document, it reports a `context` finding
naming it, and the main agent decides whether the Spec lacks a relation or the review needs another
Module. In this version, reviewers read Specs directly under their grant, not the Spec MCP server,
on one checklist covering all dimensions; splitting by dimension and server queries are future
work.

## Relationships

```d2
tooling: Spec tooling {
  review: Spec review
  core: Spec core
  review -> core
}
harness: Harness {
  workers: Workers
}
operations: Operations
tooling.review -> harness.workers
tooling.review -> operations
operations -> tooling.review
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

**Workers**, in the Harness, turn a frozen grant into a running Claude Code worker: launch each
reviewer with only its [brief](../../harness/workers/module.md#concept.workers.brief), return its
[worker result](../../harness/workers/module.md#concept.workers.worker-result) extended with
findings, audit for changes, and keep a
[run record](../../harness/workers/module.md#concept.workers.run-record). A `blocked`/`failed`
worker, or an audit finding a change, makes that Module's review `incomplete`, its error link
travelling in the result's error chain unchanged.

<a id="uses-operations"></a>

**Operations** defines the [Operation](../../operations/module.md#concept.operations.operation)
concept, runs its [host](../../operations/module.md#concept.operations.host) from `concorde run`,
and fixes the [Operation result](../../operations/module.md#concept.operations.result) envelope in
which Spec review returns its verdict and findings. Spec review relies on it to be launched with a
task and its arguments and to hand its payload back; its duty is to fill the envelope honestly,
keeping worker claims apart from the host's own evidence.
