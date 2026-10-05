# Framework requirements

These requirements hold for the Framework as a whole. Each [Module](glossary.json#concept.module)
states the precise behaviour it contributes. A requirement here promises what the Modules achieve
together.

## Parts

### req.concorde.part-dependencies — A part imports only the parts it depends on

Except for Distribution, every [part](glossary.json#concept.part) SHALL import code only from these
sources:

- Itself.
- The parts it depends on, as the table below gives them.

| Part | Depends on |
| --- | --- |
| spec | nothing |
| kernel | nothing |
| worker harness | kernel |
| execution | kernel |
| workflow | execution, kernel |
| issues | kernel |
| coordination | kernel |
| method | spec, worker harness, execution, workflow, kernel |
| distribution | nothing |

The root's [parts](module.md#the-parts) explains what each part holds. It also explains why the
directions are these. Distribution, the installation host, depends on no part. It is the one part that reaches
the others' code. It imports a part's code only through the entries and `loads` modules of that
part's [registration](glossary.json#concept.part-registration). Dogfooding's code is no part.
Distribution imports it only through the entry the package descriptor names under `develop.check`,
as its `uses` of Dogfooding declares.

There is no exception for an [optional integration](glossary.json#concept.optional-integration).
It imports no code of the part it uses, not even guarded against that part's absence. It reaches
that part only through that part's `concorde` command or a file format its Spec defines.
A Module's `uses` of a Module in a part its own part does not depend on is therefore one of two
things, and its explanation says which:

- It relies on a format or convention that part defines, which the relying part implements or
  meets itself. For example, the Spec tooling keeps its own copy of the Kernel's
  [typed values](glossary.json#concept.typed-value). Every part meets the host promises of
  Distribution, the installation host present in every installation.
- It is an optional integration. Its explanation says what the feature does with that part and
  without it.

No part imports Distribution. Distribution reaches the parts only
through their [registrations](glossary.json#concept.part-registration).

### req.concorde.part-installation — A part requires only the parts it depends on

Installing a part SHALL require the installation of only the parts it depends on, as [req.concorde.part-dependencies](#req.concorde.part-dependencies) gives them, besides Distribution.

Each part's registration names exactly those parts. When a selection lacks them, the installer
adds them transitively
([req.distribution.parts-installable](distribution/requirements.md#req.distribution.parts-installable)).
Distribution, the installation host, is installed beside every selection. It is no part's
dependency.

### req.concorde.part-alone — A part works with its dependencies alone

When installed with only its dependencies, every part SHALL do its work.

What a part cannot do without another part is an optional integration, never a failure of its own
work. With no other part installed, the spec part does the following:

- Checks Specs.
- Serves Specs.
- Publishes Specs.

With the kernel alone, the coordination part does the following:

- Opens tasks.
- Delivers tasks.
- Merges tasks.
- Closes tasks.

Distribution, the installation host, is installed beside every selection. It counts as no
dependency. It depends on no part. It reads only the registrations of the parts installed with it.

### req.concorde.absent-part-stated — An absent part is stated, not failed

An optional integration whose part is not installed SHALL be skipped with a statement that names the missing part, never making the rest of the work it belongs to fail.

When a part is not installed, its command or MCP tool is absent rather than present and broken.
A command that needs it is refused naming the part.

### req.concorde.one-version — All parts carry one version

Every part SHALL carry the version number of the [Concorde repository](glossary.json#concept.concorde-repository)
it was built from, the same for every part.

## Runtime

### req.concorde.main-agent-program — The main agent runs on Claude Code

The Framework SHALL support a [main agent](glossary.json#concept.main-agent) in Claude Code.

For now the main agent runs only on Claude Code. The
[task sessions](glossary.json#concept.task-session) it starts do too. Task sessions always run on
the main agent's own program. [Workers](glossary.json#concept.worker) need not do so. Their program
is the [worker configuration](glossary.json#concept.worker-configuration)'s choice, as
req.concorde.worker-program says. Therefore, the tasks of a Claude Code main agent may still run
pi workers.

### req.concorde.worker-program — Workers run on the configured program

Every worker SHALL run on the agent program the worktree's worker configuration chooses for it, and on pi when it chooses none, whatever program the main agent runs on.

When a worker's chosen program is not installed, the worker is refused, never moved to the other
program.

### req.concorde.grant-program-independent — A grant does not depend on the program

A worker's grant SHALL NOT depend on the agent program the worker runs on.

The [Spec](glossary.json#concept.spec) Protocol needs no change for this, because it defines
visibility. It does not define how an agent runs. Each backend compiles the same grant into its own mechanism.
Therefore, a Claude Code main agent may run pi workers as well as Claude Code workers.

### req.concorde.worker-models-per-worktree — Worker models belong to the worktree

The model and reasoning level of every worker SHALL come from the worker configuration of the checkout its run works in: the worktree of the run's workspace for a bound run, and the configuration committed in the unbound checkout for an unbound run.

### req.concorde.worker-models-tracked — The worker models are tracked with the project

The worker configuration SHALL be a file tracked by Git, so that:

- A task carries the configuration of its base commit.
- A change the task makes to the configuration merges with the task.

### req.concorde.worker-models-install-independent — The tracked configuration names no installation's model ids

The worker configuration SHALL name every model by a project model name that depends on no
installation, leaving each program's local model id to the user's untracked
[model map](glossary.json#concept.model-map).

### req.concorde.worker-models-explicit — Worker models change only on request

A worktree's worker configuration SHALL change only by an explicit request of the developer.

## The two halves

### req.concorde.halves-apart — The lower half knows no task

No [Operation](glossary.json#concept.operation), [execution command](glossary.json#concept.execution-command), workflow or worker SHALL read or write a [task record](glossary.json#concept.task-record), a
[decision log](glossary.json#concept.decision-log) or any other record Coordination keeps of a task.

The halves are those of the root's [Two halves, one seam](module.md#two-halves-one-seam).
The upper half is Coordination. The lower half comprises the parts that do the work in a
workspace:

- Execution.
- Workflows.
- Method.
- The worker harness.

The upper half hands a task to the lower half only by writing its worktree's
[workspace binding](glossary.json#concept.workspace-binding). The upper half learns the outcome
of the work done there only from the following:

- The [run store](glossary.json#concept.run-store).
- The [delivery commits](glossary.json#concept.delivery-commit).
- What Git shows of the task branch and its worktree.

The upper half, [Coordination](coordination/module.md), organizes the work. The lower half does
it. Keeping every piece of shared state on one side lets either half change without the other.

### req.concorde.operations-are-ai — An Operation involves a model

Every Operation SHALL launch at least one AI worker in each of its runs that is not refused before its first worker starts.

This classifies what an Operation is rather than forcing a launch. A run refused at admission
launches none. A run whose first worker is refused at launch also launches none. Deterministic work that a task
or a workflow runs is an execution command or a plain `concorde` command instead.

## Boundaries

A worker works under a grant. It never touches Git. Every grant Method computes comes from the
Specs of the checkout its run works in
([req.method.workspace-specs](method/requirements.md#req.method.workspace-specs)):

- For a bound run, the worktree of the run's
  [workspace](glossary.json#concept.workspace).
- For an [unbound run](glossary.json#concept.unbound-run), the
  [unbound checkout](glossary.json#concept.unbound-checkout).

No worker can read or change Git metadata
([req.workers.no-git](worker-harness/workers/launch.md#req.workers.no-git)). Git belongs to the
levels around the workers:

- The run that launches a worker reads the worktree's changes to audit them against the grant.
- The task level commits verified steps on the task branch.
- `delivery` makes the [delivery commit](glossary.json#concept.delivery-commit).
- The main agent merges.

### req.concorde.spec-first — Specs are derived from code only by code-to-spec

Every Spec statement that an Operation or an execution command writes from the contents of implementation files SHALL originate from a worker of [task type](glossary.json#concept.task-type) `code-to-spec`.

Concorde's flow is Spec first. When writing a Spec, every other worker sees code at most by name.
A project whose code came before its Specs is described through the
[Adoption](method/adoption/module.md) Operations. Their `code-to-spec` workers record behaviour
as it is. They return doubtful intent as [open questions](glossary.json#concept.open-question)
instead of promises. The one Adoption step without a worker, the execution command `scaffold`,
writes only what such a worker proposed.

### req.concorde.no-wider-than-type — A worker's grant never exceeds its task type

The [grant](glossary.json#concept.grant) Method computes for a worker SHALL NOT make readable or writable any of the project's files beyond what its task type assigns to its bound Modules.

This promise is Method's. Method computes every grant of Concorde's own workers. Used alone, the
worker harness enforces whatever grant its caller hands it. It audits that grant. It promises
nothing about where that grant came from ([Worker harness](worker-harness/module.md)).

The complete assignment is the level each task type gives every
[boundary set](glossary.json#concept.boundary-set). The task-type table of
[Spec core's grants](spec-tooling/spec/contracts.md#grants) gives this assignment. Spec core's
[boundary sets](spec-tooling/spec/contracts.md#boundary-sets) say which paths each set holds.

The promise bounds the computed grant. The [Harness](worker-harness/harness/module.md) then
enforces that grant on both backends. On Claude Code that enforcement has one gap. A file created
in the task worktree after generation of the worker's [deny rules](glossary.json#concept.deny-rules)
has no rule of its own. Unless a directory rule hides it, the file tools can therefore read it.
Unless the grant makes it writable, the [write hook](glossary.json#concept.write-hook) still
refuses to change it. Since the worker writes only writable paths, it cannot create such a file itself. The Harness's [known limits](worker-harness/harness/module.md#known-limits-of-v1) state
the gap.

Besides the project's files, the [Harness](worker-harness/harness/module.md) gives a worker
these directories of its run:

- Its own working directory.
- Its own home directory.
- Its own temporary directory.

The Harness leaves readable the system paths every program needs. Its
[known limits](worker-harness/harness/module.md#known-limits-of-v1) say what else it leaves out.

## Results and errors

Whatever the run's status, every [run result](glossary.json#concept.run-result) keeps the evidence
the run produced apart from the worker's own report. The runner and its steps never place a worker
result's statement in the result's summary or host evidence
([req.execution.claims-apart](execution/requirements.md#req.execution.claims-apart)). The worker's
link in the chain is marked with the level `worker`.

### req.concorde.detailed-errors — Errors are reported in detail

Every Operation, execution command, worker, step, `concorde` command other than Spec tooling's deterministic commands and Distribution's `build` and `protocol-manifest`, and the main agent SHALL report a failure to its parent as an error link that describes it completely: what failed, where, the exact message or output, the evidence and what was tried.

None of the following alone is ever the whole report:

- A status.
- A code.
- A one-line summary.

The parent must be able to reason about the error from the link without asking the actor that wrote it.

Spec tooling's deterministic commands and library, such as `concorde spec-validation`, are the
exception. They depend on no other Module. They report with Spec tooling's own, equally detailed
error record. Distribution's `build` and `protocol-manifest` print Spec core's shared envelope with that
record too ([req.distribution.one-envelope](distribution/requirements.md#req.distribution.one-envelope)).
When a Module cannot handle such a record, it translates the record into a link
([Where links appear](kernel/tracing/contracts.md#where-links-appear)).

### req.concorde.error-chain — An unhandled error keeps its chain

An actor that cannot handle an error it received from a child SHALL pass the child's error on
unchanged as a cause of its own link, which states the reason the actor cannot handle the error.

The reasons are the fixed set of the [error contract](kernel/tracing/contracts.md#contract.tracing.error).
The last receiver thereby reads one reason per level, from where the error started up to itself.
Independent errors, such as several failing checks, are sibling causes.

### req.concorde.structured-errors — The chain is structured data

Every error link SHALL conform to the error contract wherever it appears:

- In a [run result](glossary.json#concept.run-result).
- In a worker [run record](glossary.json#concept.run-record).
- In a refusal of a `concorde` command.
- In an escalation of the main agent or a [task session](glossary.json#concept.task-session).

A [worker result](glossary.json#concept.worker-result) carries the worker's link without the
following fields. Before the link reaches a run record, Workers adds these fields:

- `level`.
- `actor`.
- `causes`.

### req.concorde.spec-gaps-stop — Automatic rounds never fill a Spec gap

When a failure is a [Spec gap](glossary.json#concept.spec-gap) or a needed path outside the grant, an Operation SHALL stop and return its [error chain](glossary.json#concept.error-chain) instead of resuming a worker.

A [resume round](glossary.json#concept.resume-round) feeds back to the same worker only what a
program found:

- The failures of [configured checks](glossary.json#concept.configured-check) against code.
- Once they pass, what the step's own validation of the round reports to repair, such as the
  structural errors a Spec-writing worker introduced.

A promise the Spec does not state, or a path the grant does not give, is never supplied by another
round. It goes up to be decided.

## Change control

### req.concorde.delivery-separate — A task is delivered only by a delivery commit

A task SHALL count as delivered only through a [delivery commit](glossary.json#concept.delivery-commit) on its branch.

The task level may commit verified steps on the task branch as it works. Those commits deliver
nothing. `delivery` validates everything the branch holds since its base commit together with
what is not committed yet. Only when that whole workspace is ready does it commit the delivery
commit on top, as
[req.delivery.own-readiness](method/delivery/requirements.md#req.delivery.own-readiness) states.
Where the method part is not installed, after the checks it was given pass, `task deliver` commits
it. It judges nothing else.

### req.concorde.delivery-commit-by-delivery — Only a delivering command makes a delivery commit

No actor SHALL make a delivery commit except one of these delivering commands:

- Method's `delivery` execution command.
- Only where the method part is not installed, Coordination's `task deliver`.

A delivery commit is recognized by its subject alone
([Kernel](kernel/contracts.md#delivery-commit)). Therefore, none of the following commits under
that subject:

- A task session.
- The main agent.
- Any other command.

Delivery gives that subject to its delivery commits alone
([req.delivery.marked](method/delivery/requirements.md#req.delivery.marked)). Wherever the method
part is installed, `task deliver` refuses, so that a workspace Method could validate is never
delivered without that validation.

### req.concorde.merge-by-main-agent — The main agent merges delivered tasks

The main agent SHALL be able to merge a delivered task branch into the primary branch without asking the developer for authorization.
