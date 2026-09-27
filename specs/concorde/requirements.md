# Framework requirements

These requirements hold for the Framework as a whole. Each [Module](glossary.json#concept.module)
states the precise behaviour it contributes; a requirement here promises what the Modules achieve
together.

## Runtime

### req.concorde.agent-runtimes — Claude Code and pi are the agent runtimes

The Framework SHALL support a [main agent](glossary.json#concept.main-agent) in Claude Code or in pi and run every worker of that main agent, under the same grant, on the agent program the worktree's [worker model configuration](glossary.json#concept.worker-model-configuration) chooses for it, and on the main agent's own program when it chooses none.

The [Spec](glossary.json#concept.spec) Protocol needs no change for this, because it defines
visibility, not how an agent is run; each backend compiles the same grant into its own mechanism, so
a Claude Code main agent may run pi workers and a pi main agent Claude Code workers. A worker whose
chosen program is not installed is refused, never moved to the other program.

### req.concorde.worker-models-per-worktree — Worker models belong to the worktree

The model and reasoning level of every worker SHALL come from the worker model configuration of the worktree it works on, which a new task worktree inherits from the primary worktree when the task opens and which changes afterwards only by an explicit request made in that worktree.

## The two halves

### req.concorde.halves-apart — The execution core knows no task

No [Operation](glossary.json#concept.operation), [execution command](glossary.json#concept.execution-command), workflow or worker SHALL read or write a [task record](glossary.json#concept.task-record), a [decision log](glossary.json#concept.decision-log) or any other state of the task store.

The upper half hands a task to the execution core only by writing its worktree's
[workspace binding](glossary.json#concept.workspace-binding), and learns what happened there only
from the [run store](glossary.json#concept.run-store) and the
[delivery commits](glossary.json#concept.delivery-commit).

The upper half, [Coordination](coordination/module.md), organizes the work; the lower half,
[Execution](execution/module.md), does it. Keeping every piece of shared state on one side lets
either half change without the other.

### req.concorde.operations-are-ai — An Operation involves a model

Every Operation SHALL launch at least one AI worker.

Deterministic work that a task or a workflow runs is an execution command or a plain `concorde`
command instead.

## Boundaries

### req.concorde.spec-first — Specs are derived from code only by code-to-spec

Every Spec statement that an Operation writes from the contents of implementation files SHALL originate from a worker of [task type](glossary.json#concept.task-type) `code-to-spec`.

Concorde's flow is Spec first, and every other worker sees code at most by name when it writes a
Spec. A project whose code came before its Specs is described through the
[Adoption](execution/operations/adoption/module.md) Operations: their `code-to-spec` workers record
behaviour as it is and return doubtful intent as
[open questions](glossary.json#concept.open-question) instead of promises, and the one Adoption step
without a worker, the execution command `scaffold`, writes only what such a worker proposed.

### req.concorde.grant-from-task-worktree — Grants come from the workspace's own Specs

Every grant a worker receives SHALL be computed from the Specs in the worktree of the workspace it works on.

### req.concorde.no-wider-than-type — A worker never exceeds its task type

A worker's readable and writable paths SHALL NOT exceed what its task type assigns to its bound Modules.

### req.concorde.workers-no-git — Workers have no Git access

A worker SHALL NOT be able to read or change Git metadata; diffs and delivery commits belong to the runs that launch no worker, and merges to the main agent.

## Results and errors

### req.concorde.detailed-errors — Errors are reported in detail

Every Operation, execution command, worker, step, `concorde` command and the main agent SHALL report a failure to its parent as an error link that describes it completely: what failed, where, the exact message or output, the evidence and what was tried.

A status, a code or a one-line summary alone is never the whole report. The parent must be able to reason about the error from the link without asking the actor that wrote it.

### req.concorde.error-chain — An unhandled error keeps its chain

An actor that cannot handle an error it received from a child SHALL pass the child's error on unchanged as a cause of its own link, which states the reason the actor cannot handle the error.

The reasons are the fixed set of the [error contract](contracts.md#contract.concorde.error). The last receiver thereby reads one reason per level, from where the error started up to itself. Independent errors, such as several failing checks, are sibling causes.

### req.concorde.structured-errors — The chain is structured data

Every error link SHALL conform to the error contract wherever it appears: in a [run result](glossary.json#concept.run-result), a worker [run record](glossary.json#concept.run-record), a [worker result](glossary.json#concept.worker-result), a refusal of a `concorde` command and an escalation of the main agent.

### req.concorde.claims-apart — Host evidence and worker claims stay apart

Every run result that is not successful SHALL keep the evidence the run produced apart from the worker's own report.

The worker's link in the chain is marked with the level `worker`; the run never moves a worker's statement into its own links or its host evidence.

### req.concorde.spec-gaps-stop — Automatic rounds never repair Specs

An Operation SHALL stop and return its [error chain](glossary.json#concept.error-chain) instead of resuming a worker when the failure is a [Spec gap](glossary.json#concept.spec-gap), a needed path outside the grant, or a failed structural Spec check.

Only failures of [configured checks](glossary.json#concept.configured-check) against code are fed
back to the same worker automatically.

## Change control

### req.concorde.delivery-separate — Delivery is its own Operation

Changes of a task SHALL reach the task branch only through the `delivery` Operation, which commits them together with their evidence.

### req.concorde.merge-by-main-agent — The main agent merges delivered tasks

The main agent SHALL be able to merge a delivered task branch into the primary branch without asking the developer for authorization.
