# Understanding

## Purpose

Understanding lets the main agent learn what one or more Modules promise before anything changes.
It provides the `understand` Operation: a worker reads the bound Modules' Specs and only the names
of their code files, and answers a stated goal with what the Modules promise, whether their Spec
suffices, the Spec gaps if not, and, when asked, a plan. The main agent relies on it to plan work
and confirm a Spec repair closed a gap. Understanding never changes a file, never reads code
contents and never fills a missing promise by guessing from code; a plan is a proposal the main
agent may follow, change or reject.

## Terminology

| Term | Definition |
| --- | --- |
| Assessment | The result of one understand run: what the bound Modules promise, whether their Spec is sufficient for the stated goal, the Spec gaps found and, when requested and sufficient, a plan. |
| Spec gap | A promise that the stated goal needs and that the Spec of a bound Module does not state, reported with where it belongs instead of being inferred. |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Spec context](../../vocabulary.md#concept.concorde.spec-context) | |
| [Implementation context](../../vocabulary.md#concept.concorde.implementation-context) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Operation](../module.md#concept.operations.operation) | |
| [Operation host](../module.md#concept.operations.host) | |
| [Operation result](../module.md#concept.operations.result) | |
| [Grant](../../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Brief](../../agents/workers/module.md#concept.workers.brief) | |
| [Worker result](../../agents/workers/module.md#concept.workers.worker-result) | |
| [Write audit](../../agents/workers/module.md#concept.workers.audit) | |

An assessment is the answer; Spec gaps are the part of it that says why the goal cannot proceed
yet. The plan is optional and exists only inside a sufficient assessment.

## Usage

The main agent runs the Operation in a task worktree, usually before specifying or implementing:

```text
concorde run understand [--task <task-id>] --modules <module-id>[,<module-id>…] --goal "<text>" [--plan] [--input <run-id>]…
```

Without `--task` it runs [without a task](../module.md#concept.operations.no-task) on the primary
worktree, to answer a question before any task exists; it then
admits only inputs of other runs without a task. `--modules` names the worker's bound Modules
(default: the task's), `--goal` states what the main
agent wants to know or do, `--plan` also asks for a plan, and `--input` admits an earlier `ok`
run's output as task material. For example, `--modules module.issues --goal "let reports carry a
severity" --plan` has the worker answer with either a plan (`specify`, `implement`, `test`,
`code_review`) or the Spec gaps that block it.

<a id="concept.understanding.assessment"></a>

The Operation returns an [Operation result](../module.md#concept.operations.result) whose `output`
is an **assessment**, defined by the
[assessment contract](contracts.md#contract.understanding.assessment): for each bound Module, what
it promises that matters for the goal, and whether the Spec is **sufficient**. When it is and a
plan was requested, the plan names the Modules to change, the files to declare as pending entries
and where, the ordered next Operations, and the open decisions the main agent has to take. The
plan has no separate Operation: breaking work into steps is one use of understanding.

<a id="concept.understanding.spec-gap"></a>

When not sufficient, the assessment lists each **Spec gap** instead of a plan: the Module and
document where the promise belongs, what is missing, why the goal needs it and a suggested repair.
The usual next step is `specify` to close the gaps, then another `understand` to confirm it.

`status` is `ok` whenever the worker completed an assessment, sufficient or not; `sufficient` says
whether work may proceed. It is `blocked` when the worker could not assess the goal at all — an
ambiguous goal, or Modules not bound — and the
[error chain](../../vocabulary.md#concept.concorde.error-chain) ends in the worker's own link with
what it tried and would need. It is `failed` when the host could not run the worker, the worker
changed a file, or the assessment names an unknown Module or is internally inconsistent (gaps and
sufficiency, or plan and `--plan`, disagree; no entry for a bound Module): the Operation's own link
then has the code `unknown_modules` or `inconsistent_assessment`, lists every unknown Module or
every inconsistency, and gives `capability` as its reason — the host checks the assessment but
never corrects it or relaunches the worker. A failed or blocked result carries no `output`; the
worker's own answer stays in the `worker` field. Running the Operation again with the same inputs
is safe.

## Design

The Operation is worker-backed, run with task type `understand`, which gives the worker the bound
Modules' [Spec context](../../vocabulary.md#concept.concorde.spec-context) and external material to
read, only the file names of their
[implementation context](../../vocabulary.md#concept.concorde.implementation-context), and nothing
to write. Reading names but not contents is the point: the only promises the worker can report are
ones the Spec states, so a thin Spec is a Spec gap, never inferred from code.

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Compute and freeze the `understand` [grant](../../spec-tooling/spec/module.md#concept.spec.grant) | Workers, Spec core | Specs cannot load, or unknown Module (`failed`) |
| 2 | Generate settings, tools and the [brief](../../agents/workers/module.md#concept.workers.brief) | Workers | — |
| 3 | Launch the worker and wait for its [worker result](../../agents/workers/module.md#concept.workers.worker-result) | Workers, worker | launch error or timeout (`failed`) |
| 4 | [Audit](../../agents/workers/module.md#concept.workers.audit): read-only grant, so any change is a violation; write the run record | Workers | any change (`failed`) |
| 5 | Check every named Module exists and the assessment is consistent | host | unknown Module or inconsistency (`failed`) |
| 6 | Return the Operation result | host | — |

The worker gets only Read, Glob and Grep — no Edit, Write, Bash, web tools or MCP server. Pending
files are not pre-created and checks are not run, since nothing is writable or executed; a
malformed assessment is not repaired either, so every accepted assessment is one reading of one
frozen grant.

The host treats the assessment as the worker's claim, verifying only what it can decide from
declarations and the assessment's own shape, then adds its own evidence: grant, context identity,
audit and transcript path.
Whether a plan is good is for the main agent and later Operations to find out. See the
[requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.understanding.operation"></a>

The **Understand Operation** realization holds the host steps, worker instructions and result
schema in `src/concorde/understanding/` (`operation.py` declares the `UNDERSTAND` provider) with
prompt `prompts/workers/understand.md`, tested against a fake worker.

### Outside

<a id="uses-operations"></a>

**Operations** lists `understand` in its catalog, dispatches to this Module, and provides the host
runner and [Operation result](../module.md#concept.operations.result) envelope; Understanding never
calls another Operation.

<a id="uses-workers"></a>

**Workers** turns the frozen grant into settings, launches the worker with this Module's brief,
collects its [worker result](../../agents/workers/module.md#concept.workers.worker-result), audits
the worktree and writes the run record. Any audit violation is a failed run.

<a id="uses-spec"></a>

**Spec core** computes the `understand`
[grant](../../spec-tooling/spec/module.md#concept.spec.grant) and resolves Module identities for
step 5, always from the task worktree's own Specs.
