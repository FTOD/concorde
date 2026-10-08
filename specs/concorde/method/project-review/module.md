# Project review

## Purpose

Project review judges a whole project in one run. It provides one
[Operation](../../glossary.json#concept.operation), `project_review`. The Operation combines what
the other reviews judge one Module at a time:

- The whole project's structural validation.
- Every [configured check](../../glossary.json#concept.configured-check) of the reviewed
  [Modules](../../glossary.json#concept.module).
- The scenarios no test verifies.
- The files no Module binds.
- One architecture review of the whole project.
- A Spec panel per Module, of reviewers and a chair.
- A Module-scope code review per Module.

Its caller is the [main agent](../../glossary.json#concept.main-agent) or a
[task session](../../glossary.json#concept.task-session) that wants
to know how the whole project stands. The Operation runs unbound in the primary worktree, without a
task, or in a bound workspace. It changes no [Spec](../../glossary.json#concept.spec) or code. Where
the issues part is installed, it records every problem it finds as an
[Issue](../../glossary.json#concept.issue). It returns an outcome per Module and one verdict for the
project.

A review of 37 Modules launches about 190 workers. A project changes a few Modules between two
reviews. So the Operation skips each part of a Module's review whose input is unchanged since the
part was last judged. It keeps what was last judged in a **review record** on the primary branch.

## Core concepts

### One review of the project

One run of `project_review` covers the Modules `--modules` names. Without `--modules`, it covers
every Module the examined worktree registers. It judges them in these parts:

| Part | What it judges | Workers |
| --- | --- | --- |
| Validation | the whole project's structure, by Spec core's [structural checks](../../glossary.json#concept.structural-check) | none |
| Checks | every configured check of every covered Module, except a check marked to run only when readiness is decided | none |
| Coverage | the scenarios of every covered Module that no [verification declaration](../../glossary.json#concept.verification-declaration) names | none |
| Unowned files | the files Git tracks that no Module binds | none |
| Architecture review | every Module's place among the others, once for the project | `architect1`, `architect2`, `arch_chair` |
| Spec panel | each covered Module's own Specs | `reviewer1` … `reviewer5`, `chair` |
| Code review | each covered Module's whole code against its Specs | `code_reviewer` |

The first four parts are deterministic. They run on every run that is not refused. The last three
launch workers. Each of them is skipped when what it would judge is unchanged since it was last
judged. When every one of them would be skipped, the run has nothing to review. Its admission
refuses it with `nothing_to_review` before any step. It runs no check and writes no Issue and no
record. `--full` reviews the parts anyway.

The architecture review is a Spec panel with architects and a chair but no reviewers. Its reviewed
subject is the whole project: every Module's documents may carry a blocking finding. Each finding
belongs to the Module whose document it cites. A Module's own Spec panel has reviewers and a chair
but no architects, since the architecture review judges every Module's place once. A Module's code
review is a [Code review](../code-review/module.md) of Module scope.

Every worker has its own [worker id](../../glossary.json#concept.worker-id). The
[worker configuration](../../glossary.json#concept.worker-configuration) may therefore give each a
backend, model and level of its own under `operations.project_review`.

### The review record

The **review record** is the file `.concorde/reviews/record.json` of the primary branch. For each
Module, it keeps what the Module's last Spec panel and last code review judged. It also keeps what
the last architecture review judged. Each entry holds these items:

- The identity of what was judged.
- The run that judged it.
- The commit that run examined.
- The time.

The identity of each part is computed by the Operation from the examined worktree:

| Part | Its identity |
| --- | --- |
| Spec panel | the [context identity](../../glossary.json#concept.context-identity) of the Module's `review-spec` [grant](../../glossary.json#concept.grant) |
| Code review | the context identity of the Module's `review-code` grant, and the **code digest** of the Module |
| Architecture review | the context identity of the `review-architecture` grant of every Module |

The [record contract](contracts.md#contract.project-review.record) defines the code digest exactly.
It changes whenever a file the Module binds changes, appears or disappears. A context identity changes whenever a Spec source it selects changes. The code
digest changes whenever a bound file changes. A code reviewer may read every Module's code, but only
its own Module's code decides whether it is judged again. A change of another Module's code is
judged by that Module's own code review. A part whose identity equals the recorded one is **skipped**. Each
identity is a digest of content, not of a place. So a record entry holds wherever the content was
judged: in a task's workspace, in the primary worktree or by another collaborator.

Each entry also lists the earlier Issues its part found resolved, each with the
[revision](../../glossary.json#concept.issue-revision) the part was offered. One rule holds for
every resolution, of this run or remembered: it counts only while the Issue's revision equals the
one offered. An Issue that took a
report after the part read it is not listed, since its resolution judged older content. A skipped
part did not judge again, so the resolutions of its last judgment still hold. An Issue it found
resolved therefore does not stand while its revision is unchanged. Only a task closes it. An Issue
with a newer report stands again. When the open Issues cannot be listed to bind the resolutions,
nothing is recorded.

The record is Git-tracked. It is shared by every worktree and collaborator of the project. It is
read from the primary worktree's last commit. It is never read from the examined checkout. After the
reviews, the Operation merges the parts this run completed into the record. A part is completed
when its workers finished and all of its Issues were written. The Operation commits the record alone
on the primary branch under the [merge lock](../../glossary.json#concept.merge-lock), as an Issue
write commits its record. The examined checkout stays untouched.

The record changes only through such a commit. Every run that could skip and is not refused takes
the merge lock once
to check the record, even when it has nothing new to record. When the record file holds a valid
record no commit holds, a write was interrupted after it published the file. The run puts that file
back first. It refuses any other change of the file with `uncommitted_change`, changing nothing. When the
committed record is not valid, nothing is skipped, and the write refuses with `record_invalid`.

While it holds the merge lock, the record's write first reads the Kernel's
[unfinished-merge marker](../../glossary.json#concept.unfinished-merge-marker). While the marker is
present, a merge into the primary branch is unfinished, such as a task merge whose process ended
before its checks decided. The write then refuses with `merge_incomplete`, carrying the Kernel's
account of the merge, and commits nothing. A marker that cannot be read refuses the write with
`unreadable_merge_marker`. Thus, no record lands between a merge commit and its checks, where it
would keep `task merge --resume` and `--abort` from finishing the merge. The marker is Kernel
state. The Operation reads no [task record](../../glossary.json#concept.task-record), as no
Operation does ([req.concorde.halves-apart](../../requirements.md#req.concorde.halves-apart)). The
run's Issue writes refuse an unfinished merge themselves, which makes those parts incomplete and
unrecorded.

A skipped part changes no Issue. Its Module's outcome comes from the Issues that stand. That is
why skipping needs the issues part. Where the issues part is not installed, nothing is skipped and
no record is written. `--full` reviews every part whatever the record says. It still records what
it judged.

### Deterministic findings

Three problems need no worker to establish:

- A configured check that failed or timed out.
- The scenarios of a covered Module that no verification declaration names. The Operation reads the
  declarations of every file a Module binds, as structural validation does. It counts a scenario of
  a Module without code too.
- The files Git tracks that no Module binds. When Git cannot list them, they are not examined.

Each is reported as an Issue of a fixed title, tier and severity, which
[req.project-review.deterministic-issues](requirements.md#req.project-review.deterministic-issues)
gives. A failed check is an obvious problem whose fix the task fixing it finds in the log. A timed-out
check may be an environment problem as well as a code problem, so its fix is uncertain. A scenario
no test verifies has an obvious fix: a test that declares it. A file no Module binds needs a
decision about the Module it belongs to.

A file is bound to no Module by [Validation](../validation/module.md)'s rule for a changed path:
the file is none of these:

- A member of a Spec document or the glossary.
- A control record under `.concorde/`.
- A generated or build output.
- External material.
- A file a Module binds.

Submodules are left out.

The **earlier Issue** of a deterministic problem is the open Issue that meets all of these
conditions:

- It is of the same Module.
- A `project_review` report of the same kind made it.
- It has the same title.

The Operation, not a worker, settles them:

- When the problem's text, tier and severity are unchanged, its earlier Issue is carried. Nothing
  is written.
- When they changed, the Operation appends a report to the earlier Issue.
- When there is no earlier Issue, it creates one.
- When the run examined the Module's problems of that kind and none has the Issue's title, the
  Issue is listed as resolved. One check repaired while another still fails resolves the repaired
  check's Issue alone. A check removed from the configuration no longer fails, so its Issue is
  resolved too. Checks that could not run, or files Git could not list, were not examined, so
  their Issues are carried.

The Operation closes no Issue.

### The kinds of review in one Operation's Issues

The reports of one `project_review` run are of six kinds. Each kind is its report's provenance
`phase`:

| Phase | Reports of |
| --- | --- |
| `spec-panel` | a Module's Spec panel |
| `code-review` | a Module's code review |
| `architecture` | the architecture review |
| `check` | a configured check that did not pass |
| `coverage` | a Module's scenarios no test verifies |
| `unowned` | the tracked files bound to no Module |

The phase decides which reviews offer an Issue as an earlier Issue:

- A Module's Spec panel offers the Module's Issues of `spec_panel`'s `report` phase and of the
  `spec-panel` phase.
- `spec_panel` offers the Module's Issues of `spec_panel`, whatever their phase, and those of the
  `spec-panel` and `architecture` phases, since it has architects
  ([Spec review](../spec-review/panel.md#earlier-issues)).
- A Module's code review offers its Issues of `code_review` and of the `code-review` phase, as
  `code_review` does ([Code review](../code-review/module.md#earlier-issues)).
- The architecture review offers every open Issue of the `architecture` phase, of
  `project_review` and of `spec_panel`. `spec_panel` reports with that phase its architects'
  findings, whose every merged label is an architect's
  ([Spec review](../spec-review/panel.md#reporting-findings)). A Module's Spec panel in this
  Operation has no architects, so it does not offer them.

Thus `project_review`, `spec_panel` and `code_review` build on each other's Issues rather than
reporting a problem again. Within one run, the report key of a phase other than `report` begins with
that phase. Thus a Module's panel and code review never reuse each other's key.

### Outcomes and the verdict

After every part, the Operation reads the open Issues that a review made: `spec_panel`,
`code_review` or `project_review`. An Issue that a part of this run found resolved does not stand.
Every other such Issue **stands** for the Module that owns it. A Module's outcome has these values:

- `incomplete`, when it failed structural validation, its Spec panel or code review stopped, or its
  Issues could not all be written.
- `changes_required`, when an Issue of a blocking tier stands for it.
- `accepted`, otherwise.

A Module is also `incomplete` when its checks could not run, when one of its deterministic
problems could not be written, or when an architecture finding about it could not be written.

`--modules` narrows which Modules the run covers. The Issues that stand are counted for the covered
Modules alone. An architecture finding about a Module the run does not cover stands for that Module.
It counts in the next run that covers it. A Module that fails structural validation is still judged
by the architecture review, which reads every Module's Specs as they are written.

The project's verdict is the highest Module outcome in the order `accepted`, `changes_required`,
`incomplete`. It is also `incomplete` in these cases:

- The architecture review stopped.
- The checks could not run.
- The deterministic findings could not all be written.
- The Issues that stand could not be read.

The result counts the Issues that stand by [severity](../../glossary.json#concept.issue-severity)
and by [tier](../../glossary.json#concept.issue-tier). Where the issues part is not installed, each
Module's outcome follows from this run's findings, exactly as from the Issues they would become.

## Overview

```d2 illustrative
direction: down
prepare: "Validate the project; compute each part's identity;\nread the review record; decide the skips"
deterministic: "Run every covered Module's checks; find uncovered\nscenarios and unowned files; settle and report"
architecture: "Architecture review, once\n(skipped when every Spec is unchanged)"
modules: "Per Module, at most --parallel at once:\nSpec panel and code review,\neach skipped when its input is unchanged"
record: "Merge the completed parts into the review record;\ncommit it under the merge lock"
verdict: "Each Module's outcome from the Issues that stand;\nthe project verdict" {shape: page}
prepare -> deterministic -> architecture -> modules -> record -> verdict
```

## Running project_review

```text
concorde run project_review [--modules <id>,…] [--full] [--parallel <1-8>] [--reviewers <2-5>] [--architects <0-2>]
```

| Argument | Meaning | Default |
| --- | --- | --- |
| `--modules` | the Modules whose checks, coverage, Spec panel and code review the run covers | every registered Module |
| `--full` | review every part whatever the record says | off |
| `--parallel` | how many Spec panels and code reviews run at the same time | 2 |
| `--reviewers` | the reviewers of each Spec panel | 3 |
| `--architects` | the architects of the architecture review; 0 leaves it out | 2 |

Each Spec panel runs its reviewers at the same time, so one Module's review keeps several workers
busy at once. Workers that share one model provider can meet its concurrency limit. The default
`--parallel` of 2 keeps the run's workers fewer than that limit usually allows.
[Workers](../../worker-harness/workers/launch.md#retries) retries a round that such a limit ended
anyway.

In the primary worktree, the run is an [unbound run](../../glossary.json#concept.unbound-run). It
examines the worktree's `HEAD` in its [unbound checkout](../../glossary.json#concept.unbound-checkout).
In a task worktree, it examines the bound [workspace](../../glossary.json#concept.workspace), its
uncommitted changes included. Either way, its Issues and the review record go to the primary branch.
The command waits for the result. Start it in background Bash.

When every worker part would be skipped, the run is refused with `nothing_to_review` before any
step. Its result is `failed`, and its error names `--full`.

The run's status is `ok` when every part completed and the record was written or had nothing new.
Otherwise it is `blocked` or `failed`, with an [error chain](../../glossary.json#concept.error-chain)
that has one cause per part that did not complete. The output carries the verdict either way. The
caller handles the Issues that stand by their tier, as the
[main-session guidance](../../coordination/main-session/module.md#issues) says. Fixing them is later
work of a task. It is never the review's.

## How it is built

The Operation is worker-backed. The [Execution runner](../../glossary.json#concept.execution-runner)
runs it with [task type](../../glossary.json#concept.task-type) `review-spec`. Each worker runs under
the grant of its own part's task type:

- `review-spec` for a Spec panel's reviewers and chair.
- `review-architecture` of every Module for the architects and their chair.
- `review-code` for a code reviewer.

It may run unbound, since it launches only reading workers.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Admit every worker against the worker configuration and the [model map](../../glossary.json#concept.model-map) | Method | a worker cannot be configured (`failed`) |
| 2 | Validate the whole project. Compute each covered Module's identities and the architecture's. Read the review record. Decide what is skipped. The Operation's admission does this work before step 1 and the step returns what it found | Operation, Spec core | every worker part skipped (refused with `nothing_to_review` before any step); Specs that do not load, Issues that cannot be read (`failed`); a Module with a structural error or no grant is `incomplete` and not reviewed; a record that cannot be read skips nothing |
| 3 | Run every covered Module's configured checks of the work stage. Find the uncovered scenarios and the unowned files. Settle them with their earlier Issues and report them | Operation, Check execution, Issues | — (checks that cannot run, or a refusal of the Issue store, make the project and the Modules concerned `incomplete`) |
| 4 | Unless skipped or left out, run the architecture review: read its earlier Issues, run the panel graph without reviewers, report the chair's findings with phase `architecture` | Operation, Workers, Issues | — (a stop, a grant that cannot be computed or LangGraph missing makes the project `incomplete`) |
| 5 | Run every Spec panel and code review not skipped, at most `--parallel` at once. A Spec panel runs as `spec_panel` runs one Module's panel without architects, with phase `spec-panel`. A code review runs as `code_review --scope module` reviews one Module, with phase `code-review` | Operation, Workers, Issues | — (a stop makes that Module `incomplete`) |
| 6 | Merge the completed parts into the review record and commit it on the primary branch | Operation, Kernel | — (a refusal fails the run with `record_unpublished`; the verdict stands) |
| 7 | Read the Issues that stand. Derive each Module's outcome and the verdict. Return the result | Operation, Issues | — |

The parts share no worker and no Module state. So they may run at the same time. The Issue store
takes the merge lock for each write, so their reports never interleave.

<a id="realization.project-review.operation"></a>

The **Project review Operation** realization, `src/concorde/method/project_review/`, holds these:

- The Operation's steps, its arguments and its result schema.
- The deterministic findings and their Issues.
- The review record: its schema, how it is read and how it is published.
- The tests.

It reuses the parts of Spec review and Code review that judge one Module. It never calls another
Operation.

<a id="realization.project-review.architecture"></a>

The **Architecture brief**, `prompts/workers/project-architecture.md`, follows the Panel brief in the
brief of every architect and chair of the architecture review. It tells them that the reviewed
subject is the whole project. It names what to look for first.

## Why it is built this way

**One Operation, not a workflow.** A workflow orders runs of one bound workspace, one at a time.
A project review needs neither a task nor a workspace. Its parts must run at the same time. One
Operation runs them all in one unbound run and returns one result. It still calls no other
Operation. It reuses their host code instead.

**One architecture review, not one per Module.** An architect judges a Module's place among all
Modules. It reads every Module's Specs for each Module it judges. Two architects per Module would
read the whole project twice for every Module. One architecture review reads it twice in all.

**A record of content identities, not of commits.** A commit says nothing about which Module
changed. A context identity and a digest of the bound files change exactly when a Module's Specs or
code change. So an entry needs no history to compare. It holds wherever the content was judged.

**The record is committed like an Issue.** The developer decided that a review's memory is tracked
in Git and shared by every collaborator. An unbound run may change nothing in what it examines. It
may only publish through a commit of its own under the merge lock. Execution allows exactly two such
publications: the Issues and this record
([req.execution.unbound-origin-untouched](../../execution/requirements.md#req.execution.unbound-origin-untouched)).

**Nothing to review is a refusal.** An Operation launches a worker in every run it does not refuse
([req.concorde.operations-are-ai](../../requirements.md#req.concorde.operations-are-ai)). A run
whose every worker part is skipped would launch none. The Issues that stand already give every
outcome of such a run. So the developer decided that the Operation refuses it before any step,
rather than run only its deterministic parts.

**Checks run on every run.** A Module whose own code is unchanged can still fail its tests when a
Module it uses changes. Checks cost no model spend. So they run for every covered Module, skipped
or not.

## What it relies on

<a id="uses-spec-review"></a>

**Spec review** provides the Spec panel that `project_review` runs for each Module and, without
reviewers, for the architecture. Project review relies on Spec review's host code for these:

- Validating the whole project, and stopping a Module that fails it.
- The panel graph, its accounting and its chair's second attempt.
- Normalizing findings and reporting them with a given provenance phase.
- Settling the earlier Issues a report names.

It relies on the [panel payload](../spec-review/panel.md#contract.spec-review.panel-payload) for the
shape of each panel in its result.

<a id="uses-code-review"></a>

**Code review** provides the Module review that `project_review` runs for each Module. Project review
relies on it for the reviewer's brief, the evidence check of every finding and the
[Issue reports](../../glossary.json#concept.issue-report) with a given provenance phase. It relies on the
[code review report](../code-review/contracts.md#contract.code-review.review) for the shape of each
Module's code review in its result.

<a id="uses-spec"></a>

**Spec core** loads the examined worktree's Specs. It validates their structure and reports the
scenarios no test verifies. It computes every grant and context identity. It lists the files each
Module binds and the root Module.

<a id="uses-workers"></a>

**Workers**, in the worker harness, launches every reviewer, architect, chair and code reviewer
through Method's [standard worker sequence](../../glossary.json#concept.standard-worker-sequence),
audits the worktree after each and writes its [run record](../../glossary.json#concept.run-record).

<a id="uses-checks"></a>

**Check execution** runs every covered Module's configured checks in its
[read-only check boundary](../../glossary.json#concept.read-only-check-boundary). It returns a
[check result](../../glossary.json#concept.check-result) for each.

<a id="uses-operations"></a>

**Operations**, Execution's Operation framework, is what `project_review` plugs into. Method
registers it as an Operation that writes nothing and may run unbound, with its worker ids
([Method](../module.md#the-operations-and-commands-it-provides)).

<a id="uses-execution"></a>

**Execution**'s runner runs the steps. It reads the
[workspace binding](../../glossary.json#concept.workspace-binding), creates the unbound checkout and
wraps the output in the [run result](../../glossary.json#concept.run-result). Project review relies
on it for the worktree the run started in, whose primary worktree keeps the Issues and the record.

<a id="uses-kernel"></a>

**Kernel** provides the [merge lock](../../glossary.json#concept.merge-lock) the record's commit
holds, the [unfinished-merge marker](../../glossary.json#concept.unfinished-merge-marker) it reads
under that lock and the [file transaction](../../glossary.json#concept.file-transaction) that
publishes the record. Project review relies on the marker's writer writing it before a merge touches
the primary branch and removing it only once the merge is decided.

<a id="uses-issues"></a>

**Issues** is an [optional integration](../../glossary.json#concept.optional-integration). Project
review reaches it only through the issues part's
[bookkeeping command](../../issues/interface.md#bookkeeping-command), as every review does. Where it
is installed, it keeps the project's Issues, which every part reads and writes. Where it is not
installed, every finding stays in the result, nothing is skipped and no record is written. A
failure of the Issue system is never reported as an Issue. It stays an error chain in the result.

<a id="uses-validation"></a>

**Validation** gives the rule by which a changed path is accounted for in a
[readiness](../../glossary.json#concept.readiness). Project review applies the same rule to every
tracked file to find the files bound to no Module.

<a id="uses-workflows"></a>

**Workflows** defines the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output). The result
carries its `workflow` object, with one review note, as every review's does.
