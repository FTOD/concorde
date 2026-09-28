# Understanding

## Purpose

Understanding lets callers learn what one or more Modules promise before anything changes. It
provides the `understand` [Operation](../../../glossary.json#concept.operation): a worker reads the
bound Modules' Specs and
only the names of their code files, and answers a stated goal with what the Modules promise, whether
their [Spec](../../../glossary.json#concept.spec) suffices, the
[Spec gaps](../../../glossary.json#concept.spec-gap) if not, and, when asked, a plan. The caller
relies on it to plan work and confirm a Spec repair closed a gap. Understanding never changes a Spec
or code file, never reads code contents and never fills a missing promise by guessing from code; a
plan is a proposal the caller may follow, change or reject.

## Usage

The caller runs the Operation in a task worktree, usually before specifying or implementing:

```text
concorde run understand [--modules <module-id>[,<module-id>…]] --goal "<text>" [--plan] [--input <run-id>]…
```

The run works on the [workspace](../../../glossary.json#concept.workspace) whose binding lies in the
worktree it starts in, and briefs the worker with that workspace's goal beside the run's own. In a
worktree without a binding, such as the primary worktree, it is an
[unbound run](../../../glossary.json#concept.unbound-run) that answers a question before any task
exists; it then works on the Modules `--modules` names and admits only inputs of other unbound runs.
`--modules` names the worker's bound Modules (default: the binding's; an unbound run without it
fails at step 1 with `grant_unavailable`, since a grant needs a Module), `--goal` states what the
caller wants to know or do, `--plan` also asks for a plan, and `--input` admits an earlier `ok`
run's output as material, which the brief carries beside the goals. For example, `--modules
module.issues --goal "let reports carry a severity" --plan` has the worker answer with either a plan
(`specify`, `implement`, `test`, `code_review`, `task-validation`, `delivery`) or the Spec gaps that
block it.

The Operation returns a [run result](../../../glossary.json#concept.run-result) whose `output` is an
**assessment**, defined by the
[assessment contract](contracts.md#contract.understanding.assessment): for each bound
[Module](../../../glossary.json#concept.module), what it promises that matters for the goal, and
whether the Spec is **sufficient**. When it is and a plan was requested, the plan names the Modules
to change, the files to declare as pending entries and where, the ordered next runs — the
Operations `understand`, `specify`, `implement`, `test`, `spec_review` and `code_review`, and the
[execution commands](../../../glossary.json#concept.execution-command) `task-validation` and
`delivery` that end a task's work — and the open decisions left to the task level. The plan has
no separate Operation: breaking work into steps is one use of understanding.

The Spec is sufficient when it states every promise the goal relies on. For a goal that asks what
the Modules promise, that is every promise the answer needs. For a goal that changes them, the
existing Specs must state every promise the change relies on and say where each new promise it
adds belongs, so that the change can be planned: the new promises become the plan's `specify`
steps and are never Spec gaps.

<a id="concept.spec-gap"></a>

When not sufficient, the assessment lists each **Spec gap** instead of a plan: a promise the goal
relies on that the Specs do not state, including where a new promise belongs when no bound Module's
Spec says so. Each names the Module and document where the promise belongs, what is missing, why the
goal needs it and a suggested repair. The usual next step is `specify` to close the gaps, then
another `understand` to confirm it.

`status` is `ok` whenever the worker completed an assessment, sufficient or not; `sufficient` says
whether work may proceed. It is `blocked` when the worker could not assess the goal at all — an
ambiguous goal, or Modules not bound — and the
[error chain](../../../glossary.json#concept.error-chain) ends in the worker's own link with
what it tried and would need. It is `failed` when the worker could not be run or changed a file,
with Workers' launch, timeout or audit error as the cause of the Operation's link, as for every
[standard worker sequence](../../../glossary.json#concept.standard-worker-sequence). It is also
`failed` when the assessment names an unknown Module or is internally inconsistent (gaps and
sufficiency, or plan and `--plan`, disagree; a bound Module has no entry or more than one; an entry
names a Module that is not bound): the Operation's own link then has the code `unknown_modules` or
`inconsistent_assessment`, lists every unknown Module or every inconsistency, and gives
`capability` as its reason — the Operation checks the assessment but never corrects it or
relaunches the worker. A failed or blocked result carries no `output`; the worker's own answer
stays in the `worker` field. Running the Operation again with the same inputs is safe.

## Design

The Operation is worker-backed, run with [task type](../../../glossary.json#concept.task-type)
`understand`, which gives the worker the bound Modules'
[Spec context](../../../glossary.json#concept.spec-context) and external material to read, only the
file names of their [implementation context](../../../glossary.json#concept.implementation-context),
and nothing to write. Reading names but not contents is the point: the only promises the worker can
report are ones the Spec states, so a thin Spec is a Spec gap, never inferred from code.

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `understand` [grant](../../../glossary.json#concept.grant) | Operation, Spec core | Specs cannot load, no Module named, or unknown Module (`failed`) |
| 2 | Generate settings, tools and the [brief](../../../glossary.json#concept.brief) | Workers | — |
| 3 | Launch the worker and wait for its [worker result](../../../glossary.json#concept.worker-result) | Workers, worker | launch error or timeout (`failed`) |
| 4 | [Audit](../../../glossary.json#concept.write-audit): read-only grant, so any change is a violation; write the [run record](../../../glossary.json#concept.run-record) | Workers | any change (`failed`) |
| 5 | Check every named Module exists in the Specs of the worktree the run works on and the assessment is consistent | Operation | unknown Module or inconsistency (`failed`) |
| 6 | Return the assessment as the run's output | Operation, Execution runner | — |

The worker gets only its [worker backend](../../../glossary.json#concept.worker-backend)'s reading
tools (Read, Glob and Grep on Claude Code; `read`, `grep`, `find` and `ls` on pi) — no editing,
shell or web tool and no MCP server. Pending files are not pre-created and checks are not run, since
nothing is writable or executed; a malformed assessment is not repaired either, so every accepted
assessment is one reading of one frozen grant.

The Operation treats the assessment as the worker's claim, verifying only what it can decide from
declarations and the assessment's own shape, then adds its own evidence, the **host evidence** of
the [run result](../../../glossary.json#concept.run-result): grant,
[context identity](../../../glossary.json#concept.context-identity), audit and transcript path, and
every unknown Module or inconsistency it finds. Whether a plan is good is for the caller and
later Operations to find out. See the [requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.understanding.operation"></a>

The **Understand Operation** realization holds the Operation's steps, worker instructions and result
schema in `src/concorde/understanding/` (`operation.py` declares the `UNDERSTAND` provider) with
prompt `prompts/workers/understand.md`, tested against a fake worker.

### Outside

<a id="uses-operations"></a>

**Operations** lists `understand` in its catalog as an Operation that may run unbound and writes
nothing, and names this Module as its provider; Understanding never calls another Operation.

<a id="uses-execution"></a>

**Execution**'s [runner](../../../glossary.json#concept.execution-runner) runs the Operation's
steps: it reads the [workspace binding](../../../glossary.json#concept.workspace-binding), settles
the Modules and inputs, and wraps the assessment in the
[run result](../../../glossary.json#concept.run-result). Understanding relies on it for the
workspace's goal and Modules, and for refusing an input that is not an `ok` run of the same
workspace, or, for an unbound run, of no workspace.

<a id="uses-workers"></a>

**Workers** turns the frozen grant into settings, launches the worker with this Module's brief,
collects its [worker result](../../../glossary.json#concept.worker-result), audits
the worktree and writes the run record. Any audit violation is a failed run. The brief Workers
appends tells the understand worker never to infer a promise the Spec does not state but to report
it as a Spec gap and end `ok`; this Module's instructions say the same, since for this worker a
missing promise is the finding itself: it reports the promise in an `ok`, insufficient assessment,
which infers nothing, and returns `blocked` only when it cannot assess the goal at all.

<a id="uses-spec"></a>

**Spec core** computes the `understand`
[grant](../../../glossary.json#concept.grant) and resolves Module identities for
step 5, always from the Specs of the worktree the run works on.
