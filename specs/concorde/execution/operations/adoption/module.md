# Adoption

## Purpose

Adoption describes a project whose code came before its Specs. It provides two Operations: `survey`
has a worker read a [Module](../../../glossary.json#concept.module)'s code and propose how to split
it into child Modules, and `code_to_spec` has a worker read a Module's code and write that Module's
[Spec](../../../glossary.json#concept.spec). Between them the
[execution command](../../../glossary.json#concept.execution-command) `scaffold` of
[Scaffold](../../commands/scaffold/module.md) creates the proposed child Modules. The three are the
only runs that turn code into Specs, and they exist for the uncommon project adopted after its code
was written; a project specified first never needs them. Adoption never changes what code does,
records behaviour as it is instead of improving it, and never writes a behaviour whose intent the
code does not settle as a promise: such behaviour becomes an
[open question](../../../glossary.json#concept.open-question) for the developer. The one edit it
makes outside Specs marks the project's existing tests with the scenarios taken from them.

## Core concepts

### Decomposition proposal

<a id="concept.decomposition-proposal"></a>

A survey worker reads the code of one Module, usually the root, and returns a **decomposition
proposal** ([contract](contracts.md#contract.adoption.decomposition)): for each child Module to
create, its identity, title, a one-paragraph purpose, the paths it should bind and the Modules it
uses with the reason; the third-party code the project vendors, such as a bundled copy of a
library, each with the Module that uses it; the test and lint commands it found, proposed in the
shape of [configured checks](../../../glossary.json#concept.configured-check) of the Modules they
check; the decisions it took; and its open questions. The host adds the realization entries, the
bound paths, that stay with the surveyed Module. A proposal with no children is valid: the Module is
small enough to describe as it is.

### Spec description

A `code_to_spec` worker rewrites the bound Modules' own documents from their code, and the result's
output is a **Spec description** ([contract](contracts.md#contract.adoption.spec-description)).

### Decisions and open questions

<a id="concept.open-question"></a>

Workers of both Operations meet two kinds of uncertainty and report each separately instead of
hiding it in prose:

- A **decision** is a choice the code leaves open, such as whether two directories are one Module
  or two, or which name a concept gets. The worker takes it, with its options and reason, and goes
  on.
- An **open question** is about intent: the code does something, such as swallowing an error or
  treating one input specially, and nothing shows whether it is meant. The worker writes no promise
  about it. The Spec states it as an honest unknown, and the result reports what was observed, why
  it is uncertain, the options and a recommendation.

Neither Operation asks the developer: they have no one to ask. What happens next is the task
level's or the workflow's choice: go on with the worker's decisions, or seek answers through the
existing escalation path, which settles each in the main agent when its authority covers it and
otherwise with the developer.

### Answers and deviations

The answers reach a later run as an **answers** file
([contract](contracts.md#contract.adoption.answers)) with `--answers`, each naming the decision or
question it answers, the question's text, the answer and who settled it, the main agent or the
developer; a decision that follows an answer is recorded as decided by that one, so the record
never credits the developer with a choice the main agent made. `--input` admits the run that asked,
so the worker sees the earlier proposal or description. An answers file lists every answer given
so far for that step, not only the latest. A survey rerun follows every answered decision and no longer lists
an answered open question. A code_to_spec rerun writes an answered question as the promise the
answer states. When that intent differs from what the code does, the Spec states the intent, and
the result lists a **deviation** with the intended and the observed behaviour, for later
`implement` work: the Spec is again ahead of the code, as Concorde expects.

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

Adoption starts where initialization leaves a project: a root Module whose realization binds every
existing file and whose entry says nothing is specified yet. The
[main agent](../../../glossary.json#concept.main-agent) opens a task bound to that Module. The main
agent or a [task session](../../../glossary.json#concept.task-session) then runs the three steps in
order in its task worktree, directly or through the
[brownfield workflow](../../workflows/module.md):

```text
concorde run survey --modules <module-id> [--answers <file>] [--input <run-id>]…
concorde scaffold --input <survey-run-id>
concorde run code_to_spec --modules <module-id>[,<module-id>…] [--answers <file>] [--input <run-id>]…
```

Each works on the [workspace](../../../glossary.json#concept.workspace) of the worktree it starts
in, whose binding names it, and each is recorded in the
[run store](../../../glossary.json#concept.run-store) like any run, so that the scaffold can admit
the survey and a later survey or code_to_spec the run whose questions it answers.

**Survey.** A survey writes nothing, so it may also run
[unbound](../../../glossary.json#concept.unbound-run), in the primary worktree, to show the
developer a proposal before any task exists. The host gives the worker, as task material, an
inventory of every file the surveyed Module binds with its size in lines, so the worker can plan
what to read in a large codebase instead of opening everything. The files of the surveyed Module's
Concorde installation realization, the skill, workflows and agents the installer placed, are left
out of it and stay with the surveyed Module: a proposal that gives one of them to a child fails,
since they configure the agents, not the project, and the installer replaces them on every update.

**Scaffold.** The execution command `concorde scaffold` of
[Scaffold](../../commands/scaffold/module.md), with no worker, applies exactly one proposal admitted
with `--input` from an `ok` survey of the same workspace: it creates each proposed child as a stub
Module that states the survey's purpose and says honestly that nothing else is specified yet,
narrows the parent's realizations, makes vendored code an external inclusion of its user, and
returns a scaffold record. Adding Modules is a
project-level step no worker's write set includes, which is why deterministic code makes it and not
a worker, and why it is not an [Operation](../../../glossary.json#concept.operation) of this Module.

**Code to spec.** A worker of [task
type](../../../glossary.json#concept.task-type) `code-to-spec` reads the bound Modules' code and
their Specs and rewrites their own documents: each entry document (`module.md`), in the reading
order the Protocol recommends, the glossary entries of the words they own, and requirements, scenarios and contracts
in implementation documents. The host prepares the implementation documents the worker may need,
`requirements.md`, `scenarios.md` and `contracts.md`, as owned stubs before the grant is frozen, and
removes again every stub the worker left unchanged or deleted, however the run ends. The answers are
checked before anything is written. Describing the root after its children are scaffolded describes
how the children compose and the files that stayed with it.

**Statuses.** Status follows the other worker-backed Operations. A survey or code_to_spec run is
`ok` when the worker completed its proposal or description, whatever decisions and open questions it
lists. It is `blocked` when the worker could not do the work at all or when a code_to_spec change
adds a structural error; the [error chain](../../../glossary.json#concept.error-chain) then names
each finding as a cause. It is `failed` when the request or the answers are invalid, the host could
not run the worker, the audit found a write outside the grant, or the output is inconsistent, with
every inconsistency listed in the Operation's own link. Every code is in the
[error table](contracts.md#errors).

## Why it is built this way

The two Operations and the scaffold between them keep the Protocol's separation of reading, deciding
and writing. The survey worker reads code but writes nothing; deciding which Modules exist is then a
deterministic step, Scaffold's, that anyone can check against the proposal; describing a Module is a
worker bounded by that Module's own documents. A worker never adds or removes Modules, because the
registry is outside every Module's write set.

The `code-to-spec` task type is what makes this legal: it reads the bound Modules'
ImplementationScope and writes their SpecScope, which no other task type combines. The survey runs
under the same task type with the Spec side withheld, as the Protocol lets a harness give less than
a type assigns, so it can read code and write nothing. As for `specify`, the code_to_spec brief
states the rules for writing Spec documents and ends with the project's copy of Spec writing
guidelines, since no grant shows the [Protocol copy](../../../glossary.json#concept.protocol-copy).
That guide includes the overview, Required format, Writing guidance and templates: both
machine-checkable structure and syntax and content requiring reader and editor judgment. Structural
validation does not establish semantic sufficiency. Both workers get only Read, Glob and Grep, and
the code_to_spec worker also Edit and Write; neither gets Bash, so neither can run the code it
describes. What the code does is taken from reading it.

The survey and code_to_spec results hold decisions and open questions as structured lists, not
prose, because a workflow must count them to decide whether to stop in interactive mode, and must
copy them unchanged into its report in no-ask mode.

The code_to_spec host writes Specs itself before its worker runs, when it prepares the stubs. So it
checks the answers first, and removes every stub left unchanged on every way out of the run, a
failed grant or a stopped worker included: a run that ends early leaves behind only what its worker
changed.

## How it is built

```d2
adoption: Adoption {
  survey: Survey Operation {
    "src/concorde/adoption/survey.py"
    "prompts/workers/survey.md"
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
  codetospec -> shared: validates answers with
}
```

<a id="realization.adoption.survey"></a>

The **Survey Operation** realization declares the `SURVEY` provider and its step table:

| # | Step | Actor | Stops the run when |
| --- | --- | --- | --- |
| 1 | Check the answers; compute the inventory of the surveyed Module's bound files | host, Spec core | invalid answers (`failed`, `invalid_answers`); not exactly one Module (`failed`, `invalid_request`); Specs cannot load (`failed`, `specs_unloadable`) |
| 2 | Compute and freeze the `code-to-spec` grant with every writable level withheld | Operation, Spec core | the grant cannot be computed (`failed`, `grant_unavailable`) |
| 3 | Generate settings, tools and the brief with inventory, answers and inputs | Workers | — |
| 4 | Launch the worker and wait for its result | Workers, worker | launch error or timeout (`failed`); worker `blocked` or `failed` (passed on) |
| 5 | Audit: nothing is writable, so any change is a violation | Workers | any change (`failed`) |
| 6 | Check the proposal against the worktree and the answers; add the remaining entries | host | an inconsistency or an answer not followed (`failed`, `inconsistent_proposal`) |
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
| 6 | Audit and write the [run record](../../../glossary.json#concept.run-record) | Workers | a write outside the grant (`failed`, after step 7) |
| 7 | Remove the stubs left unchanged or deleted through the worker's proposed deletions from their Modules' documents, whatever steps 3 to 6 found; reconcile the registry mirror | host, Spec core | — |
| 8 | Validate again and compare with the baseline | host, Spec core | an error the run counts as its own, left after the last round (`blocked`, `new_structural_errors`) |
| 9 | Check the description against the answers and the bound Modules | host | an inconsistency or an answer not followed (`failed`, `inconsistent_description`) |
| 10 | Link the existing tests each scenario was taken from | host | — (a link it cannot make is reported in `unlinked_tests`) |
| 11 | Return the run result | host | — |

A scenario the worker took from existing tests names them in its promise's `tests`, as
`path::name` or `path::Class::name`. The worker never edits a test: step 10, the host, adds a
`verifies` decorator above each named test that exists in a Module's implementation file, and
once per file a two-line no-op definition of `verifies` after the file's docstring and imports,
so that the project's tests stay free of any import of Concorde and run the same in the project's
own environment, while the coverage check sees which test verifies which scenario. It adds
nothing else, adds nothing twice, and leaves a file untouched when the decorated file would not
parse. A file that already binds `verifies` at module level keeps that binding: the host adds only
decorators when the binding is its own no-op helper, however formatted, or an import of Concorde's
decorator from `concorde.spec.verification`, and otherwise leaves the file untouched and reports
each of its links in `unlinked_tests`, because a decorator would call the project's own `verifies`,
whatever it does. Only Python tests are linked.

Unlike `specify`, every structural error in a described Module's own documents counts as the
run's, even one the baseline already had: the worker rewrites those documents, and a retry must not
inherit a failed attempt's errors as the project's. As with `specify`, the host validates after each
round and resumes the worker, at most twice, with the errors the run is judged by, so the worker
repairs what it broke itself; only errors left after the last round stop the run as `blocked`, and
the task level or the workflow goes on.

<a id="realization.adoption.shared"></a>

The **Adoption shared records** realization holds the schemas of the
[decomposition proposal](../../../glossary.json#concept.decomposition-proposal), the answers and the
decision and open-question records, and the checks of a proposal against a worktree, which the
survey applies and [Scaffold](../../commands/scaffold/module.md) applies again before writing.

<a id="realization.adoption.tests"></a>

Adoption is tried on real codebases with real workers by
[End-to-end testing](../../../e2e/module.md), on projects from SWE-bench.

The **Adoption tests**, under `tests/concorde/adoption/` with the existing-codebase fixture
`tests/concorde/support/brownfield_project.py` and the adoption test case
`tests/concorde/support/adoption_case.py` they share with Workflows and Scaffold, run the survey and
code_to_spec, after a scaffold, in a bound task worktree of a small existing codebase with a fake
worker, verifying the [requirements](requirements.md) and [scenarios](scenarios.md).

## What it relies on

<a id="uses-execution"></a>

**Execution**'s runner runs both: it reads the
[workspace binding](../../../glossary.json#concept.workspace-binding), holds the
[workspace lock](../../../glossary.json#concept.workspace-lock), admits `--input` runs only when
they ended `ok` in the same workspace (or, for an unbound survey, in none), and wraps each output in
the [run result](../../../glossary.json#concept.run-result). It refuses code_to_spec unbound, and
Adoption relies on it admitting only runs of the same workspace as inputs, so that a rerun sees only
that workspace's earlier proposal or description.

<a id="uses-operations"></a>

**Operations** lists `survey` and `code_to_spec` in its catalog and dispatches to this Module;
`survey` is the one Adoption Operation its catalog lets run unbound. Adoption never starts another
run: the order of the survey, the scaffold and code_to_spec, and whether to seek the developer's
answers between them through the existing escalation path, is decided by the task level or a
workflow.

<a id="uses-workers"></a>

**Workers** turns each frozen grant into settings, launches the survey and code_to_spec workers with
this Module's briefs, collects their [worker results](../../../glossary.json#concept.worker-result),
audits the worktree and writes the run records; any change beyond the grant fails the run.

<a id="uses-checks"></a>

**Check execution** defines the configured check entries of the checks files, one
`.concorde/checks/<module id>.json` per Module. A survey proposes checks in that shape, each with the
`module` it is for, so that the developer can put each one they accept into that Module's checks
file without its `module` and otherwise unchanged; Adoption itself never runs or configures a check.

<a id="uses-spec"></a>

**Spec core** computes the `code-to-spec` [grant](../../../glossary.json#concept.grant), lists a
Module's bound files, runs the [structural checks](../../../glossary.json#concept.structural-check),
and regenerates the [registry](../../../glossary.json#concept.registry) mirror, always on the
workspace. Adoption relies on its checks as the definition of a valid Spec and adds none of its own;
a Spec that cannot be loaded ends the run `failed`.
