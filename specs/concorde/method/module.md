# Method

## Purpose

Method is the method [part](../glossary.json#concept.part): Concorde's own Spec-driven way of
changing a project, built from the other parts. It provides:

- The [Operations](../glossary.json#concept.operation) in which AI workers understand, specify,
  implement, test and review a project.
- The Adoption route that describes code which came before its Specs.
- The [execution commands](../glossary.json#concept.execution-command) that decide readiness,
  deliver and scaffold.
- The [brownfield workflow](../glossary.json#concept.brownfield-workflow).
- The [standard worker sequence](../glossary.json#concept.standard-worker-sequence) by which every
  one of its workers is bounded by the Specs.

Method is where the other parts meet:

- The [Spec tooling](../spec-tooling/module.md) computes a grant but launches nothing.
- The worker harness launches a worker under a grant it is given but reads no
  [Spec](../glossary.json#concept.spec).
- Execution runs a definition's steps but knows no particular Operation.
- Workflows orders runs but knows no particular procedure.

Method's definitions and steps connect them:

- They take the grant from the Spec tooling.
- They hand it to the worker harness with a
  [round validation](../worker-harness/workers/launch.md#round-validation).
- They register their Operations and commands with Execution.
- They fill the output convention Workflows reads.
- They contribute the brownfield workflow's script.

A project that installs Method therefore installs these parts with it:

- The spec part.
- The worker harness part.
- The execution part.
- The workflow part.
- The kernel part.

The issues part stays optional.

Method never does any of these on its own initiative:

- Chooses the next run.
- Asks the developer anything.
- Changes a Spec.

The task level of the [levels of work](../module.md#the-levels-of-work), directly or through a
workflow, orders its runs. When the Spec does not state a promise, that promise stops the run as a
[Spec gap](../glossary.json#concept.spec-gap).

## Core concepts

### The Operations and commands it provides

Every Operation is listed with:

- Its provider.
- The [task type](../glossary.json#concept.task-type) of its workers.
- Their [worker ids](../glossary.json#concept.worker-id).
- Whether it may run [unbound](../glossary.json#concept.unbound-run).
- What it may change.
- Its output.

Method registers these definitions with Execution, whose
[Operation catalog](../glossary.json#concept.operation-catalog) then lists them:

| Operation | Provider | Task type | Worker ids | Unbound | May change | Output |
| --- | --- | --- | --- | --- | --- | --- |
| `understand` | [Understanding](understanding/module.md) | `understand` | `worker` | yes | no | [an assessment](understanding/contracts.md#contract.understanding.assessment), with a plan when asked |
| `plan_review` | [Understanding](understanding/module.md) | `review-code` | `reviewer` | no | no | a [plan review report](understanding/contracts.md#contract.understanding.plan-review) with findings and a verdict |
| `specify` | [Specification](specification/module.md) | `specify` | `worker` | no | Specs of the bound Modules, including documents it creates, and the registry mirror | a [Spec change](../glossary.json#concept.spec-change) ([contract](specification/contracts.md#contract.specification.spec-change)) |
| `implement` | [Implementation](implementation/module.md) | `implement` | `worker` | no | code of the bound Modules | [a code change](implementation/contracts.md#contract.implementation.code-change) |
| `test` | [Implementation](implementation/module.md) | `test` | `worker` | no | no | a test report ([contract](implementation/contracts.md#contract.implementation.test-report)) |
| `spec_review` | [Spec review](spec-review/module.md) | `review-spec` | `reviewer`, `checker` | yes | no | [review findings](../glossary.json#concept.review-finding) and a verdict ([contract](spec-review/operation.md#contract.spec-review.payload)) |
| `spec_panel` | [Spec review](spec-review/module.md) | `review-spec`; `review-architecture` for its architects, and for its chair when it has an architect | `reviewer1` … `reviewer5`, `architect1`, `architect2`, `chair` | yes | no | a panel report merged from independent reviews, and a verdict ([contract](spec-review/panel.md#contract.spec-review.panel-payload)) |
| `code_review` | [Code review](code-review/module.md) | `review-code` | `worker` | yes (`--base` for a change review) | no | a code review report of a change or of whole Modules, and a verdict ([contract](code-review/contracts.md#contract.code-review.review)) |
| `survey` | [Adoption](adoption/module.md) | `code-to-spec`, writes withheld | `worker` | yes | no | a [decomposition proposal](adoption/contracts.md#contract.adoption.decomposition) |
| `code_to_spec` | [Adoption](adoption/module.md) | `code-to-spec` | `worker` | no | Specs of the bound Modules, the registry mirror and the `verifies` links of the existing tests it describes | a [Spec description](adoption/contracts.md#contract.adoption.spec-description) |

"May change" covers both what a worker's grant makes writable and what the provider's own host
steps change in the workspace. Each provider's Spec gives the rule. Method registers three
execution commands besides:

- [Validation](validation/module.md)'s `task-validation`, which decides whether the bound workspace
  is ready to deliver.
- [Delivery](delivery/module.md)'s `delivery`, the only run that commits. It decides the readiness
  again and makes the workspace's [delivery commit](../glossary.json#concept.delivery-commit).
- [Scaffold](scaffold/module.md)'s `scaffold`, which creates the child Modules a survey proposed.

Where the issues part is installed, the findings of `spec_review`, `spec_panel` and `code_review`
become [Issues](../glossary.json#concept.issue) of the project. Elsewhere each finding stays in the
run result. The verdict is derived from the findings' tiers the same way. `plan_review`'s findings
judge a plan within one run. They always stay in its report
([requirements](requirements.md#optional-integrations)).

### The standard worker sequence

<a id="concept.standard-worker-sequence"></a>

Each Operation's control flow is a step table in its provider's Spec. The runner runs it in order
until one step stops the run. **Admission** comes first, once per run. Before any of its provider's
own steps, every Operation checks:

- All the workers it may launch against the
  [worker configuration](../glossary.json#concept.worker-configuration) and the
  [model map](../glossary.json#concept.model-map).
- The configuration's Operation names and worker ids against every Operation the installed parts
  register.

This way, a run never stops at a later worker, after earlier ones ran, for a configuration or
model-map problem that admission could have found first
([what admission checks](workers.md#admitting-the-workers)). Then each worker-backed step follows
the **[standard worker sequence](../glossary.json#concept.standard-worker-sequence)** for the one
worker it launches:

1. **Bound.** The step computes the [grant](../glossary.json#concept.grant) for the task type and
   Modules from the **workspace's** Specs through [Spec core](../spec-tooling/spec/module.md).
   When its provider withholds writes, the step lowers every writable level to read. It freezes
   the result with the computed grant's [context identity](../glossary.json#concept.context-identity).
   It converts the result into the worker harness's input format.
2. **Instruct.** It composes the task instructions from:
   - The provider's prompt.
   - The definitions of the glossary terms the bound Modules use.
   - The rules about Spec gaps and paths outside the grant.
3. **Launch.** It hands these to the worker harness:
   - The grant.
   - The instructions.
   - The worker's identity.
   - The **round validation**.

   The worker harness then:
   - Prepares the settings and the [brief](../glossary.json#concept.brief).
   - Launches the worker.
   - Runs the [write audit](../glossary.json#concept.write-audit).
   - Calls the round validation after each clean round.
   - While rounds remain, resumes the worker with what the round validation reports to repair.
   - Writes the [run record](../glossary.json#concept.run-record).
4. **Decide.** It keeps the [worker result](../glossary.json#concept.worker-result) unchanged.
   It decides what the outcome means for the run.

The round validation is Method's. It checks in this order:

1. First, it checks glossary ownership. When the worker changed a glossary entry that a
   [Module](../glossary.json#concept.module) outside its grant owns, this check ends the run at once.
2. Then, when the step asks for them, it runs the
   [configured checks](../glossary.json#concept.configured-check) through Check execution, outside
   the worker. These checks cover the bound Modules and every Module that uses one of them.
3. Then, when every check passed or none ran and the step has its own validation, it runs that
   validation. One example is the structural validation a Spec-writing step runs instead of
   configured checks.

It returns the [check results](../glossary.json#concept.check-result) as the round's evidence. It
returns what failed as what to repair. Glossary ownership is checked once more after the worker
run, whatever the worker's status, so that no round and no deletion escapes it. A
[Spec gap](../glossary.json#concept.spec-gap) or a path outside the grant is never something to
repair. [How an Operation runs its
workers](workers.md#the-round-validation) gives the sequence exactly.

### The brownfield workflow

<a id="concept.brownfield-workflow"></a>

The **[brownfield workflow](../glossary.json#concept.brownfield-workflow)** describes a project
whose code came before its Specs, one Module and its new children at a time. It runs:

- A survey.
- The scaffold of the Modules it proposed.
- A `code_to_spec` run per Module.
- A Spec review.
- Task validation.
- Delivery.

Its arguments add `module`, the Module to describe, usually the root. A workspace's
[step keys](../glossary.json#concept.step-key), `validate` and `delivery` included, belong to one
procedure. For that reason, splitting a created child further is a new workspace running the
workflow on that child. Method contributes its [workflow script](../glossary.json#concept.workflow-script).
The script names `delivery` as its last step. It reads the scaffold's created Modules from the data
that run hands it. Its Operations declare its decision points in the
[step output convention](../workflows/contracts.md):

- Every decision the survey took itself.
- Every [open question](../glossary.json#concept.open-question).

[The brownfield workflow](brownfield.md) walks through it.

## Overview

### How Method connects the parts

```d2 illustrative
direction: right
spec: "Spec tooling\n(Spec core)"
harness: Worker harness
execution: Execution {
  runner: Runner
  checks: Check execution
}
workflows: Workflows
issues: "Issues\n(optional)"
method: Method {
  definitions: "Operation and command\ndefinitions"
  sequence: "Standard worker\nsequence"
  validation: "Round validation"
  script: "Brownfield\nworkflow script"
}
execution.runner -> method.definitions: "runs the steps of"
method.sequence -> spec: "computes the grant through"
method.sequence -> harness: "launches the worker through,\nwith the grant as data"
harness -> method.validation: "calls after each round"
method.validation -> execution.checks: "runs configured checks through"
method.script -> workflows: "is run by"
method.definitions -> issues: "reviews report findings to,\nwhere installed"
```

### A worker-backed step

```d2 illustrative
direction: down
admit: "Run admission, before any provider step:\nevery worker against configuration and model map"
grant: "Compute the grant from the workspace's\nSpecs and freeze it with its context identity"
instruct: "Compose the task instructions"
wh: Worker harness {
  prepare: "Settings, tool set and brief"
  launch: "Launch or resume the worker"
  audit: "Write audit against the grant"
  record: "Write the run record"
  prepare -> launch -> audit
}
validation: "Round validation (Method):\nglossary ownership, configured checks,\nthe step's own validation"
decide: "Decide what the outcome\nmeans for the run"
admit -> grant -> instruct -> wh.prepare
wh.audit -> validation: "worker ended ok, audit clean"
validation -> wh.launch: "something to repair,\nrounds left: resume round" {style.stroke-dash: 3}
validation -> wh.record: "nothing to repair, or rounds used up"
wh.audit -> wh.record: "worker blocked or failed, invalid result,\ntimeout or audit violation" {style.stroke-dash: 3}
ownership: "Glossary ownership,\nafter the worker run"
wh.record -> ownership -> decide
```

### Claims and evidence

A worker-backed run's result carries the worker's own
[worker result](../glossary.json#concept.worker-result) unchanged, beside the evidence the run's
steps produced. That evidence includes:

- The grant.
- The context identity.
- The write audit.
- Each check's exit code and log.
- The [resume rounds](../glossary.json#concept.resume-round) used.
- The transcript path.
- The worker stderr.

The caller therefore reads the claim as a claim and the evidence as fact. This is how Method's
steps meet Execution's [requirement](../execution/requirements.md#req.execution.claims-apart) that
worker claims stay the worker's. That requirement binds the runner and every step. Take an
`implement` worker that claims the goal is done while one check still fails after the last resume
round. Its run ends `failed`, with its claim kept unchanged and its chain naming the Operation,
Workers' rounds and the check's log.

## How it is built

### Why the method is a part of its own

The concrete way Concorde changes a project changes far more often than the mechanisms it uses.
That way includes:

- Which Operations exist.
- What each worker is told.
- How readiness is decided.
- What a delivery requires.

A project may want those mechanisms without this method:

- The worker harness under another orchestrator.
- Execution for its own definitions.
- Task management with its own delivery.

The method stays in one part that depends on the others, with nothing depending on it. This lets
each mechanism be installed and changed without it. The method composes them exactly as Concorde
works.

The grant always comes from the workspace's Specs, never the primary worktree's. A task that
changes a Spec is therefore bounded by the Spec as its workspace sees it. An unbound run reads its
[unbound checkout](../glossary.json#concept.unbound-checkout) of the worktree it started in. Only a
bound workspace may change, so an unbound run may launch only reading workers. Because two runs in
one worktree would audit each other's writes as their own, one workspace runs one run at a time.
Parallelism therefore comes from running workspaces side by side. No provider calls another
Operation. The task level or its workflow decides which runs next.

### Code

The providers' and commands' code lives with their Modules.

<a id="realization.method.workers"></a>

The **Standard sequence** realization, `src/concorde/method/workers.py`, holds the
[standard worker sequence](../glossary.json#concept.standard-worker-sequence). It holds:

- The admission step `check_worker_models`.
- The helper that puts it first in every Operation definition Method registers.
- The admission of its Modules.
- The runtime-path resolver of an Operation that may run unbound.
- The projection of Spec core's grant into the worker harness's grant input.
- The composition of the task instructions.
- The round validation.
- The glossary check after the worker run.
- The mapping of a worker run record to a step outcome.

<a id="realization.method.brownfield"></a>

The **Brownfield procedure** realization, `src/concorde/method/brownfield/`, holds the
[brownfield workflow](../glossary.json#concept.brownfield-workflow)'s script, `brownfield.js`. It
also holds the module that registers the workflow, with its last step `delivery`, with Workflows'
catalog when its code loads ([The brownfield workflow](brownfield.md)).

<a id="realization.method.definitions"></a>

The **Definitions** realization holds what Method's definitions share around their steps:

- When it loads, `registration.py` registers every Operation and execution command Method provides
  with Execution's catalogs.
- `specs.py` holds the admission of a run's Modules against the workspace's registry. With
  `removed-module` evidence, it leaves out the binding's Modules the workspace no longer registers.
  As [Execution's runner](../execution/runner.md#runner) lets a definition's admission do, it refuses
  `modules_removed`, `specs_unloadable` and `unknown_module`. For a command that diagnoses the Specs
  itself, it begins anyway. It also holds the translation of Spec tooling's errors into links of
  the [error chain](../glossary.json#concept.error-chain).
- `checks.py` selects these for [Check execution](#uses-checks):
  - The Modules a change concerns and every Module that uses one of them.
  - The implementation files each one's results depend on.
  - The tests whose [verification declarations](../glossary.json#concept.verification-declaration)
    name a scenario of theirs.
  - The project's interpreter.

  It runs their checks.
- `prompts.py` holds the prompt and brief helpers of the worker-backed providers.

<a id="realization.method.review-issues"></a>

**Review Issues**, `src/concorde/method/review_issues.py`, is the review providers' shared handling
of their Issues. Through the issues command, as [Issues](#uses-issues) says, it handles:

- Reading a reviewed Module's earlier Issues.
- Settling which a review carries or resolves.
- Reporting its findings.

Where the issues part is not installed, it states in the result that the findings were not recorded.

<a id="realization.method.guidance"></a>

The **Method guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance), kept in `prompts/guidance/method/`.
The sections are registered under `guidance` in the part's registration. Wherever the part is
installed, [Distribution](../distribution/module.md#guidance-composition) composes them after
Coordination's working method. They are:

- The project skill's "Operations", with the brownfield workflow.
- The [task-session](../glossary.json#concept.task-session) prompt's "Method's Operations", with:
  - Preparing the workers' environment.
  - `plan_review`.
  - Delivering with `task-validation` and `delivery`.
  - The reviews.
- The `CLAUDE.md` block's sentence on `brownfield`.

Each section says what happens where a part it mentions is not installed.

### The children

<a id="contains-understanding"></a>

**Understanding** provides `understand` and `plan_review`. In `understand` a worker reads the bound
Modules' Specs and file names. It returns an assessment, changing nothing. Its output is advice to
the task level, never an instruction to the runner. It may run unbound, which is how the
[main agent](../glossary.json#concept.main-agent) answers a question before any change is agreed.
In the optional `plan_review` a reviewer reads the Specs and the code. It judges a plan the task
level wrote, changing nothing. Until the verdict is `accepted`, the task level answers its findings
in the next run, with the previous run as `--input`. It needs a bound workspace, whose goal the plan
is judged against.

<a id="contains-specification"></a>

**Specification** provides `specify`: a worker edits the bound Modules' own Spec documents.
The Operation validates the result. It is the Operation that changes what a Module promises.
`code_to_spec` writes Specs only to describe existing code. `implement` changes no Spec.
The task level therefore routes every Spec repair through `specify` or does it itself.

<a id="contains-implementation"></a>

**Implementation** provides `implement` and `test`. In `implement` a worker changes the bound
Modules' code under a grant that makes only that code writable. Its round validation runs their
checks with resume rounds until they pass or the rounds run out. Its result therefore says whether
the checks passed on the changed code. In `test` a read-only worker interprets the checks the
Operation ran. It returns a test report. The check results, not the worker's reading of them, are
the evidence. Both need a bound workspace.

<a id="contains-code-review"></a>

**Code review** provides `code_review`. A worker judges code against the Specs and returns
findings, changing nothing. It judges one of these:

- A workspace's change since the binding's base commit.
- When it runs unbound, a change since `--base`.
- With `--scope module`, each named Module's whole code, one worker per Module.

The Operation:

- Keeps the findings as the workers' claims.
- Checks their evidence.
- Where the issues part is installed, reports each as an Issue.
- Derives the verdict from the findings' tiers.

Acting on a finding is the task level's decision.

<a id="contains-spec-review"></a>

**Spec review** provides `spec_review` and `spec_panel`: reviewers read the bound Modules' Specs and
return findings, changing nothing. The findings stay the workers' claims. The provider derives
the verdict from them. Where the issues part is installed, the provider reports each as an
[Issue](../glossary.json#concept.issue), in bound and unbound runs alike. The primary worktree keeps
those Issues, so the workspace does not change. `spec_panel` is the one provider whose steps run a
LangGraph graph inside the run. The runner neither knows nor needs that graph. The provider still
returns one run result through the ordinary steps.

<a id="contains-adoption"></a>

**Adoption** provides `survey` and `code_to_spec`, the Operations that describe existing code in
Specs for a project whose code came before them. The brownfield workflow usually runs them in
this order:

- A read-only survey proposes child Modules.
- The execution command `scaffold` creates them between the two Operations.
- `code-to-spec` workers describe each Module's code.

<a id="contains-validation"></a>

**Validation** provides `task-validation`, which decides whether the bound workspace is ready to
deliver. It:

- Checks the Spec structure.
- Finds the Modules the workspace changed.
- Runs their configured checks.
- Returns a [readiness](../glossary.json#concept.readiness) bound to the exact state it examined.

It changes nothing. It launches no worker.

<a id="contains-delivery"></a>

**Delivery** provides `delivery`, the only run that commits. It decides the readiness again
exactly as `task-validation` does. When the workspace is ready, it commits what is left as a
[delivery commit](../glossary.json#concept.delivery-commit) by the Kernel's convention. That commit
alone marks the workspace delivered.

<a id="contains-scaffold"></a>

**Scaffold** provides `scaffold`. Between a survey and the descriptions, it creates the child
Modules a survey's [decomposition proposal](../glossary.json#concept.decomposition-proposal) names.
It creates each as a stub Module that says plainly what is not specified yet. It returns a record
of exactly what it wrote. It never decides which Modules to create.

### What Method relies on

<a id="uses-distribution"></a>

**Distribution**, the installation host present in every installation, installs the method part
from its [part registration](../glossary.json#concept.part-registration). This is the plain data
its [registration contract](../distribution/contracts.md#contract.distribution.part-registration)
defines:

- The modules that register its Operations and execution commands, `task-validation`, `delivery`
  and `scaffold`.
- The brownfield workflow's script.
- Its guidance sections.
- LangGraph, the Python dependency its panels import.

Before Distribution routes `concorde run` or a
[workflow step](../glossary.json#concept.workflow-step) to the execution part, Method relies on
Distribution loading those modules. Method also relies on Distribution refusing a command of a
part that is not installed with `part_missing`. As the
[command line](../distribution/module.md#the-command-line) says, this is how its optional
integrations tell an absent part. Method imports nothing of Distribution.

<a id="uses-spec"></a>

**Spec core** loads the workspace's Specs, resolves the named Modules, and computes each worker's
grant and context identity. In their admission, Method's steps check the Modules a run names against the registry. They rely
on Spec core computing the same grant from the same Specs. Before any worker starts, they freeze
it through the library of [Spec core's contracts](../spec-tooling/spec/contracts.md).

Unless the definition diagnoses the Specs itself, as `task-validation` and `delivery` do, a Spec
that cannot be loaded is refused rather than partially read. The run then ends `failed`, with Spec
core's [error record](../spec-tooling/spec/errors.md#contract.spec.error) translated into the run's
link.

<a id="uses-workers"></a>

**Workers**, in the worker harness, launches every worker of Method's Operations. A step hands it:

- The grant as data.
- The instructions.
- The worker's identity.
- The [trace node](../glossary.json#concept.trace-node) folder of the run.
- The round validation.

Workers performs the rest. It returns the worker result with the evidence it gathered. Method
relies on Workers doing these:

- Launching the worker only under that grant.
- Auditing every write against it.
- Calling the round validation after each clean round.
- Keeping the worker's claims apart from what it measured.

A launch error, a timeout or an audit violation ends the run `failed`, with Workers' link as a
cause of the Operation's own.

<a id="uses-operations"></a>

**Operations** and **Commands** of Execution are the frameworks Method's definitions plug into.
Method registers these for each Operation and command:

- Its definition.
- Its steps.
- Its arguments.
- Whether it may run unbound.
- Its output contract.

For an Operation that may run unbound, Method also registers its runtime-path resolver.

<a id="uses-execution"></a>

**Execution**'s runner runs those definitions like any other. Method relies on it directly for
these actions:

- It reads the [workspace binding](../glossary.json#concept.workspace-binding).
- For a bound run, it holds the [workspace lock](../glossary.json#concept.workspace-lock).
- For an unbound run, it creates and removes the
  [unbound checkout](../glossary.json#concept.unbound-checkout).
- Before it links anything into that checkout, it calls the definition's runtime-path resolver.
- It builds the run's error link over the links Method's steps return.
- It writes the [run result](../glossary.json#concept.run-result), keeping the worker result apart
  from the host evidence.

Method's steps add the codes of [the worker sequence](workers.md#errors-of-the-worker-sequence).
They never write a result themselves. [How a run is executed](../execution/runner.md) is the
canonical account.

<a id="uses-checks"></a>

**Check execution** runs the project's configured checks for these:

- Method's round validations.
- `test`.
- The readiness of `task-validation` and `delivery`.

It returns each result's check id, status, exit code and log as evidence. It reads no Spec. From
the workspace's Specs and configuration, Method names these:

- The Modules whose checks run.
- The files each one's results depend on.
- The tests a selective check runs.
- The interpreter.

Method relies on two promises. A check's direct writes to the filesystem are confined to its own
scratch, with the workspace mounted read-only. When the inputs measured before and after the
check differ, Check execution refuses the result as `stale_evidence`.

Both have limits Method does not hide. A check can still ask a host service to act through a
socket. A change undone before the second measurement is not detected
([What the boundary enforces](../execution/checks/module.md#what-the-boundary-enforces)). A
configured check is the project's own trusted command. Method therefore treats a check's result
as evidence about the inputs it measured, not as proof that nothing else happened.

<a id="uses-workflows"></a>

**Workflows** runs the brownfield workflow's script. Under its step output convention, it reads
the following items that Method's Operations declare in their output:

- [decision points](../glossary.json#concept.decision-point).
- Decisions.
- Deviations.
- Notes.

This is how a survey's decisions stop an interactive workflow. This is also how the proposed
checks and a review's verdict reach the [workflow result](../glossary.json#concept.workflow-result).

<a id="uses-issues"></a>

**Issues** is an [optional integration](../glossary.json#concept.optional-integration). Where the
issues part is installed, `spec_review`, `spec_panel` and `code_review` do these:

- Report each finding as an Issue of the Module it concerns.
- Read the earlier Issues of a reviewed Module.
- Settle which a review carries or resolves.

Where it is not installed, they report nothing outside the run. In that case, every finding stays
in the run result with its tier. The result says that the findings were not recorded as Issues.

They reach Issues only through the issues part's
[bookkeeping command](../issues/interface.md#bookkeeping-command), `concorde issues` of the
worktree the run started in. They never reach it through its code. The command takes JSON in and
out through these:

- `list`.
- `show`.
- `report --provenance` with the provenance the Operation vouches for.

They write each finding as an [Issue report](../issues/interface.md#contract.issues.report). They
read back its [receipt](../issues/interface.md#contract.issues.receipt). The issues part counts as
not installed when that `concorde` does all of these, as
[Distribution](../distribution/module.md#the-command-line) does:

- Refuses `issues` as a command of a part the project has not installed.
- Prints `{"error": <link>}` with the code `part_missing`.
- Exits with status 1.
