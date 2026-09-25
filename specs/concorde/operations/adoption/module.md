# Adoption

## Purpose

Adoption describes a project whose code came before its Specs. It provides three Operations:
`survey` reads a Module's code and proposes how to split it into child Modules, `scaffold` creates
those child Modules from an accepted proposal, and `code_to_spec` has a worker read a Module's code
and write that Module's Spec. They are the only Operations that turn code into Specs, and they
exist for the uncommon project adopted after its code was written; a project specified first never
needs them. Adoption never changes code, records behaviour as it is instead of improving it, and
never writes a behaviour whose intent the code does not settle as a promise: such behaviour becomes
an open question for the developer.

## Terminology

| Term | Definition |
| --- | --- |
| Survey | The read-only Operation in which a worker reads one Module's code and proposes a decomposition, without writing anything. |
| Decomposition proposal | The output of a survey: the child Modules to create with their purposes, bound entries and uses, the checks it proposes, the decisions it took and its open questions. |
| Scaffold | The deterministic Operation that turns one accepted decomposition proposal into child Module stubs, a narrower parent realization and registry records. |
| Scaffold record | The output of a scaffold: the Modules and documents it created and the parent's realization entries before and after. |
| Code to spec | The Operation in which a worker of task type `code-to-spec` reads the bound Modules' code and writes their own documents to describe it. |
| Spec description | The output of a code_to_spec run: the documents changed, the promises written, the decisions taken, the open questions, the deviations between stated intent and code, and the validation outcome. |
| Decision | A choice between named options that a worker took where the code allowed several, recorded with its reason and whether the worker or the developer made it. |
| Open question | A behaviour the worker read but could not tell to be intended, reported with what it observed, why it is uncertain and the options, and written into no promise. |
| Answers | The developer's answers to earlier decisions and open questions, passed to a later survey or code_to_spec run so that its worker follows them. |
| Deviation | A difference between the intent the developer stated in an answer and what the code does, which the Spec states as intent and the result reports for later implementation work. |
| [Main agent](../../vocabulary.md#concept.concorde.main-agent) | |
| [Developer](../../vocabulary.md#concept.concorde.developer) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Module](../../vocabulary.md#concept.concorde.module) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Implementation context](../../vocabulary.md#concept.concorde.implementation-context) | |
| [Error chain](../../vocabulary.md#concept.concorde.error-chain) | |
| [Operation](../module.md#concept.operations.operation) | |
| [Operation host](../module.md#concept.operations.host) | |
| [Operation result](../module.md#concept.operations.result) | |
| [Run without a task](../module.md#concept.operations.no-task) | |
| [Grant](../../spec-tooling/spec/module.md#concept.spec.grant) | |
| [Structural check](../../spec-tooling/spec/module.md#concept.spec.structural-check) | |
| [Project registry](../../spec-tooling/spec/module.md#concept.spec.registry) | |
| [File transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction) | |
| [Brief](../../harness/workers/module.md#concept.workers.brief) | |
| [Worker result](../../harness/workers/module.md#concept.workers.worker-result) | |
| [Write audit](../../harness/workers/module.md#concept.workers.audit) | |
| [Configured check](../../harness/checks/module.md#concept.checks.configured-check) | |

Read Survey, Scaffold and Code to spec first: they are the three steps. Decisions and open questions
are how every step says what it could not settle alone; answers are how the developer settles them.

## Usage

Adoption starts where initialization leaves a project: a root Module whose realization binds every
existing file and whose entry says nothing is specified yet. The main agent opens a task bound to
that Module, usually through the [brownfield workflow](../../workflows/module.md), and runs the three
Operations in order:

```text
concorde run survey [--task <task-id>] --modules <module-id> [--answers <file>] [--input <run-id>]…
concorde run scaffold --task <task-id> --input <survey-run-id>
concorde run code_to_spec --task <task-id> --modules <module-id>[,<module-id>…] [--answers <file>] [--input <run-id>]…
```

```d2
survey: Survey
proposal: Decomposition proposal
scaffold: Scaffold
record: Scaffold record
codetospec: Code to spec
description: Spec description
decision: Decision
question: Open question
answers: Answers
survey -> proposal: produces
scaffold -> proposal: applies
scaffold -> record: produces
codetospec -> description: produces
proposal -> decision: lists
description -> decision: lists
description -> question: lists
answers -> question: settle
answers -> decision: settle
```

<a id="concept.adoption.survey"></a><a id="concept.adoption.decomposition"></a>

**Survey.** A worker reads the code of one Module, usually the root, and returns a **decomposition
proposal** ([contract](contracts.md#contract.adoption.decomposition)): for each child Module to
create, its identity, title, a one-paragraph purpose, the paths it should bind and the Modules it
uses with the reason; the test and lint commands it found, proposed in the shape of
[configured checks](../../harness/checks/module.md#concept.checks.configured-check) of the Modules
they check; the decisions it took; and its open questions. The host adds the entries that stay with
the surveyed Module. A proposal with no children is valid: the Module is small enough to describe as
it is. A survey writes nothing, so it may also run [without a
task](../module.md#concept.operations.no-task) to show the developer a proposal before any task
exists.

The host gives the worker, as task material, an inventory of every file the surveyed Module binds
with its size in lines, so the worker can plan what to read in a large codebase instead of opening
everything.

<a id="concept.adoption.scaffold"></a><a id="concept.adoption.scaffold-record"></a>

**Scaffold.** The host alone, with no worker, applies exactly one proposal admitted with `--input`
from an `ok` survey of the same task, and returns a **scaffold record**
([contract](contracts.md#contract.adoption.scaffold-record)). For each child it writes an entry
`module.md` and its metadata in a folder named after the child's identity, next to the parent's
entry, stating the survey's purpose, a realization binding the proposed entries, and the proposed
`uses`, with every other section saying honestly that it is not specified yet. It adds the children
to the parent's `contains` with one explaining paragraph each, removes the children's paths from the
parent's realizations and adds the registry records. Adding Modules is the project-level step the
Protocol reserves for the registry and the parent's `contains`, which is why it is a host step and
not a worker's. It never configures the proposed checks: a check is a command the host later runs,
and a command a model chose after reading code nobody vouched for must be accepted by the developer
first, so the checks stay a proposal the workflow reports. Everything is written in one
[file transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction) that is kept
only if validation finds no new error.

<a id="concept.adoption.code-to-spec"></a><a id="concept.adoption.spec-description"></a>

**Code to spec.** A worker of task type `code-to-spec` reads the bound Modules' code and their Specs
and rewrites their own documents: Purpose, Terminology, Usage, Design and Relationships of each
entry, and requirements, scenarios and contracts in implementation documents. The host prepares the
implementation documents the worker may need, `requirements.md`, `scenarios.md` and `contracts.md`,
as owned stubs before the grant is frozen, and removes again every stub the worker left unchanged,
however the run ends. The answers are checked before anything is written. The result's output is a **Spec description**
([contract](contracts.md#contract.adoption.spec-description)). Describing the root after its
children are scaffolded describes how the children compose and the files that stayed with it.

<a id="concept.adoption.decision"></a><a id="concept.adoption.open-question"></a>

**Decisions and open questions.** Workers of both Operations meet two kinds of uncertainty and
report each separately instead of hiding it in prose:

- A **decision** is a choice the code leaves open, such as whether two directories are one Module
  or two, or which name a concept gets. The worker takes it, with its options and reason, and goes
  on.
- An **open question** is about intent: the code does something, such as swallowing an error or
  treating one input specially, and nothing shows whether it is meant. The worker writes no promise
  about it. The Spec states it as an honest unknown, and the result reports what was observed, why
  it is uncertain, the options and a recommendation.

Neither Operation asks the developer: they have no one to ask. What happens next is the main
agent's or the workflow's choice: go on with the worker's decisions, or put them and the open
questions to the developer.

<a id="concept.adoption.answers"></a><a id="concept.adoption.deviation"></a>

**Answers.** The developer's answers reach a later run as an **answers** file
([contract](contracts.md#contract.adoption.answers)) with `--answers`, each naming the decision or
question it answers, the question's text and the answer; `--input` admits the run that asked, so the
worker sees the earlier proposal or description. An answers file lists every answer given so far for
that step, not only the latest. A survey rerun follows every answered decision. A
code_to_spec rerun writes an answered question as the promise the developer stated. When that intent
differs from what the code does, the Spec states the intent, and the result lists a **deviation**
with the intended and the observed behaviour, for later `implement` work: the Spec is again ahead of
the code, as Concorde expects.

Status follows the other worker-backed Operations. A survey or code_to_spec run is `ok` when the
worker completed its proposal or description, whatever decisions and open questions it lists. It is
`blocked` when the worker could not do the work at all, when a code_to_spec change adds a structural
error, or, for a scaffold, when the proposal no longer fits the worktree; the error chain then names
each finding or mismatch as a cause. It is `failed` when the request or the answers are invalid, the
host could not run the worker, the audit found a write outside the grant, or the output is
inconsistent, with every inconsistency listed in the Operation's own link. Every code is in the
[error table](contracts.md#errors).

## Design

The three Operations keep the Protocol's separation of reading, deciding and writing. The survey
worker reads code but writes nothing; deciding which Modules exist is then a deterministic host
step anyone can check against the proposal; describing a Module is a worker bounded by that Module's
own documents. A worker never adds or removes Modules, because the registry is outside every
Module's write set.

The `code-to-spec` task type is what makes this legal: it reads the bound Modules'
ImplementationScope and writes their SpecScope, which no other task type combines. The survey runs
under the same task type with the Spec side withheld, as the Protocol lets a harness give less than
a type assigns, so it can read code and write nothing. As for `specify`, the code_to_spec brief
states the rules for writing Spec documents and ends with the project's copy of the Protocol's
writing guide, since no grant shows the Protocol copy. Both workers get only Read, Glob and Grep,
and the code_to_spec worker also Edit and Write; neither gets Bash, so neither can run the code it
describes. What the code does is taken from reading it.

The survey and code_to_spec results hold decisions and open questions as structured lists, not prose,
because a workflow must count them to decide whether to stop in interactive mode, and must copy them
unchanged into its report in no-ask mode.

The code_to_spec host writes Specs itself before its worker runs, when it prepares the stubs. So it
checks the answers first, and removes every stub left unchanged on every way out of the run, a
failed grant or a stopped worker included: a run that ends early leaves behind only what its worker
changed.

Scaffold writes where it can decide by rules alone. A child's folder is the parent entry's folder
plus the child identity's last segment. The parent keeps every path its realizations covered that no
child took. A directory entry of the parent that contains a child's entry is replaced by the entries
below it that no child took: a directory stays one entry when no child took anything inside it, and
a file is listed exactly. A directory that would bind no file, such as an empty one or one holding
only skipped files, and a symbolic link are left out, as a directory entry never bound them.
Conversely a file a child's directory entry does not bind, such as a dot file the parent binds
exactly because its own directory entry skips it, stays with the parent. So no
path is bound by both parent and child unless the proposal deliberately gives one path to several
children.

How Adoption is built:

```d2
adoption: Adoption {
  survey: Survey Operation {
    "src/concorde/adoption/survey.py"
    "prompts/workers/survey.md"
  }
  scaffold: Scaffold Operation {
    "src/concorde/adoption/scaffold.py"
  }
  codetospec: Code to spec Operation {
    "src/concorde/adoption/code_to_spec.py"
    "prompts/workers/code-to-spec.md"
  }
  shared: Adoption shared records {
    "src/concorde/adoption/__init__.py"
    "src/concorde/adoption/records.py"
  }
  survey -> shared: validates proposals with
  scaffold -> shared: validates proposals with
  codetospec -> shared: validates answers with
}
```

<a id="realization.adoption.survey"></a>

The **Survey Operation** realization declares the `SURVEY` provider and its step table:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Check the answers; compute the inventory of the surveyed Module's bound files | host, Spec core | invalid answers (`failed`, `invalid_answers`); not exactly one Module (`failed`, `invalid_request`); Specs cannot load (`failed`, `specs_unloadable`) |
| 2 | Compute and freeze the `code-to-spec` grant with every writable level withheld | Workers, Spec core | the grant cannot be computed (`failed`, `grant_unavailable`) |
| 3 | Generate settings, tools and the brief with inventory, answers and inputs | Workers | — |
| 4 | Launch the worker and wait for its result | Workers, worker | launch error or timeout (`failed`); worker `blocked` or `failed` (passed on) |
| 5 | Audit: nothing is writable, so any change is a violation | Workers | any change (`failed`) |
| 6 | Check the proposal against the worktree and the answers; add the remaining entries | host | an inconsistency or an answer not followed (`failed`, `inconsistent_proposal`) |
| 7 | Return the Operation result | host | — |

<a id="realization.adoption.scaffold"></a>

The **Scaffold Operation** realization declares the `SCAFFOLD` provider, which launches no worker:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Admit exactly one `ok` survey of the same task as input | host | none or several, or not a survey (`failed`, `invalid_request`) |
| 2 | Validate the worktree as a baseline and check the proposal against it again | host, Spec core | the proposal no longer fits (`blocked`, `stale_proposal`) |
| 3 | Compute every file change: child entries, parent entry and realization, registry | host | a target file already exists (`blocked`, `stale_proposal`) |
| 4 | Apply them as one file transaction, kept only if validation finds no new error | host, Spec core | a new error (`failed`, `scaffold_invalid`), nothing kept |
| 5 | Return the Operation result with the scaffold record | host | — |

<a id="realization.adoption.code-to-spec"></a>

The **Code to spec Operation** realization declares the `CODE_TO_SPEC` provider:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Check the answers; validate the task worktree's Specs as a baseline | host, Spec core | invalid answers (`failed`, `invalid_answers`); Specs cannot load (`failed`, `specs_unloadable`) |
| 2 | Create the missing implementation document stubs of each bound Module and reconcile the registry mirror | host, Spec core | unknown Module (`failed`, `unknown_modules`) |
| 3 | Compute and freeze the `code-to-spec` grant | Workers, Spec core | the grant cannot be computed (`failed`, `grant_unavailable`, after step 7) |
| 4 | Generate settings, tools and the brief with the registered Modules, answers and inputs | Workers | — |
| 5 | Launch the worker and wait for its result | Workers, worker | launch error or timeout (`failed`); worker `blocked` or `failed` (passed on, after step 7) |
| 6 | Audit and write the run record | Workers | a write outside the grant (`failed`, after step 7) |
| 7 | Remove the stubs left unchanged, whatever steps 3 to 6 found; reconcile the registry mirror | host, Spec core | — |
| 8 | Validate again and compare with the baseline | host, Spec core | a new error (`blocked`, `new_structural_errors`) |
| 9 | Check the description against the answers and the bound Modules | host | an inconsistency or an answer not followed (`failed`, `inconsistent_description`) |
| 10 | Return the Operation result | host | — |

As with `specify`, a failed structural check starts no resume round: repairing a Spec needs a
decision, not another guess, so the run stops and the main agent or the workflow goes on.

<a id="realization.adoption.shared"></a>

The **Adoption shared records** realization holds the schemas of the decomposition proposal, the
answers and the decision and open-question records, and the checks the survey and the scaffold both
apply to a proposal.

<a id="realization.adoption.tests"></a>

Adoption is tried on real codebases from [SWE-bench](https://github.com/SWE-bench/SWE-bench),
vendored under `references/swe-bench/` at a fixed commit: its harness names the Python projects
it draws from, such as `psf/requests` and `pallets/flask`, which are existing codebases of known
size and quality to describe with the brownfield workflow.

The **Adoption tests**, under `tests/concorde/adoption/` with the existing-codebase fixture
`tests/concorde/support/brownfield_project.py` they share with Workflows, run the three Operations
against a small existing codebase with a fake worker, verifying the [requirements](requirements.md) and
[scenarios](scenarios.md).

## Relationships

```d2
adoption: Adoption
operations: Operations
workers: Workers
checks: Check execution
spec: Spec core
adoption -> operations
adoption -> workers
adoption -> checks
adoption -> spec
```

<a id="uses-operations"></a>

**Operations** lists `survey`, `scaffold` and `code_to_spec` in its catalog, dispatches to this
Module and provides the host runner, the admission of `--input` runs and the
[Operation result](../module.md#concept.operations.result) envelope. Adoption never calls another
Operation: the order of the three, and whether to ask the developer between them, is decided by the
main agent or a workflow.

<a id="uses-workers"></a>

**Workers** turns each frozen grant into settings, launches the survey and code_to_spec workers with
this Module's briefs, collects their [worker results](../../harness/workers/module.md#concept.workers.worker-result),
audits the worktree and writes the run records; any change beyond the grant fails the run.

<a id="uses-checks"></a>

**Check execution** defines the [configured check](../../harness/checks/module.md#concept.checks.configured-check)
entries of the project configuration. A survey proposes checks in that shape so that the
developer can configure the ones they accept unchanged; Adoption itself never runs or configures a
check.

<a id="uses-spec"></a>

**Spec core** computes the `code-to-spec` [grant](../../spec-tooling/spec/module.md#concept.spec.grant),
lists a Module's bound files, runs the [structural checks](../../spec-tooling/spec/module.md#concept.spec.structural-check),
regenerates the [registry](../../spec-tooling/spec/module.md#concept.spec.registry) mirror and
applies the scaffold's [file transaction](../../spec-tooling/spec/module.md#concept.spec.file-transaction),
always on the task worktree. Adoption relies on its checks as the definition of a valid Spec and adds
none of its own; a Spec that cannot be loaded ends the run `failed`.
