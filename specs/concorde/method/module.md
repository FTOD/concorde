# Method

## Purpose

Method is the method [part](../glossary.json#concept.part): Concorde's own Spec-driven way of
changing a project, built from the other parts. It provides the
[Operations](../glossary.json#concept.operation) in which AI workers understand, specify,
implement, test and review a project, the Adoption route that describes code which came before its
Specs, the [execution commands](../glossary.json#concept.execution-command) that decide readiness,
deliver and scaffold, the [brownfield workflow](../glossary.json#concept.brownfield-workflow), and
the [standard worker sequence](../glossary.json#concept.standard-worker-sequence) by which every
one of its workers is bounded by the Specs.

Method is where the other parts meet. The Spec tooling computes a grant but launches nothing; the
worker harness launches a worker under a grant it is given but reads no [Spec](../glossary.json#concept.spec); Execution runs a
definition's steps but knows no particular Operation; Workflows orders runs but knows no particular
procedure. Method's definitions and steps connect them: they take the grant from the Spec tooling,
hand it to the worker harness with a round validation, register their Operations and commands with
Execution, fill the output convention Workflows reads, and contribute the brownfield workflow's
script. A project that installs Method therefore installs the spec, worker harness, execution,
workflow and kernel parts with it; the issues part stays optional.

Method never chooses the next run, asks the developer anything or changes a Spec on its own
initiative: the task level, directly or through a workflow, orders its runs, and a promise the Spec
does not state stops the run as a [Spec gap](../glossary.json#concept.spec-gap).

## Core concepts

### The Operations and commands it provides

Every Operation is listed with its provider, the
[task type](../glossary.json#concept.task-type) of its workers, their
[worker ids](../glossary.json#concept.worker-id), whether it may run
[unbound](../glossary.json#concept.unbound-run), what it may change and its output. Method
registers these definitions with Execution, whose
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
| `survey` | [Adoption](adoption/module.md) | `code-to-spec`, Specs withheld | `worker` | yes | no | a [decomposition proposal](adoption/contracts.md#contract.adoption.decomposition) |
| `code_to_spec` | [Adoption](adoption/module.md) | `code-to-spec` | `worker` | no | Specs of the bound Modules, the registry mirror and the `verifies` links of the existing tests it describes | a [Spec description](adoption/contracts.md#contract.adoption.spec-description) |

"May change" covers both what a worker's grant makes writable and what the provider's own host
steps change in the workspace; each provider's Spec gives the rule. Method registers three
execution commands besides: [Validation](validation/module.md)'s `task-validation`, which decides
whether the bound workspace is ready to deliver; [Delivery](delivery/module.md)'s `delivery`, the
only run that commits, which decides the readiness again and makes the workspace's
[delivery commit](../glossary.json#concept.delivery-commit); and [Scaffold](scaffold/module.md)'s
`scaffold`, which creates the child Modules a survey proposed.

The findings of `spec_review`, `spec_panel` and `code_review` become
[Issues](../glossary.json#concept.issue) of the project only where the issues part is installed;
elsewhere each finding stays in the run result, and the verdict is derived from the findings' tiers
the same way. `plan_review`'s findings judge a plan within one run and always stay in its report
([requirements](requirements.md#optional-integrations)).

### The standard worker sequence

<a id="concept.standard-worker-sequence"></a>

Each Operation's control flow is a step table in its provider's Spec, which the runner runs in
order until one step stops the run. A worker-backed step follows the
**[standard worker sequence](../glossary.json#concept.standard-worker-sequence)**:

1. **Admit.** Before any of its provider's own steps, every Operation checks all the workers it may
   launch against the [worker configuration](../glossary.json#concept.worker-configuration) and
   the [model map](../glossary.json#concept.model-map), and the configuration's Operation names and
   worker ids against every Operation the installed parts register, so that a run never stops at a
   later worker, after earlier ones ran, for a configuration or model-map problem it could have
   found first ([what admission checks](workers.md#admitting-the-workers)).
2. **Bound.** The step computes the [grant](../glossary.json#concept.grant) for the task type and
   Modules from the **workspace's** Specs through Spec core, lowers every writable level to read when
   its provider withholds writes, freezes the result with the computed grant's
   [context identity](../glossary.json#concept.context-identity), and converts it into the worker
   harness's input format.
3. **Instruct.** It composes the task instructions: the provider's prompt, the definitions of the
   glossary terms the bound Modules use, and the rules about Spec gaps and paths outside the grant.
4. **Launch.** It hands the grant, the instructions, the worker's identity and the
   **round validation** to the worker harness, which prepares the settings and the
   [brief](../glossary.json#concept.brief), launches the worker, runs the
   [write audit](../glossary.json#concept.write-audit), calls the round validation after each clean
   round, resumes the worker with what it reports to repair while rounds remain, and writes the
   [run record](../glossary.json#concept.run-record).
5. **Decide.** It keeps the [worker result](../glossary.json#concept.worker-result) unchanged and
   decides what the outcome means for the run.

The round validation is Method's, and checks in this order: first glossary ownership, which ends
the run at once when the worker changed a glossary entry that a
[Module](../glossary.json#concept.module) outside its grant owns; then, when the step asks for
them, the [configured checks](../glossary.json#concept.configured-check) of the bound Modules and of
every Module that uses one of them, through Check execution, outside the worker; then, when every
check passed or none ran, the step's own validation, if it has one, such as the structural
validation a Spec-writing step runs instead of configured checks. It returns the
[check results](../glossary.json#concept.check-result) as the round's evidence and what failed as
what to repair. Glossary ownership is checked once more after the worker run, whatever the worker's
status, so that no round and no deletion escapes it. A [Spec gap](../glossary.json#concept.spec-gap)
or a path outside the grant is never something to repair. [How an Operation runs its
workers](workers.md#the-round-validation) gives the sequence exactly.

### The brownfield workflow

<a id="concept.brownfield-workflow"></a>

The **[brownfield workflow](../glossary.json#concept.brownfield-workflow)** describes a project
whose code came before its Specs, one Module and its new children at a time: a survey, the scaffold
of the Modules it proposed, a `code_to_spec` run per Module, a Spec review, task validation and
delivery. Its arguments add `module`, the Module to describe, usually the root. Splitting a created
child further is a new workspace running the workflow on that child, since a workspace's [step keys](../glossary.json#concept.step-key),
`validate` and `delivery` included, belong to one procedure. Method contributes its
[workflow script](../glossary.json#concept.workflow-script), which names `delivery` as its last
step and reads the scaffold's created Modules from that run's output itself; its decision points
are those its Operations declare in the [step output convention](../workflows/contracts.md):
every decision the survey took itself and every [open question](../glossary.json#concept.open-question).
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
admit: "Admit every worker:\nconfiguration and model map"
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
steps produced — grant, context identity, write audit, each check's exit code and log,
[resume rounds](../glossary.json#concept.resume-round) used, transcript path, worker stderr — so the caller reads the claim as a claim and the
evidence as fact. An `implement` worker that claims the goal is done while one check still fails
after the last resume round ends the run `failed`, its claim kept unchanged and its chain naming
the Operation, Workers' rounds and the check's log.

## How it is built

### Why the method is a part of its own

The concrete way Concorde changes a project — which Operations exist, what each worker is told, how
readiness is decided and what a delivery requires — changes far more often than the mechanisms it
uses, and a project may want those mechanisms without this method: the worker harness under another
orchestrator, Execution for its own definitions, task management with its own delivery. Keeping the
method in one part that depends on the others, and nothing depending on it, lets each mechanism be
installed and changed without it, while the method composes them exactly as Concorde works.

The grant always comes from the workspace's Specs, never the primary worktree's, so a task that
changes a Spec is bounded by the Spec as its workspace sees it; an unbound run reads its
[unbound checkout](../glossary.json#concept.unbound-checkout) of the worktree it started in and may
launch only reading workers, since only a bound workspace may change. One workspace runs one run at
a time, because two runs in one worktree would audit each other's writes as their own, so
parallelism comes from running workspaces side by side. No provider calls another Operation: the
task level or its workflow decides which runs next.

### Code

The providers' and commands' code lives with their Modules. The standard worker sequence is today
the run context's worker launch in Execution's runner package, the admission step is in
`src/concorde/execution/operations/`, and the brownfield script in `src/concorde/workflows/scripts/`;
those Modules' realizations bind them until the code tasks that follow this Spec move them into
Method's package.

<a id="realization.method.review-issues"></a>

**Review Issues**, `src/concorde/method/review_issues.py`, is the review providers' shared handling
of their Issues: reading a reviewed Module's earlier Issues, settling which a review carries or
resolves and reporting its findings, all through the issues command as [Issues](#uses-issues) says,
and stating in the result that the findings were not recorded where the issues part is not
installed.

### The children

<a id="contains-understanding"></a>

**Understanding** provides `understand` and `plan_review`. In `understand` a worker reads the bound
Modules' Specs and file names and returns an assessment, changing nothing; its output is advice to
the task level, never an instruction to the runner. It may run unbound, which is how the [main agent](../glossary.json#concept.main-agent)
answers a question before any change is agreed. In the optional `plan_review` a reviewer reads the
Specs and the code and judges a plan the task level wrote, changing nothing; the task level answers
its findings in the next run, with the previous run as `--input`, until the verdict is `accepted`.
It needs a bound workspace, whose goal the plan is judged against.

<a id="contains-specification"></a>

**Specification** provides `specify`: a worker edits the bound Modules' own Spec documents and the
Operation validates the result. It is the Operation that changes what a Module promises:
`code_to_spec` writes Specs only to describe existing code, and `implement` changes no Spec, so the
task level routes every Spec repair through `specify` or does it itself.

<a id="contains-implementation"></a>

**Implementation** provides `implement` and `test`. In `implement` a worker changes the bound
Modules' code under a grant that makes only that code writable, and its round validation runs their
checks with resume rounds until they pass or the rounds run out, so its result says whether the
checks passed on the changed code. In `test` a read-only worker interprets the checks the Operation
ran and returns a test report; the check results, not the worker's reading of them, are the
evidence. Both need a bound workspace.

<a id="contains-code-review"></a>

**Code review** provides `code_review`: a worker judges code against the Specs and returns
findings, changing nothing, either a workspace's change since the binding's base commit, or since
`--base` when it runs unbound, or, with `--scope module`, each named Module's whole code, one worker
per Module. The Operation keeps the findings as the workers' claims, checks their evidence, reports
each as an Issue where the issues part is installed and derives the verdict from the findings'
tiers; acting on a finding is the task level's decision.

<a id="contains-spec-review"></a>

**Spec review** provides `spec_review` and `spec_panel`: reviewers read the bound Modules' Specs and
return findings, changing nothing. The findings stay the workers' claims, while the provider derives
the verdict from them and reports each as an [Issue](../glossary.json#concept.issue) where the
issues part is installed, in bound and unbound runs alike; the primary worktree keeps those Issues,
so the workspace does not change. `spec_panel` is the one provider whose steps run a LangGraph graph
inside the run, which the runner neither knows nor needs: the provider still returns one run result
through the ordinary steps.

<a id="contains-adoption"></a>

**Adoption** provides `survey` and `code_to_spec`, the Operations that describe existing code in
Specs for a project whose code came before them: a read-only survey proposes child Modules, the
execution command `scaffold` creates them between the two, and `code-to-spec` workers describe each
Module's code. The brownfield workflow usually runs them in that order.

<a id="contains-validation"></a>

**Validation** provides `task-validation`, which decides whether the bound workspace is ready to
deliver: it checks the Spec structure, finds the Modules the workspace changed, runs their
configured checks and returns a [readiness](../glossary.json#concept.readiness) bound to the exact
state it examined. It changes nothing and launches no worker.

<a id="contains-delivery"></a>

**Delivery** provides `delivery`, the only run that commits: it decides the readiness again exactly
as `task-validation` does and, when the workspace is ready, commits what is left as a
[delivery commit](../glossary.json#concept.delivery-commit) by the Kernel's convention, which alone
marks the workspace delivered.

<a id="contains-scaffold"></a>

**Scaffold** provides `scaffold`, which creates, between a survey and the descriptions, the child
Modules a survey's [decomposition proposal](../glossary.json#concept.decomposition-proposal) names,
each as a stub Module that says plainly what is not specified yet, and returns a record of exactly
what it wrote; it never decides which Modules to create.

### What Method relies on

<a id="uses-spec"></a>

**Spec core** loads the workspace's Specs, resolves the named Modules, and computes each worker's
grant and context identity. Method's steps check the Modules a run names against the registry in
their admission, rely on Spec core computing the same grant from the same Specs, and freeze it before
any worker starts. A Spec that cannot be loaded is refused rather than partially read, ending the run
`failed`, unless the definition diagnoses the Specs itself, as `task-validation` and `delivery` do.

<a id="uses-workers"></a>

**Workers**, in the worker harness, launches every worker of Method's Operations. A step hands it the
grant as data, the instructions, the worker's identity, the [trace node](../glossary.json#concept.trace-node) folder of the run and the
round validation; Workers performs the rest and returns the worker result with the evidence it
gathered. Method relies on Workers launching the worker only under that grant, auditing every write
against it, calling the round validation after each clean round and keeping the worker's claims
apart from what it measured. A launch error, a timeout or an audit violation ends the run `failed`,
with Workers' link as a cause of the Operation's own.

<a id="uses-operations"></a>

**Operations** and **Commands** of Execution are the frameworks Method's definitions plug into:
Method registers each Operation's and command's definition, its steps, arguments, whether it may run
unbound, its output contract and, for an Operation that may run unbound, its runtime-path resolver.

<a id="uses-execution"></a>

**Execution**'s runner runs those definitions like any other, and Method relies on it directly: it
reads the [workspace binding](../glossary.json#concept.workspace-binding), holds the
[workspace lock](../glossary.json#concept.workspace-lock) of a bound run, creates and removes an
unbound run's [unbound checkout](../glossary.json#concept.unbound-checkout), calling the
definition's runtime-path resolver before it links anything into it, builds the run's error link
over the links Method's steps return, and writes the [run result](../glossary.json#concept.run-result),
keeping the worker result apart from the host evidence. Method's steps add the codes of
[the worker sequence](workers.md#errors-of-the-worker-sequence) and never write a result
themselves; [How a run is executed](../execution/runner.md) is the canonical account.

<a id="uses-checks"></a>

**Check execution** runs the project's configured checks for Method's round validations, for
`test` and for the readiness of `task-validation` and `delivery`, returning each result's command,
exit code and log as evidence. Method relies on two promises: a check's direct writes to the
filesystem are confined to its own scratch, the workspace being mounted read-only, and a result is
refused as `stale_evidence` when the inputs it measured before and after the check differ. Both
have limits Method does not hide: a check can still ask a host service to act through a socket, and
a change undone before the second measurement is not detected
([What the boundary enforces](../execution/checks/module.md#what-the-boundary-enforces)). A
configured check is the project's own trusted command, so Method treats a check's result as
evidence about the inputs it measured, not as proof that nothing else happened.

<a id="uses-workflows"></a>

**Workflows** runs the brownfield workflow's script and reads the
[decision points](../glossary.json#concept.decision-point), decisions, deviations and notes
Method's Operations declare in their output under its step output convention, which is how a
survey's decisions stop an interactive workflow and how the proposed checks and a review's verdict
reach the [workflow result](../glossary.json#concept.workflow-result).

<a id="uses-issues"></a>

**Issues** is an [optional integration](../glossary.json#concept.optional-integration). Where the
issues part is installed, `spec_review`, `spec_panel` and `code_review` report each finding as an
Issue of the Module it concerns, read the earlier Issues of a reviewed Module and settle which a
review carries or resolves; where it is not, they report nothing outside the run, every finding
stays in the run result with its tier, and the result says that the findings were not recorded as
Issues. They reach Issues only through the issues part's
[bookkeeping command](../issues/interface.md#bookkeeping-command), `concorde issues` of the worktree
the run started in, JSON in and out (`list`, `show`, and `report --provenance` with the provenance
the Operation vouches for), never through its code; the issues part counts as not installed when
that `concorde` refuses `issues` as a command of a part the project has not installed, or offers no
such command at all.
