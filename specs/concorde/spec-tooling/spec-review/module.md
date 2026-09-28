# Spec review

## Purpose

Spec review judges whether the Specs of one or more Modules are good enough for their reader, which
no deterministic check can establish. It provides two Operations. In a Spec review, one run of the
`spec_review` Operation, a headless `review-spec` worker per named
[Module](../../glossary.json#concept.module) reads its
[Spec context](../../glossary.json#concept.spec-context), works through one checklist, and returns
every blocking finding in one pass with a verdict the Operation derives. In a Spec panel, one run
of `spec_panel`, several reviewers review each Module independently and a chair audits and merges
their reviews into one report, so that one reviewer's blind spots and false alarms do not decide
what reaches the developer. Neither Operation edits a [Spec](../../glossary.json#concept.spec),
repairs a finding or calls another Operation, and neither repeats structural validation (Spec
core) or judges code (Code review).

## Usage

The caller runs a **Spec review** when a
[Spec change](../../glossary.json#concept.spec-change) is ready to be judged, typically after
`specify` and before implementation, or when it doubts that an existing Spec is clear enough to hand
to workers:

```text
concorde run spec_review --modules module.checkout,module.inventory [--check-findings] [--force]
```

The command waits for the result; with `--detach` it is a
[detached run](../../glossary.json#concept.detached-run) that prints its run identity at once and
writes the result when it ends. In a task worktree it reviews the
[workspace](../../glossary.json#concept.workspace) whose binding lies there, and `--modules`
defaults to the binding's Modules; each named Module is reviewed on its own from that worktree's
Specs, so what gets judged is the branch's own change, committed or not. In a worktree without a
binding, such as the primary worktree, it is an
[unbound run](../../glossary.json#concept.unbound-run) that judges the Specs of that worktree's
`HEAD`, read from its [unbound checkout](../../glossary.json#concept.unbound-checkout).
Status is `ok` whenever every Module could be reviewed, `blocked`/`failed` only when the verdict is
`incomplete` — still carrying every reviewed Module's findings.

<a id="concept.review-finding"></a>

Each **[review finding](../../glossary.json#concept.review-finding)** names the Module, document and
anchor or line concerned, one checklist dimension (`readability`, `obligations`, `design`, `views`,
`terminology`, or `context` for a document or promise the reviewer needed but was not given), a
severity, the problem, its evidence and a suggested repair. It is `blocking` when
a reader or bound worker could not rely on the Spec as written, `advisory` otherwise. A reviewer
reports every blocking finding it can establish in one pass, so one round of changes can address
them all. `--check-findings` has a second worker mark each finding `confirmed` or `disputed` with a
reason; a Module without findings needs no checker.

<a id="concept.review-verdict"></a>

The **[review verdict](../../glossary.json#concept.review-verdict)** is `accepted` when no blocking
finding stands in any reviewed Module's [review memory](../../glossary.json#concept.review-memory),
`changes_required` when one does, whether this review reported it or an earlier one did and it still
stands, and `incomplete` when a Module could not be reviewed — for example failed structural
validation, a blocked/failed worker or an audit-found change; the
[step table](operation.md#host-sequence) gives every cause. It carries every reviewed Module's
context identity and stops applying once any of those Specs changes. The task level decides what
to act on, logs that decision, and reruns `specify` for changes; Spec review itself changes no
Spec.

<a id="concept.review-memory"></a>

The **review memory** keeps a Module's review history, so that a repeated review neither forgets
earlier findings nor reports them again as new
([contract](operation.md#contract.spec-review.memory)). It is the file
`.concorde/reviews/spec/<module>.json`, tracked with the project. A repeated review returns what it
found new, which earlier findings it updated or resolved, and the earlier ones it carried
unchanged; an earlier finding it does not mention still stands and still counts toward the
verdict. While a Module's context identity is the one the last completed review judged, a review
launches no reviewer and the memory decides the Module's outcome, unless `--force` asks for a new
look. Only a review inside a workspace writes the memory, and the task's
[delivery commit](../../glossary.json#concept.delivery-commit) carries it; an unbound review reads
it and writes nothing. [The review memory](#the-review-memory) in Design explains why it works this
way.

A **Spec panel** is for a review the caller wants to
rely on more than on one reviewer, whose findings vary from run to run and are sometimes wrong. It
is run the same way as a Spec review:

```text
concorde run spec_panel --modules module.checkout [--reviewers 3]
```

Three reviewers, by default, review the Module at the same time, each on its own and with the same
checklist. The chair then reads all their findings, checks each against the Specs, merges the ones
that describe the same problem and rejects the ones that do not hold. The result is the **panel
report**: every merged finding names the reviewer findings it came from and how many reviewers
reported it, and every rejection gives its reason. The Operation checks that the report accounts for
every reviewer finding exactly once, so nothing a reviewer found is silently lost, and gives the
chair one more attempt when it does not. The Module's outcome is `changes_required` when a report
finding is blocking, `accepted` otherwise. A panel writes nothing, not even a review memory
([definition](panel.md)).

## Design

Spec review follows the ordinary step sequence of a worker-backed Operation, minus the writing
steps a `review-spec` grant makes moot. It validates Modules first, marking one `incomplete` on a
Spec core structural error rather than send a worker to judge a Spec that won't load; freezes one
grant per Module; launches one reviewer per Module; audits for changes; optionally runs the
checker; and derives the verdict ([step table](operation.md#host-sequence)).

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

**Review Operations** runs that sequence through Workers and returns the run's output, reviewing
Modules one after another in this version. It runs the Spec panel as well, sharing the first step
and the finding normalization with the Spec review.

<a id="realization.spec-review.checklist"></a>

**Reviewer brief** is the checklist every reviewer and checker receives — dimensions, what counts as
blocking, the one-pass rule, a finding's shape — plus, from the Operation, the role, the reviewed
Module's own documents, the workspace's goal and, for a checker, the numbered findings to check. The
checklist itself is a shared part, so that a panel judges by exactly the same bar.

<a id="realization.spec-review.panel"></a>

**Panel brief** is what every panel worker receives: the shared checklist and the roles of the
reviewers and the chair, plus, from the Operation, the role and seat or attempt, and for the chair
every labelled reviewer finding and, on its second attempt, its previous report and what it left
unaccounted.

### The review memory

A single reviewer's findings vary from run to run, so a review that forgot the one before it would
report again, in other words, problems the task has already seen, and would drop the ones it
happened not to notice this time. The review memory is the state that carries a Module's findings
from one review to the next: every finding its reviews kept, under a stable id `f.<n>` never
reused, with its content as last reported, whether it is open or resolved, the runs that first and
last reported or resolved it and, once resolved, the reason; and, under `reviewed`, the context identity of the
Specs the last completed review judged, with that review's run.

There is one tracked file per Module because the history belongs to the Module, as its Specs do,
and is bound to the same per-Module context identity as its outcome. A task that reviews a Module
changes only that Module's file, so tasks reviewing different Modules never touch the same file,
and a merged task brings the Module's history to every later task and collaborator.

The reviewer, not the Operation, matches a finding with an earlier one. Two reviews describe the
same problem in other words, at another anchor or with other evidence, and only a reader of the
Specs can tell that it is the same problem; a textual comparison would keep duplicates or merge
distinct problems. So the reviewer receives the open earlier findings, without the runs that
reported them, and names the earlier id it updates or resolves. The Operation keeps what no worker
may decide: it assigns ids, ignores a resolution that names no open finding, keeps an update of an
unknown finding as a new one, keeps out a finding the checker disputed, and derives the outcome
from the open findings alone, so a blocking finding stands until a review resolves it.

An unbound run never writes the memory. It works in an unbound checkout the runner removes before
the result, and writing into the worktree it started in, such as the primary worktree, would change
the shared history outside any task, with no delivery to account for it. A bound review writes the
file in its worktree and the delivery commits it with the rest of the task, so the history changes
only through a merged task. A review that skips the reviewer because the Specs are unchanged, and
an `incomplete` review, write nothing, so a failed review never records Specs as judged.

A memory the Operation cannot use, one that is not valid JSON, does not match the contract or names
another Module, makes only that Module's review `incomplete` with `review_memory_unusable`, naming
the file; the other Modules of the run are still reviewed and their memories written. The Operation
leaves that file as it is rather than overwrite a history it cannot read: repairing or removing it
is the task's decision.

For each Module, a repeated review runs through the memory like this
([step table](operation.md#host-sequence)):

```d2 illustrative
direction: down
read: "Read the Module's review memory"
usable: "Usable?" {shape: diamond}
same: "Records this context identity,\nwithout --force?" {shape: diamond}
skip: "Launch no reviewer;\nthe memory decides\n(unchanged_since)"
launch: "Launch the reviewer with\nthe open earlier findings,\nthen audit"
check: "Checker, with --check-findings\nand at least one finding"
merge: "Merge: new ids, updates,\nresolutions; disputed kept out;\nrecord the context identity and run"
outcome: "Outcome from the open findings" {shape: page}
bound: "Bound run?" {shape: diamond}
write: "Write the memory file;\ndelivery commits it"
nothing: "Nothing written" {shape: page}
unusable: "Module incomplete:\nreview_memory_unusable" {shape: page}

read -> usable
usable -> unusable: no
usable -> same: yes
same -> skip: yes
same -> launch: no
skip -> outcome
launch -> check -> merge -> bound
bound -> write: yes
bound -> nothing: no
write -> outcome
nothing -> outcome
```

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
[definition](panel.md#the-panel-graph) draws it. The graph lives inside the Operation's steps: to
its caller
`spec_panel` is an ordinary Operation with one result, and every reviewer and chair is an ordinary
worker run.

The Operation keeps what no worker may decide: it labels each reviewer finding, normalizes every
finding as a Spec review does, checks the chair's accounting and derives the outcome. A report that
loses a reviewer finding is sent back rather than repaired by the Operation, since only the chair
judges findings; after its second attempt the Module is `incomplete` with the reviews still in the
result. A reviewer that does not finish stops the panel before the chair, so that a report never
silently rests on fewer reviews than asked for.

A reviewer cannot widen its own view: lacking a needed document of another Module, it reports a
`context` finding naming it and goes on, and the task level decides whether the Spec lacks a
relation or the review needs another Module. A reviewer ends `blocked` only when it cannot review
at all, for example because the reviewed Module's own documents cannot be read. In this version,
reviewers read Specs directly under their grant, not the Spec MCP server, on one checklist covering
all dimensions; splitting by dimension and server queries are future work.

### Around it

Spec review stays inside Spec tooling but reaches outside it for everything a Spec cannot judge on
its own: it asks Spec core whether a Module can be reviewed at all, it reaches an agent only
through Workers, and it is run, like every Operation, by the Execution runner.

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
tooling.review -> execution.workers
tooling.review -> execution.operations
tooling.review -> execution
```

Operations also uses Spec review in turn, since `spec_review` is one of its own Operations —
declared and explained there, not here.

<a id="uses-spec"></a>

**Spec core**'s [structural checks](../../glossary.json#concept.structural-check) decide whether a
Module can be reviewed at all; its [grants](../../glossary.json#concept.grant) with
[context identities](../../glossary.json#concept.context-identity) fix, per Module and
[task type](../../glossary.json#concept.task-type) `review-spec`, exactly which Specs a reviewer may
read and bind the verdict to. A load failure fails the run, with the loading error as host evidence;
a rejected grant makes that Module's review `incomplete`.

<a id="uses-workers"></a>

**Workers**, in Execution, turn a frozen grant into a running worker: launch each reviewer, checker,
panel reviewer and chair with only its [brief](../../glossary.json#concept.brief), return its
[worker result](../../glossary.json#concept.worker-result) extended with findings, checks or a
panel report, audit for changes, and keep a
[run record](../../glossary.json#concept.run-record). A `blocked`/`failed` worker, or an audit
finding a change, makes that Module's review or panel `incomplete`, its error link travelling in the
result's [error chain](../../glossary.json#concept.error-chain) unchanged.

<a id="uses-operations"></a>

**Operations** defines the [Operation](../../glossary.json#concept.operation) concept and lists
`spec_review` and `spec_panel` in its catalog as Operations that may run unbound, `spec_review`
changing only the reviewed Modules' review memories in a bound run and `spec_panel` nothing, with
their [worker ids](../../glossary.json#concept.worker-id). Spec review relies on that entry to be
dispatched to with its arguments.

<a id="uses-execution"></a>

**Execution**'s [runner](../../glossary.json#concept.execution-runner) runs both Operations' steps
from `concorde run`: it reads the
[workspace binding](../../glossary.json#concept.workspace-binding), settles the Modules, admits the
inputs and fixes the [run result](../../glossary.json#concept.run-result) envelope in which Spec
review returns its verdict and findings. Spec review relies on it for the workspace's goal and
Modules and for knowing whether the run is unbound, which decides whether the review memory is
written; its duty is to fill the envelope honestly, keeping worker claims apart from its own
evidence.
