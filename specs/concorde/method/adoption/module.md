# Adoption

## Purpose

Adoption describes a project whose code came before its Specs. It provides two Operations:

- `survey` has a worker read a [Module](../../glossary.json#concept.module)'s code and propose
  how to split it into child Modules.
- `code_to_spec` has a worker read a Module's code and write that Module's
  [Spec](../../glossary.json#concept.spec).

Between them the [execution command](../../glossary.json#concept.execution-command) `scaffold` of
[Scaffold](../scaffold/module.md) creates the proposed child Modules. The three are the only runs
that turn code into Specs. They exist for the uncommon project adopted after its code was written.
A project specified first never needs them. Adoption never changes what code does. It records
behaviour as it is instead of improving it. When the code does not settle a behaviour's intent,
Adoption never writes that behaviour as a promise. Such behaviour becomes an
[open question](../../glossary.json#concept.open-question) for the developer. The one edit it
makes outside Specs marks the project's existing tests with the scenarios taken from them.

## Core concepts

### Decomposition proposal

<a id="concept.decomposition-proposal"></a>

A survey worker reads the code of one Module, usually the root. It returns a **decomposition
proposal** ([contract](contracts.md#contract.adoption.decomposition)) with these items:

- Each child Module to create, with these details:
  - Its identity.
  - Its title.
  - Its one-paragraph purpose.
  - The paths it should bind.
  - The Modules it uses with the reason.
- The third-party code the project vendors, such as a bundled copy of a library, each with the
  Module that uses it.
- The test and lint commands it found, proposed in the shape of
  [configured checks](../../glossary.json#concept.configured-check) of the Modules they check.
- The decisions it took.
- Its open questions.

The host adds the realization entries, the bound paths, that stay with the surveyed Module. A
proposal with no children is valid: the Module is small enough to describe as it is.

### Spec description

A `code_to_spec` worker rewrites the bound Modules' own documents from their code. The result's
output is a **Spec description** ([contract](contracts.md#contract.adoption.spec-description)).

### Decisions and open questions

<a id="concept.open-question"></a>

Workers of both Operations meet two kinds of uncertainty. They report each separately instead of
hiding it in prose:

- A **decision** is a choice the code leaves open, such as whether two directories are one Module
  or two, or which name a concept gets. The worker takes it, with its options and reason. It goes
  on. It names each option by a short identity of its own. It names its choice by that identity.
  The host records the chosen option's text. It records that the worker decided it. This means no
  worker has to repeat an option word for word.
- An **open question** is about intent. The code does something, such as swallowing an error or
  treating one input specially. Nothing shows whether it is meant. The worker writes no promise
  about it. The Spec states it as an honest unknown. The result reports these items:
  - What was observed.
  - Why it is uncertain.
  - The options.
  - A recommendation.

Neither Operation asks the developer: they have no one to ask. The task level or the workflow
chooses what happens next: go on with the worker's decisions, or seek answers through the existing
escalation path. When its authority covers a decision, the main agent settles it through that path.
Otherwise, the developer settles it.

This Module, not the workflow, says which of them a workflow stops for. Each run's output lists
them again under the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output) that
[Workflows](../../workflows/module.md) reads. Since how a project splits into Modules shapes all
later work, a survey declares these items as a
[decision point](../../glossary.json#concept.decision-point):

- Every decision its worker took itself.
- Every open question.

A survey lists every decision it reports among `decisions` as well. A decision point of kind
`decision` keeps the same identity. A survey declares its proposed checks as `notes` for the
developer. A code_to_spec run declares its open questions as decision points of kind `question`.
Its decisions are ordinary. It declares them as `decisions` the workflow only reports. Both list
their deviations as `deviations`
([req.adoption.step-output](requirements.md#req.adoption.step-output)).

### Answers and deviations

The answers reach a later run as an **answers** file
([contract](contracts.md#contract.adoption.answers)) with `--answers`. Each answer names these
items:

- The decision or question it answers.
- The question's text.
- The answer.
- Who settled it, the main agent or the developer.

The worker lists an answered decision without choosing. The host records the answer as its choice.
It records whoever gave the answer as the one who decided it. This means the record never credits
the developer with a choice the main agent made. `--input` admits the run that asked, so the worker
sees the earlier proposal or description. An answers file lists every answer given so far for that
step, not only the latest.
A survey rerun follows every answered decision. It no longer lists an answered open question. A
code_to_spec rerun writes an answered question as the promise the answer states. When that intent
differs from what the code does, the Spec states the intent. In that case, the result lists a
**deviation** with the intended and the observed behaviour, for later `implement` work. The Spec
is again ahead of the code, as Concorde expects.

## Overview

The path through the three steps, with the reruns that answers lead to:

```d2 illustrative
direction: down
survey: "concorde run survey"
inspect: "The task level inspects\nthe decomposition proposal"
scaffold: "concorde scaffold --input <survey run>"
describe: "concorde run code_to_spec\n(the brownfield workflow: one Module at a time,\ncreated Modules providers first, the surveyed Module last)"
review: "The task level inspects\neach Spec description"
implement: "implement, for each deviation"
survey -> inspect
survey <- inspect: "developer's answers:\n--answers, --input <survey run>" {style.stroke-dash: 3}
inspect -> scaffold: proposal accepted
scaffold -> describe -> review
describe <- review: "developer's answers:\n--answers, --input <code_to_spec run>" {style.stroke-dash: 3}
review -> implement: an answered intent differs from the code {style.stroke-dash: 3}
```

The records the runs produce, and what answers settle in them:

```d2 illustrative
survey: Survey
proposal: Decomposition proposal
codetospec: Code to spec
description: Spec description
decision: Decision
question: Open question
answers: Answers
survey -> proposal: produces
codetospec -> description: produces
proposal -> decision: lists
description -> decision: lists
description -> question: lists
answers -> question: settle
answers -> decision: settle
```

## Running the three steps

Adoption starts where initialization leaves a project: a root Module with these properties:

- Its realization binds every existing file.
- Its entry says nothing is specified yet.

The [main agent](../../glossary.json#concept.main-agent) opens a task bound to that Module. It
hands the task to the task's [task session](../../glossary.json#concept.task-session). The task
session runs the three steps in order in its task worktree. It runs them directly or through
Method's [brownfield workflow](../../glossary.json#concept.brownfield-workflow)
([how it runs](../brownfield.md)).
Within its authority, the main agent settles the
[decision points](../../glossary.json#concept.decision-point). It puts the rest to the developer:

```text
concorde run survey --modules <module-id> [--answers <file>] [--input <run-id>]…
concorde scaffold --input <survey-run-id>
concorde run code_to_spec --modules <module-id>[,<module-id>…] [--answers <file>] [--input <run-id>]…
```

Each works on the [workspace](../../glossary.json#concept.workspace) of the worktree it starts
in. The worktree's binding names that workspace. Each is recorded in the
[run store](../../glossary.json#concept.run-store) like any run. This lets the scaffold admit the
survey. It also lets a later survey or code_to_spec admit the run whose questions it answers.

**Survey.** A survey writes nothing. It may therefore also run
[unbound](../../glossary.json#concept.unbound-run), in the primary worktree, to show the
developer a proposal before any task exists. As task material, the host gives the worker an
inventory of every file the surveyed Module binds. The inventory gives each file's size in lines.
This lets the worker plan what to read in a large codebase instead of opening everything. The inventory is a file of
the run's [trace node](../../glossary.json#concept.trace-node). The worker may read it beside its
grant. The brief names it with a summary: the number of files and lines in all and under each
top-level path. Thus no number of files makes the brief too long. No file is left out.

The inventory leaves out the files of the surveyed Module's Concorde installation realization.
These files stay with the surveyed Module:

- The skill the installer placed.
- The workflows the installer placed.
- The agents the installer placed.

When a proposal gives one of them to a child, it fails. They configure the agents, not the project.
The installer replaces them on every update.

A survey proposes against the Module as it is. In a workspace where a scaffold already wrote to
the surveyed Module, a survey never runs. Before any worker starts, it ends `failed` with
`fresh_workspace_required`. Revising a survey after its scaffold ran requires a fresh workspace,
a new task in Concorde. In that workspace, the survey runs again with the answers that revise it.
Nothing the scaffold or a later run wrote in the first workspace is undone. The task level decides
whether to keep or discard that workspace.

The host tells a scaffold's writes from the surveyed Module's entry metadata alone. It identifies
these additions compared with the same metadata at the workspace's base commit:

- A Module it contains.
- An external inclusion it has.

These are exactly the additions a scaffold makes to the Module it applies a proposal to
([req.adoption.survey-after-scaffold](requirements.md#req.adoption.survey-after-scaffold)).

**Scaffold.** The execution command `concorde scaffold` of
[Scaffold](../scaffold/module.md) has no worker. It applies exactly one proposal admitted
with `--input` from an `ok` survey of the same workspace. It takes these steps:

- It creates each proposed child as a stub Module that states the survey's purpose. The stub says
  honestly that nothing else is specified yet.
- It narrows the parent's realizations.
- It makes vendored code an external inclusion of its user.
- It returns a scaffold record.

Adding Modules is a project-level step no worker's write set includes. That is why deterministic
code makes it and not a worker. It is also why it is not an
[Operation](../../glossary.json#concept.operation) of this Module.

**Code to spec.** A worker of [task
type](../../glossary.json#concept.task-type) `code-to-spec` reads the bound Modules' code and
their Specs. It rewrites their own documents:

- Each entry document (`module.md`), in the reading order the Protocol recommends.
- The glossary entries of the words they own.
- Requirements, scenarios and contracts in implementation documents.

Before the host freezes the grant, it prepares these implementation documents the worker may need
as owned stubs:

- `requirements.md`.
- `scenarios.md`.
- `contracts.md`.

However the run ends, the host removes every stub the worker left unchanged or deleted. Before
anything is written, the host checks the answers. After its children are scaffolded, describing
the root describes how the children compose and the files that stayed with it.

**Statuses.** Status follows the other worker-backed Operations. When the worker completes its
proposal or description, a survey or code_to_spec run is `ok`, whatever decisions and open
questions it lists. Under either of these conditions, it is `blocked`:

- The worker could not do the work at all.
- A code_to_spec change adds a structural error.

The [error chain](../../glossary.json#concept.error-chain) then names each finding as a cause.
Under any of these conditions, it is `failed`:

- The request or the answers are invalid.
- A survey's workspace already holds a scaffold's writes.
- The host could not run the worker.
- The audit found a write outside the grant.
- The output is inconsistent.

For inconsistent output, the Operation's own link lists every inconsistency. Every code is in the
[error table](contracts.md#errors).

## Why it is built this way

The two Operations and the scaffold between them keep the Protocol's separation of reading, deciding
and writing. They divide the work as follows:

- The survey worker reads code but writes nothing.
- Scaffold deterministically decides which Modules exist. Anyone can check this against the proposal.
- A worker bounded by a Module's own documents describes that Module.

Because the registry is outside every Module's write set, a worker never adds or removes Modules.

The `code-to-spec` task type makes this legal. It combines reading the bound Modules'
ImplementationScope with writing their SpecScope, which no other task type combines. The survey runs
under the same task type with every writable level withheld. The Protocol lets a harness give less
than a type assigns. Thus the survey reads the code and the Specs its grant names and writes nothing.
As for `specify`, the code_to_spec brief states the rules for writing Spec documents.
Since no grant shows the [Protocol copy](../../glossary.json#concept.protocol-copy), the brief ends
with the project's copy of Spec writing guidelines. That guide includes these parts:

- The overview.
- Required format.
- Writing guidance.
- Sentence style.
- Evaluating a Spec.
- Templates.

It covers machine-checkable structure and syntax. It also covers content requiring reader and
editor judgment. Structural validation does not establish semantic sufficiency. Both workers get
only Read, Glob and Grep. The code_to_spec worker also gets Edit and Write. Since neither gets
Bash, neither can run the code it describes. What the code does is taken from reading it.

Because a workflow must count them, the survey and code_to_spec results hold decisions and open
questions as structured lists, not prose. The workflow counts them to decide whether to stop in
interactive mode. In no-ask mode, it must copy them unchanged into its report.

Wherever a worker would otherwise have to repeat something exactly, the host writes it instead. A
worker restating an option in its own words is not a wrong choice. The worker therefore names
options by identities. The host copies the text. Since its working directory is not the worktree,
the worker's tools take absolute paths. The outputs name project-relative paths. The brief asks
for relative paths in the result. When a path begins with the worktree's own path, it is unambiguous.
The host therefore writes it relative instead of failing the run.

When it prepares the stubs before its worker runs, the code_to_spec host writes Specs itself. It
therefore checks the answers first. On every way out of the run, it removes every stub left
unchanged, including after a failed grant or a stopped worker. A run that ends early leaves behind
only what its worker changed.

## How it is built

```d2
adoption: Adoption {
  survey: Survey Operation {
    "src/concorde/method/adoption/survey.py"
    "prompts/workers/survey.md"
  }
  codetospec: Code to spec Operation {
    "src/concorde/method/adoption/code_to_spec.py"
    "prompts/workers/code-to-spec.md"
  }
  shared: Adoption shared records {
    "src/concorde/method/adoption/__init__.py"
    "src/concorde/method/adoption/records.py"
  }
  survey -> shared: validates proposals with
  codetospec -> shared: validates answers with
}
```

<a id="realization.adoption.survey"></a>

The **Survey Operation** realization declares the `SURVEY` provider and its step table:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Check the answers; in a bound workspace, compare the surveyed Module's entry metadata with the workspace's base commit; write the inventory of the surveyed Module's bound files to the run's trace node | host, Spec core | invalid answers (`failed`, `invalid_answers`); not exactly one Module (`failed`, `invalid_request`); Specs cannot load, now or at the base commit (`failed`, `specs_unloadable`); a scaffold's writes (`failed`, `fresh_workspace_required`) |
| 2 | Compute and freeze the `code-to-spec` grant with every writable level withheld | Operation, Spec core | the grant cannot be computed (`failed`, `grant_unavailable`) |
| 3 | Generate settings, tools and the brief with the inventory file, readable beside the grant, its summary, answers and inputs | Workers | — |
| 4 | Launch the worker and wait for its result | Workers, worker | launch error or timeout (`failed`); worker `blocked` or `failed` (passed on) |
| 5 | Audit: nothing is writable, so any change is a violation | Workers | any change (`failed`) |
| 6 | Write the paths inside the worktree relative to it and record the decisions; check the proposal against the worktree and the answers; add the remaining entries | host | an inconsistency, a decision without a valid choice or an answer not followed (`failed`, `inconsistent_proposal`) |
| 7 | Return the run result | host | — |

<a id="realization.adoption.code-to-spec"></a>

The **Code to spec Operation** realization declares the `CODE_TO_SPEC` provider:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Check the answers; validate the workspace's Specs as a baseline | host, Spec core | invalid answers (`failed`, `invalid_answers`); Specs cannot load (`failed`, `specs_unloadable`) |
| 2 | Create the missing implementation document stubs of each bound Module and reconcile the registry mirror | host, Spec core | unknown Module (`failed`, `unknown_modules`) |
| 3 | Compute and freeze the `code-to-spec` grant | Operation, Spec core | the grant cannot be computed (`failed`, `grant_unavailable`, after step 7) |
| 4 | Generate settings, tools and the brief with the registered Modules, the structural errors already in the described Modules' documents, answers and inputs | Workers | — |
| 5 | Launch the worker and wait for its result; after each round validate and, at most twice, resume it with the errors the run is judged by | Workers, worker, host | launch error or timeout (`failed`); worker `blocked` or `failed` (passed on, after step 7) |
| 6 | Audit and write the [run record](../../glossary.json#concept.run-record) | Workers | a write outside the grant (`failed`, after step 7) |
| 7 | Remove the stubs left unchanged or deleted through the worker's proposed deletions from their Modules' documents, whatever steps 3 to 6 found; reconcile the registry mirror | host, Spec core | — |
| 8 | Validate again and compare with the baseline | host, Spec core | an error the run counts as its own, left after the last round (`blocked`, `new_structural_errors`) |
| 9 | Write the paths inside the worktree relative to it and record the decisions; check the description against the answers and the bound Modules | host | an inconsistency, a decision without a valid choice or an answer not followed (`failed`, `inconsistent_description`) |
| 10 | Link the existing tests each scenario was taken from | host | — (a link it cannot make is reported in `unlinked_tests`) |
| 11 | Return the run result | host | — |

A scenario the worker took from existing tests names them in its promise's `tests`, as
`path::name` or `path::Class::name`. The worker never edits a test. In step 10, the host adds a
`verifies` decorator above each named test that exists in a Module's implementation file. Once per
file, it adds a two-line no-op definition of `verifies` after the file's docstring and imports.
This keeps the project's tests free of any import of Concorde. They run the same in the project's
own environment. The coverage check sees which test verifies which scenario.

The host finds a test where the coverage check finds it:

- In the module body.
- In a class body.
- Under a control-flow statement such as a top-level `if` or `try`.

It never finds a test inside a function. When a name is defined more than once in those places, the
host reports it, since it cannot tell which definition is the test. The host adds nothing else. It adds
nothing twice. It leaves every byte already in the file as it was, including its line endings and
blank lines. What it inserts takes the file's own line ending and indentation. The blank lines it
adds around the helper only make up the two that set it apart.

When the decorated file would not parse or cannot be written, the host leaves the file untouched.
It replaces a file only through a new file beside it, so that a failed write leaves the original
whole. It reports the links of such a file. It links the next file all the same.

When a file already binds `verifies` at module level, the host keeps that binding. This applies to
bindings by any of these forms:

- A statement.
- An `except` clause.
- An assignment expression.
- A match pattern.

The host adds only decorators when the binding is one of these:

- Its own no-op helper, however formatted.
- An import of Concorde's decorator from `concorde.spec.verification`, standing at the file's top
  level before the test.

Otherwise, the host leaves the file untouched. It reports each of the file's links in
`unlinked_tests`. A decorator would call the project's own `verifies`, whatever it does, or find no
`verifies` at all when the module is imported. Only Python tests are linked.

Unlike `specify`, every structural error in a described Module's own documents counts as the
run's, even one the baseline already had. The worker rewrites those documents. A retry must not
inherit a failed attempt's errors as the project's. As with `specify`, the host validates after each
round. It resumes the worker, at most twice, with the errors the run is judged by, so the worker
repairs what it broke itself. Only errors left after the last round stop the
run as `blocked`. The task level or the workflow goes on.

<a id="realization.adoption.shared"></a>

The **Adoption shared records** realization holds these schemas and checks:

- The schema of the [decomposition proposal](../../glossary.json#concept.decomposition-proposal).
- The schema of the answers.
- The schemas of the decision and open-question records.
- The checks of a proposal against a worktree.

The survey applies those checks. Before writing, [Scaffold](../scaffold/module.md) applies them
again.

<a id="realization.adoption.tests"></a>

Adoption is tried on real codebases with real workers by
[End-to-end testing](../../e2e/module.md), on projects from SWE-bench.

The **Adoption tests** are under `tests/concorde/adoption/`. They share these with Workflows and
Scaffold:

- The existing-codebase fixture `tests/concorde/support/brownfield_project.py`.
- The adoption test case `tests/concorde/support/adoption_case.py`.

After a scaffold, the tests run the survey and code_to_spec in a bound task worktree of a small
existing codebase with a fake worker. They verify the [requirements](requirements.md) and
[scenarios](scenarios.md).

## What it relies on

<a id="uses-execution"></a>

**Execution**'s runner runs both. It takes these steps:

- It reads the [workspace binding](../../glossary.json#concept.workspace-binding).
- It holds the [workspace lock](../../glossary.json#concept.workspace-lock).
- It admits `--input` runs only when they ended `ok` in the same workspace (or, for an unbound
  survey, in none).
- It wraps each output in the [run result](../../glossary.json#concept.run-result).

It refuses code_to_spec unbound. Adoption relies on it admitting only runs of the same workspace
as inputs. Thus a rerun sees only that workspace's earlier proposal or description.

<a id="uses-operations"></a>

**Operations**, Execution's Operation framework, is what both plug into. Method registers `survey`
and `code_to_spec` with it, naming this Module as their provider
([Method](../module.md#the-operations-and-commands-it-provides)). The `survey` Operation is the one
Adoption Operation whose definition lets it run unbound. Adoption never starts another run. The
task level or a workflow decides these matters:

- The order of the survey, the scaffold and code_to_spec.
- Whether to seek the developer's answers between them through the existing escalation path.

<a id="uses-workers"></a>

Through Method's [standard worker sequence](../../glossary.json#concept.standard-worker-sequence),
**Workers**, in the worker harness, receives each frozen grant as data. It also receives
code_to_spec's round validation. It takes these steps:

- It turns the grant into settings.
- It launches the survey and code_to_spec workers with this Module's instructions.
- It collects their [worker results](../../glossary.json#concept.worker-result).
- It audits the worktree.
- It writes the run records.

Any change beyond the grant fails the run.

<a id="uses-checks"></a>

**Check execution** defines the configured check entries of the checks files, one
`.concorde/checks/<module id>.json` per Module. A survey proposes checks in that shape, each with the
`module` it is for. The developer can put each check they accept into that Module's checks file
without its `module` and otherwise unchanged. Adoption itself never runs or configures a check.

<a id="uses-spec"></a>

Always on the workspace, **Spec core** performs these actions:

- It computes the `code-to-spec` [grant](../../glossary.json#concept.grant).
- It lists a Module's bound files.
- It runs the [structural checks](../../glossary.json#concept.structural-check).
- It regenerates the [registry](../../glossary.json#concept.registry) mirror.

Adoption relies on its checks as the definition of a valid Spec. Adoption adds none of its own.
When a Spec cannot be loaded, the run ends `failed`.

<a id="uses-workflows"></a>

**Workflows** defines the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output), the
`workflow` object of a run's output. As [Decisions and open
questions](#decisions-and-open-questions) says, every `ok` survey and code_to_spec run declares
these items in that object:

- Its [decision points](../../glossary.json#concept.decision-point).
- Its decisions.
- Its deviations.
- For a survey, its proposed checks as notes.

Adoption builds that object with Workflows' `step_output` helper. The helper checks it against the
convention. Adoption knows no workflow. Which items are decision points is Adoption's rule. What a
workflow does with them is the workflow's rule.
