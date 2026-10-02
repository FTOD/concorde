# Understanding

## Purpose

Understanding lets callers learn what one or more Modules promise before anything changes, and have
a plan for changing them reviewed before it is followed. It provides two
[Operations](../../glossary.json#concept.operation). In `understand` a worker reads the bound
Modules' Specs and only the names of their code files, and answers a stated goal with what the
Modules promise, whether their [Spec](../../glossary.json#concept.spec) suffices, the
[Spec gaps](../../glossary.json#concept.spec-gap) if not, and, when asked, a plan. In the
optional `plan_review` a reviewer reads the Specs and the code and judges a plan the caller wrote
against the workspace's goal, reporting findings the caller answers in a next run. The caller relies
on them to plan work, to confirm a Spec repair closed a gap and to catch a wrong plan before it
costs a change. Understanding never changes a Spec or code file and never fills a missing promise
by guessing from code; `understand` never reads code contents; a plan is a proposal the caller may
follow, change or reject, and a review of it is advice the caller answers.

## Core concepts

### The assessment

The Operation returns a [run result](../../glossary.json#concept.run-result) whose `output` is an
**assessment**, defined by the
[assessment contract](contracts.md#contract.understanding.assessment): for each bound
[Module](../../glossary.json#concept.module), what it promises that matters for the goal, and
whether the Spec is **sufficient**. When it is and a plan was requested, the plan names the Modules
to change, the new files the change needs, which the task level creates and binds before the run
that fills them, the ordered next runs — the
Operations `understand`, `specify`, `implement`, `test`, `spec_review` and `code_review`, and the
[execution commands](../../glossary.json#concept.execution-command) `task-validation` and
`delivery` that end a task's work — and the open decisions left to the task level. Making the plan
has no separate Operation: breaking work into steps is one use of understanding. Reviewing a plan
has one, `plan_review` (see [Reviewing a plan](#reviewing-a-plan)), because it judges a plan the
caller wrote, which may start from this one, against the code as well as the Specs.

The Spec is sufficient when it states every promise the goal relies on. For a goal that asks what
the Modules promise, that is every promise the answer needs. For a goal that changes them, the
existing Specs must state every promise the change relies on and say where each new promise it
adds belongs, so that the change can be planned: the new promises become the plan's `specify`
steps and are never Spec gaps.

### Spec gaps

<a id="concept.spec-gap"></a>

When not sufficient, the assessment lists each **Spec gap** instead of a plan: a promise the goal
relies on that the Specs do not state, including where a new promise belongs when no bound Module's
Spec says so. Each names the Module and document where the promise belongs, what is missing, why the
goal needs it and a suggested repair. The usual next step is `specify` to close the gaps, then
another `understand` to confirm it.

Reading names but not contents is what makes a gap visible: the worker's
[implementation context](../../glossary.json#concept.implementation-context) holds only the file
names, so the only promises it can report are ones the Spec states, and a thin Spec is a Spec gap,
never inferred from code.

## Overview

A run ends in one of three statuses, and an `ok` assessment leads the task level to one of three
next steps; a gap usually goes through `specify` and back to `understand`:

```d2 illustrative
direction: down
worker: The worker assesses the goal
host: "The Operation checks launch, timeout, audit,\nknown Modules and consistency"
blocked: "blocked: goal not assessable" {shape: oval}
failed: "failed: not run, changed a file,\nunknown Module or inconsistent assessment" {shape: oval}
ok: "ok: an assessment" {shape: oval}
plan: "Follow the plan's runs,\nwhich may start with specify"
answer: "Use the answer"
gaps: "Read the Spec gaps"
specify: "specify closes the gaps"
worker -> host
worker -> blocked: "ambiguous goal, Modules not bound" {style.stroke-dash: 3}
host -> failed {style.stroke-dash: 3}
host -> ok
ok -> plan: "sufficient, --plan"
ok -> answer: "sufficient, no --plan"
ok -> gaps: not sufficient
gaps -> specify
worker <- specify: "understand again to confirm" {style.stroke-dash: 3}
```

## Running understand

The caller runs the Operation in a task worktree, usually before specifying or implementing:

```text
concorde run understand [--modules <module-id>[,<module-id>…]] --goal "<text>" [--plan] [--input <run-id>]…
```

The run works on the [workspace](../../glossary.json#concept.workspace) whose binding lies in the
worktree it starts in, and briefs the worker with that workspace's goal beside the run's own. In a
worktree without a binding, such as the primary worktree, it is an
[unbound run](../../glossary.json#concept.unbound-run) that answers a question before any task
exists; it then works on the Modules `--modules` names and admits only inputs of other unbound runs.
`--modules` names the worker's bound Modules (default: the binding's; an unbound run without it
fails at step 1 with `grant_unavailable`, since a grant needs a Module), `--goal` states what the
caller wants to know or do, `--plan` also asks for a plan, and `--input` admits an earlier `ok`
run's output as material, which the brief carries beside the goals. For example, `--modules
module.issues --goal "let reports carry a severity" --plan` has the worker answer with either a plan
(`specify`, `implement`, `test`, `code_review`, `task-validation`, `delivery`) or the Spec gaps that
block it.

### Statuses

`status` is `ok` whenever the worker completed an assessment, sufficient or not; `sufficient` says
whether work may proceed. It is `blocked` when the worker could not assess the goal at all — an
ambiguous goal, or Modules not bound — and the
[error chain](../../glossary.json#concept.error-chain) ends in the worker's own link with
what it tried and would need. It is `failed` when the worker could not be run or changed a file,
with Workers' launch, timeout or audit error as the cause of the Operation's link, as for every
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence). It is also
`failed` when the assessment names an unknown Module or is internally inconsistent (gaps and
sufficiency, or plan and `--plan`, disagree; a bound Module has no entry or more than one; an entry
names a Module that is not bound): the Operation's own link then has the code `unknown_modules` or
`inconsistent_assessment`, lists every unknown Module or every inconsistency, and gives
`capability` as its reason — the Operation checks the assessment but never corrects it or
relaunches the worker. A failed or blocked result carries no `output`; the worker's own answer
stays in the `worker` field. Running the Operation again with the same inputs is safe.

## Reviewing a plan

`plan_review` is optional: nothing requires it before a task's validation or delivery, and the
caller runs it when a change deserves a second reading of its plan before any Spec or code changes.
The caller writes the plan itself, in its own words and shape, possibly starting from an
`understand` plan; one reviewer, [worker id](../../glossary.json#concept.worker-id) `reviewer`, reads it with the bound Modules' Specs and
the project's code and reports every problem it can establish, in one pass, as findings. The
reviewer changes nothing and its model comes from the
[worker configuration](../../glossary.json#concept.worker-configuration) like every worker's.

### The discussion

A plan is discussed over several runs, which the caller leads; the Operation never loops. Each run
is one **iteration**: the caller answers every finding of the previous iteration, accepting it and
revising the plan or rejecting it with its reason, and runs `plan_review` again with the revised
plan, the previous run as `--input` and the answers. The reviewer then sees its earlier findings
and the answers, says for each earlier finding whether it is **settled**, by the revision or by the
reason given, or **maintained**, restating a maintained one as a finding of this iteration, and
reports what else it finds. The discussion ends when the **verdict** is `accepted`, which it is
exactly when no finding of the iteration is blocking; the caller takes a disagreement it cannot
settle itself, such as a finding the reviewer maintains after the caller rejected it, to whoever
decides above it, and states that decision in its next answer.

```d2 illustrative
direction: down
write: "Caller writes the plan"
review: "plan_review: the reviewer judges the plan\nagainst goal, Specs and code"
verdict: "Verdict" {shape: diamond}
follow: "Follow the plan" {shape: oval}
answer: "Caller answers every finding:\naccept and revise, or reject with a reason"
escalate: "Caller takes a maintained disagreement\nto whoever decides above it"
write -> review
review -> verdict
verdict -> follow: accepted
verdict -> answer: changes_required
answer -> review: "next iteration: --input the previous run,\n--accept / --reject"
answer -> escalate: "cannot settle it itself" {style.stroke-dash: 3}
escalate -> answer: "the decision, stated in the answer" {style.stroke-dash: 3}
```

### Findings

Each finding of the [plan review report](contracts.md#contract.understanding.plan-review) is
blocking, when following the plan unchanged would miss the goal or break a promise, or advisory,
and names its kind: the plan misses the goal or part of it (`goal`), a planned step would break a
promise a Spec states (`violation`), the plan relies on a promise the Specs do not state or adds one
without a step that states it (`spec-gap`), the plan misjudges the existing code (`code`), the plan
changes something outside the bound Modules or the goal (`scope`), or its steps are missing, in an
order that cannot work or leave a new file uncreated before the worker that fills it (`sequence`).
A finding may name its **basis**, a stable identity or Spec passage of the bound Modules'
[Spec context](../../glossary.json#concept.spec-context); a `violation` always does. The
reviewer judges the plan against the goal, the Specs and the code as they are, never against taste.

### Running plan_review

```text
concorde run plan_review --plan <file> [--modules <module-id>[,<module-id>…]] [--input <run-id>]…
                         [--accept <finding> "<how the plan settles it>"]… [--reject <finding> "<why>"]…
```

The run needs a [workspace](../../glossary.json#concept.workspace): it reviews the plan against
the goal of the workspace whose binding lies in the worktree it starts in, so it never runs
unbound. `--plan` names the plan file, relative to that worktree or absolute; the Operation keeps an
exact copy of it as `plan.md` in the run's [trace node](../../glossary.json#concept.trace-node),
so the file may be changed or removed afterwards. `--modules` names the bound Modules (default: the
binding's). `--input` admits earlier `ok` runs of the workspace as material: at most one of them is
a `plan_review` run, the **previous iteration**, and every other, such as the `understand` run the
plan started from, is given to the reviewer as it is. `--accept` and `--reject` answer the previous
iteration's findings, each once, by their ids. For example, after a first review found `F1` and
`F2`, `--plan plan.md --input <first run> --accept F1 "step 3 now creates the file first" --reject
F2 "the Spec already states the retry limit in req.payments.retry"` starts the second iteration.

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | review completed, any verdict |
| `blocked` | `worker_blocked` | `decision` | the reviewer could not judge the plan at all, such as a plan about Modules it cannot read |
| `failed` | a code of the [worker sequence](../workers.md#errors-of-the-worker-sequence) | as that table gives | the grant could not be computed, the reviewer could not be run, or the audit found a change |
| `failed` | `plan_unreadable` | `input` | the plan file is missing, unreadable, not UTF-8 text or empty |
| `failed` | `iteration_mismatch` | `input` | more than one `plan_review` input, a previous finding not answered exactly once, an answer to no previous finding, or an answer without a previous iteration; lists every problem |
| `failed` | `unresolved_basis` | `capability` | a basis that does not resolve in the bound Modules' Spec context, or a `violation` without one; names every such finding |
| `failed` | `inconsistent_review` | `capability` | responses not exactly one per previous finding, a maintained finding not restated exactly once, a restated finding that continues no maintained one, or a finding about a Module that is not bound; lists every inconsistency |

The two `input` failures stop the run before the reviewer launches. Only an `ok` run carries a
report; the reviewer's own answer stays in the `worker` field of every run it reached.

### How plan_review is built

The Operation is worker-backed with [task type](../../glossary.json#concept.task-type)
`review-code`, which gives the reviewer the bound Modules' Spec context and external material and
the whole project's implementation to read, and nothing to write. The plan, the previous
iteration's findings with the answers and the other inputs are
[task context](../../glossary.json#concept.task-context) in the brief; they add no source.

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Read the plan, keep its copy in the run's trace node and record its digest | Operation | unreadable or empty plan (`failed`) |
| 2 | Settle the iteration: the previous `plan_review` input and the answers to its findings | Operation | `iteration_mismatch` (`failed`) |
| 3 | Compute and freeze the `review-code` [grant](../../glossary.json#concept.grant); generate settings, tools and the [brief](../../glossary.json#concept.brief) | Operation, Spec core, Workers | Specs cannot load or unknown Module (`failed`) |
| 4 | Launch the reviewer and wait for its [worker result](../../glossary.json#concept.worker-result) | Workers, worker | launch error or timeout (`failed`); `blocked` passed on |
| 5 | [Audit](../../glossary.json#concept.write-audit): read-only grant, so any change is a violation; write the [run record](../../glossary.json#concept.run-record) | Workers | any change (`failed`) |
| 6 | Resolve every basis, check the responses and findings against the previous iteration, derive the verdict | Operation, Spec core | unresolved basis or inconsistency (`failed`) |
| 7 | Return the report as the run's output | Operation, Execution runner | — |

The reviewer has the same reading tools as the understand worker. No
[configured check](../../glossary.json#concept.configured-check) runs and the
reviewer is never resumed: a plan changes no code, and every blocking finding is due in one pass,
as in a code review. The Operation keeps the findings and responses as the reviewer's claims,
verifying only what it can decide: the bases, the consistency with the previous iteration and the
verdict that follows.

## How understand is built

`understand` is worker-backed, run with [task type](../../glossary.json#concept.task-type)
`understand`, which gives the worker the bound Modules'
[Spec context](../../glossary.json#concept.spec-context) and external material to read, only the
file names of their implementation context, and nothing to write.

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `understand` [grant](../../glossary.json#concept.grant) | Operation, Spec core | Specs cannot load, no Module named, or unknown Module (`failed`) |
| 2 | Generate settings, tools and the [brief](../../glossary.json#concept.brief) | Workers | — |
| 3 | Launch the worker and wait for its [worker result](../../glossary.json#concept.worker-result) | Workers, worker | launch error or timeout (`failed`) |
| 4 | [Audit](../../glossary.json#concept.write-audit): read-only grant, so any change is a violation; write the [run record](../../glossary.json#concept.run-record) | Workers | any change (`failed`) |
| 5 | Check every named Module exists in the Specs of the worktree the run works on and the assessment is consistent | Operation | unknown Module or inconsistency (`failed`) |
| 6 | Return the assessment as the run's output | Operation, Execution runner | — |

The worker gets only its [worker backend](../../glossary.json#concept.worker-backend)'s reading
tools (Read, Glob and Grep on Claude Code; `read`, `grep`, `find` and `ls` on pi) — no editing,
shell or web tool and no MCP server. Checks are not run, since nothing is writable or executed; a malformed assessment is not repaired either, so every accepted
assessment is one reading of one frozen grant.

The Operation treats the assessment as the worker's claim, verifying only what it can decide from
declarations and the assessment's own shape, then adds its own evidence, the **host evidence** of
the run result: grant, [context identity](../../glossary.json#concept.context-identity), audit
and transcript path, and every unknown Module or inconsistency it finds. Whether a plan is good is
for the caller and later Operations, such as `plan_review`, to find out. See the [requirements](requirements.md) and
[scenarios](scenarios.md).

<a id="realization.understanding.operation"></a>

The **Understanding Operations** realization holds both Operations' steps, worker instructions and
result schemas in `src/concorde/understanding/` (`operation.py` declares the `UNDERSTAND` provider,
`plan_review.py` the `PLAN_REVIEW` provider) with the prompts `prompts/workers/understand.md` and
`prompts/workers/plan-review.md`, tested against a fake worker.

## What it relies on

<a id="uses-operations"></a>

**Operations**, Execution's Operation framework, is what both Operations plug into: Method registers
their definitions with it, `understand` as an Operation that may run unbound and writes nothing,
`plan_review` as one that needs a workspace and writes nothing, both naming this Module as their
provider ([Method](../module.md#the-operations-and-commands-it-provides)), and Execution's
[Operation catalog](../../glossary.json#concept.operation-catalog) lists them from there.
Understanding never calls another Operation, and neither of its Operations calls the other.

<a id="uses-execution"></a>

**Execution**'s [runner](../../glossary.json#concept.execution-runner) runs the Operation's
steps: it reads the [workspace binding](../../glossary.json#concept.workspace-binding), settles
the Modules and inputs, and wraps the assessment or the plan review report in the run result.
Understanding relies on it for the workspace's goal and Modules, for the run's trace node, where
`plan_review` keeps its copy of the plan, for refusing a `plan_review` run without a workspace
binding, and for refusing an input that is not an `ok` run of the same workspace, or, for an
unbound run, of no workspace.

<a id="uses-workers"></a>

**Workers**, in the worker harness, receives the frozen grant as data through Method's
[standard worker sequence](../../glossary.json#concept.standard-worker-sequence), turns it into
settings, launches the worker with this Module's instructions, collects its worker result, audits
the worktree and writes the run record. Any audit violation is a failed run. The task instructions
Method composes for every worker tell the understand worker never to infer a promise the Spec does
not state but to report it as a Spec gap and end `ok`; this Module's instructions say the same,
since for this worker a missing promise is the finding itself: it reports the promise in an `ok`,
insufficient assessment, which infers nothing, and returns `blocked` only when it cannot assess the
goal at all. For the `plan_review` reviewer, whose task type is `review-code`, those instructions
say to report such behaviour as a `spec-gap` finding, which this Module's instructions repeat.

<a id="uses-spec"></a>

**Spec core** computes the `understand` and `review-code` grants, resolves Module identities for
`understand`'s step 5 and the bases of `plan_review`'s findings, always from the Specs of the
worktree the run works on.
