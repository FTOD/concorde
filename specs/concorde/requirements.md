# Framework requirements

These requirements hold for the Framework as a whole. Each [Module](glossary.json#concept.module)
states the precise behaviour it contributes; a requirement here promises what the Modules achieve
together.

## Parts

### req.concorde.part-dependencies — A part imports only the parts it depends on

Every [part](glossary.json#concept.part) other than Distribution SHALL import code only of itself and of the parts it depends on, as the table below gives them.

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

The root's [parts](module.md#the-parts) explains what each part holds and why the directions are
these. Distribution, the installation host, depends on no part and is the one part that reaches the
others' code: it imports a part's code only through the entries and `loads` modules of that part's
[registration](glossary.json#concept.part-registration), and Dogfooding's code, which is no part,
only through the entry the package descriptor names under `develop.check`, as its `uses` of
Dogfooding declares.

There is no exception for an [optional integration](glossary.json#concept.optional-integration): it
imports no code of the part it uses, not even guarded against that part's absence, and reaches it
only through that part's `concorde` command or a file format its Spec defines. A Module's `uses` of
a Module in a part its own part does not depend on is therefore one of two things, and its
explanation says which. Either it relies on a format or convention that part defines, which the
relying part implements or meets itself, as the Spec tooling keeps its own copy of the Kernel's
[typed values](glossary.json#concept.typed-value) and every part meets the host promises of
Distribution, the installation host present in every installation; or it is an optional
integration, whose explanation says what the feature does with that part and without it. No part
imports Distribution, which reaches the parts only through their
[registrations](glossary.json#concept.part-registration).

### req.concorde.part-installation — A part requires only the parts it depends on

Installing a part SHALL require the installation of only the parts it depends on, as [req.concorde.part-dependencies](#req.concorde.part-dependencies) gives them, besides Distribution.

Each part's registration names exactly those parts, and the installer adds them, transitively, to a
selection that lacks them
([req.distribution.parts-installable](distribution/requirements.md#req.distribution.parts-installable)).
Distribution, the installation host, is installed beside every selection and is no part's
dependency.

### req.concorde.part-alone — A part works with its dependencies alone

Every part SHALL do its work when it is installed with only the parts it depends on.

What it cannot do without another part is an optional integration, never a failure of its own
work: the spec part checks, serves and publishes Specs with no other part installed, and the
coordination part opens, delivers, merges and closes tasks with the kernel alone. Distribution, the
installation host, is installed beside every selection and counts as no dependency: it depends on
no part and reads only the registrations of the parts installed with it.

### req.concorde.absent-part-stated — An absent part is stated, not failed

An optional integration whose part is not installed SHALL be skipped with a statement that names the missing part, never making the rest of the work it belongs to fail.

A command or MCP tool of a part that is not installed is absent rather than present and broken; a
command that needs it is refused naming the part.

### req.concorde.one-version — All parts carry one version

Every part SHALL carry the version number of the [Concorde repository](glossary.json#concept.concorde-repository) it was built from, the same for every part.

## Runtime

### req.concorde.main-agent-program — The main agent runs on Claude Code

The Framework SHALL support a [main agent](glossary.json#concept.main-agent) in Claude Code.

For now the main agent runs only on Claude Code, and so do the
[task sessions](glossary.json#concept.task-session) it starts, which always run on the main agent's
own program. [Workers](glossary.json#concept.worker) need not: their program is the
[worker configuration](glossary.json#concept.worker-configuration)'s choice, as
req.concorde.worker-program says, so the tasks of a Claude Code main agent may still run pi workers.

### req.concorde.worker-program — Workers run on the configured program

Every worker SHALL run on the agent program the worktree's worker configuration chooses for it, and on pi when it chooses none, whatever program the main agent runs on.

A worker whose chosen program is not installed is refused, never moved to the other program.

### req.concorde.grant-program-independent — A grant does not depend on the program

A worker's grant SHALL NOT depend on the agent program the worker runs on.

The [Spec](glossary.json#concept.spec) Protocol needs no change for this, because it defines
visibility, not how an agent is run; each backend compiles the same grant into its own mechanism, so
a Claude Code main agent may run pi workers as well as Claude Code workers.

### req.concorde.worker-models-per-worktree — Worker models belong to the worktree

The model and reasoning level of every worker SHALL come from the worker configuration of the checkout its run works in: the worktree of the run's workspace for a bound run, and the configuration committed in the unbound checkout for an unbound run.

### req.concorde.worker-models-tracked — The worker models are tracked with the project

The worker configuration SHALL be a file tracked by Git, so that a task carries the configuration of its base commit and a change the task makes to it merges with the task.

### req.concorde.worker-models-install-independent — The tracked configuration names no installation's model ids

The worker configuration SHALL name every model by a project model name that depends on no installation, leaving each program's local model id to the user's untracked [model map](glossary.json#concept.model-map).

### req.concorde.worker-models-explicit — Worker models change only on request

A worktree's worker configuration SHALL change only by an explicit request of the developer.

## The two halves

### req.concorde.halves-apart — The lower half knows no task

No [Operation](glossary.json#concept.operation), [execution command](glossary.json#concept.execution-command), workflow or worker SHALL read or write a [task record](glossary.json#concept.task-record), a [decision log](glossary.json#concept.decision-log) or any other record Coordination keeps of a task.

The halves are those of the root's [Two halves, one seam](module.md#two-halves-one-seam): the upper
half is Coordination, and the lower half the parts that do the work in a workspace, Execution,
Workflows, Method and the worker harness. The upper half hands a task to the lower half only by
writing its worktree's
[workspace binding](glossary.json#concept.workspace-binding), and learns the outcome of the work
done there only from the [run store](glossary.json#concept.run-store) and the
[delivery commits](glossary.json#concept.delivery-commit), beside what Git shows of the task branch
and its worktree.

The upper half, [Coordination](coordination/module.md), organizes the work; the lower half does
it. Keeping every piece of shared state on one side lets either half change without the other.

### req.concorde.operations-are-ai — An Operation involves a model

Every Operation SHALL launch at least one AI worker in each of its runs that is not refused before its first worker starts.

This classifies what an Operation is rather than forcing a launch: a run refused at admission, or
whose first worker is refused at launch, launches none. Deterministic work that a task or a workflow
runs is an execution command or a plain `concorde` command instead.

## Boundaries

### req.concorde.spec-first — Specs are derived from code only by code-to-spec

Every Spec statement that an Operation or an execution command writes from the contents of implementation files SHALL originate from a worker of [task type](glossary.json#concept.task-type) `code-to-spec`.

Concorde's flow is Spec first, and every other worker sees code at most by name when it writes a
Spec. A project whose code came before its Specs is described through the
[Adoption](method/adoption/module.md) Operations: their `code-to-spec` workers record
behaviour as it is and return doubtful intent as
[open questions](glossary.json#concept.open-question) instead of promises, and the one Adoption step
without a worker, the execution command `scaffold`, writes only what such a worker proposed.

### req.concorde.grant-from-task-worktree — Grants come from the Specs the worker works on

Every grant Method computes for a worker it launches SHALL be computed from the Specs of the checkout its run works in: the worktree of the run's [workspace](glossary.json#concept.workspace) for a bound run, and the [unbound checkout](glossary.json#concept.unbound-checkout) for an [unbound run](glossary.json#concept.unbound-run).

### req.concorde.no-wider-than-type — A worker's grant never exceeds its task type

The [grant](glossary.json#concept.grant) Method computes for a worker SHALL NOT make readable or writable any of the project's files beyond what its task type assigns to its bound Modules.

These two promises are Method's, which computes every grant of Concorde's own workers. The worker
harness, used alone, enforces and audits whatever grant its caller hands it and promises nothing
about where that grant came from ([Worker harness](worker-harness/module.md)).

The complete assignment, the level each task type gives every
[boundary set](glossary.json#concept.boundary-set), is the task-type table of
[Spec core's grants](spec-tooling/spec/contracts.md#grants), and Spec core's
[boundary sets](spec-tooling/spec/contracts.md#boundary-sets) say which paths each set holds.

The promise bounds the computed grant, which the [Harness](worker-harness/harness/module.md) then enforces on
both backends. On Claude Code that enforcement has one gap: a file created in the task worktree
after the worker's [deny rules](glossary.json#concept.deny-rules) were generated has no rule of its
own, so the file tools can read it unless a directory rule hides it, although the
[write hook](glossary.json#concept.write-hook) still refuses to change it unless the grant makes it
writable. The worker cannot create such a file itself, since it writes only writable paths; the
Harness's [known limits](worker-harness/harness/module.md#known-limits-of-v1) state the gap.

Besides the project's files, the [Harness](worker-harness/harness/module.md) gives a worker its run's own working,
home and temporary directories and leaves readable the system paths every program needs; its
[known limits](worker-harness/harness/module.md#known-limits-of-v1) say what else it leaves out.

### req.concorde.workers-no-git — Workers have no Git access

A worker SHALL NOT be able to read or change Git metadata.

Git belongs to the levels around the workers: the run that launches a worker reads the worktree's
changes to audit them against the grant, the task level commits verified steps on the task branch,
`delivery` makes the [delivery commit](glossary.json#concept.delivery-commit), and the main agent
merges.

## Results and errors

### req.concorde.detailed-errors — Errors are reported in detail

Every Operation, execution command, worker, step, `concorde` command other than Spec tooling's deterministic commands and Distribution's `build` and `protocol-manifest`, and the main agent SHALL report a failure to its parent as an error link that describes it completely: what failed, where, the exact message or output, the evidence and what was tried.

A status, a code or a one-line summary alone is never the whole report. The parent must be able to reason about the error from the link without asking the actor that wrote it.

Spec tooling's deterministic commands and library, such as `concorde spec-validation`, are the
exception: they depend on no other Module and report with Spec tooling's own, equally detailed error
record. Distribution's `build` and `protocol-manifest` print Spec core's shared envelope with that
record too ([req.distribution.one-envelope](distribution/requirements.md#req.distribution.one-envelope)).
A Module that cannot handle such a record translates it into a link
([Where links appear](kernel/tracing/contracts.md#where-links-appear)).

### req.concorde.error-chain — An unhandled error keeps its chain

An actor that cannot handle an error it received from a child SHALL pass the child's error on unchanged as a cause of its own link, which states the reason the actor cannot handle the error.

The reasons are the fixed set of the [error contract](kernel/tracing/contracts.md#contract.tracing.error). The last receiver thereby reads one reason per level, from where the error started up to itself. Independent errors, such as several failing checks, are sibling causes.

### req.concorde.structured-errors — The chain is structured data

Every error link SHALL conform to the error contract wherever it appears: in a [run result](glossary.json#concept.run-result), a worker [run record](glossary.json#concept.run-record), a refusal of a `concorde` command and an escalation of the main agent or a [task session](glossary.json#concept.task-session).

A [worker result](glossary.json#concept.worker-result) carries the worker's link without `level`,
`actor` and `causes`, which Workers adds before the link reaches a run record.

### req.concorde.claims-apart — Host evidence and worker claims stay apart

Every run result SHALL keep the evidence the run produced apart from the worker's own report.

This holds whatever the run's status, as Execution's
[req.execution.claims-apart](execution/requirements.md#req.execution.claims-apart) states for the
runner and its steps. The worker's link in the chain is marked with the level `worker`; the run
never moves a worker's statement into its own links or its host evidence.

### req.concorde.spec-gaps-stop — Automatic rounds never fill a Spec gap

An Operation SHALL stop and return its [error chain](glossary.json#concept.error-chain) instead of resuming a worker when the failure is a [Spec gap](glossary.json#concept.spec-gap) or a needed path outside the grant.

A [resume round](glossary.json#concept.resume-round) feeds back to the same worker only what a
program found: the failures of [configured checks](glossary.json#concept.configured-check) against
code and, once they pass, what the step's own validation of the round reports to repair, such as
the structural errors a Spec-writing worker introduced. A promise the Spec does not state, or a
path the grant does not give, is never supplied by another round; it goes up to be decided.

## Change control

### req.concorde.delivery-separate — A task is delivered only by a delivery commit

A task SHALL count as delivered only through a [delivery commit](glossary.json#concept.delivery-commit) on its branch.

The task level may commit verified steps on the task branch as it works; those commits deliver
nothing. `delivery` validates everything the branch holds since its base commit together with what
is not committed yet, and commits the delivery commit on top only when that whole workspace is
ready, as [req.delivery.own-readiness](method/delivery/requirements.md#req.delivery.own-readiness)
states. Where the method part is not installed, `task deliver` commits it after the checks it was
given pass, and judges nothing else.

### req.concorde.delivery-commit-by-delivery — Only a delivering command makes a delivery commit

No actor other than a delivering command SHALL make a delivery commit: Method's `delivery` execution command, or, only where the method part is not installed, Coordination's `task deliver`.

A delivery commit is recognized by its subject alone
([Kernel](kernel/contracts.md#delivery-commit)), so no task session, main agent or other command
commits under that subject; Delivery gives it to its delivery commits alone
([req.delivery.marked](method/delivery/requirements.md#req.delivery.marked)), and `task deliver`
refuses wherever the method part is installed, so that a workspace Method could validate is never
delivered without that validation.

### req.concorde.merge-by-main-agent — The main agent merges delivered tasks

The main agent SHALL be able to merge a delivered task branch into the primary branch without asking the developer for authorization.
