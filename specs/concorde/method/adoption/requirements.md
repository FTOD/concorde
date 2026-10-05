# Adoption requirements

The Module-wide obligations of [Adoption](module.md). The shapes are in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete
situations.

## Reading and writing

### req.adoption.task-type — Adoption workers run under code-to-spec

The survey and code_to_spec hosts SHALL compute their workers' grants for
[task type](../../glossary.json#concept.task-type) `code-to-spec` from the Specs of the worktree the
run works on.

### req.adoption.survey-read-only — A survey writes nothing

The survey host SHALL give its worker no writable path.

The survey withholds every writable level of the `code-to-spec` grant, which the Protocol permits.
It reads the code and the [Specs](../../glossary.json#concept.spec) its grant names and writes
nothing. It may therefore also run unbound.

### req.adoption.survey-change-fails — A change during a survey fails it

When the audit finds any change, the survey host SHALL end the run `failed`.

### req.adoption.no-code-change — Adoption never changes code

No Adoption [Operation](../../glossary.json#concept.operation) SHALL create, change or delete a file
of the workspace other than these:

- Spec documents.
- The glossary entries of the Modules a code_to_spec run describes.
- The project registry.
- The `verifies` decorators and helper that code_to_spec's host adds to existing test files.

### req.adoption.self-repair — The worker repairs the Specs it breaks

The code_to_spec host SHALL resume its worker at most twice with every structural error that its
validation finds after a round and that meets either condition:

- The error is in the documents the run describes.
- The error is new since the baseline.

### req.adoption.own-errors-briefed — The worker is told the errors it must repair

The code_to_spec host SHALL list, in its worker's brief, every structural error already in the
documents of the Modules it describes.

### req.adoption.tests-linked-by-host — The host alone marks tests

The code_to_spec host SHALL add a `verifies` decorator to each existing Python test under these
conditions and exceptions:

- The test meets both conditions:
  - The test is in a Module's implementation file.
  - A scenario promise of a described Module names the test in its `tests`.
- None of these exceptions applies:
  - The file defines that test more than once.
  - The decorated file would not parse or cannot be written.
  - At module level, the file already binds the name `verifies` to something other than either of
    these:
    - The host's no-op helper.
    - An import of Concorde's `verifies` decorator from `concorde.spec.verification`.
  - While the file binds the name, no such helper or import stands at the file's top level before
    the test.

As the coverage check finds it, a test is found in the module or a class body, but never inside a
function. This includes tests under a control-flow statement such as a top-level `if` or `try`.
A decorator in a file with a binding of its own would call the project's own `verifies`, whatever
it does. When the helper or import follows a test, a decorator above that test could find no
`verifies` when the module is imported. The same risk applies when only a branch binds the name.
In these cases, the host therefore leaves the file untouched and reports the link in
`unlinked_tests`.
A module-level binding is any of these that binds the name outside a function or class body:

- A statement.
- An `except` clause.
- An assignment expression.
- A match pattern.

A test that already declares the scenario gets no second decorator. A link named more than once
gets one.

### req.adoption.test-edits-limited — Test files get decorators and one helper only

The code_to_spec host SHALL change an existing test file only by adding `verifies` decorators and,
once in a file that does not already bind the name `verifies` at its top level, a two-line no-op
definition of `verifies` with at most the blank lines that make two on each side of it, keeping
every byte already in the file, its line endings included.

Each line it adds ends as the file's lines end. A decorator takes the indentation of the line it is
added above. Both hold so that linking a test changes only the lines it adds.

### req.adoption.unlinked-reported — Links not made are reported

The code_to_spec host SHALL list in the result's `unlinked_tests` every test a scenario promise
names that it did not link, with the reason.

A test file that cannot be written is one such reason. The host replaces a file only through a new
file beside it, so the original stays whole. It goes on to link the next file.

### req.adoption.no-bash — Adoption workers cannot run code

The survey and code_to_spec workers SHALL NOT be given a tool that runs commands.

Reading the code establishes what it does. Running it would make the description depend on the
environment of one run. It would also let a worker change files through a command.

### req.adoption.modules-by-host — Only the scaffold adds Modules

A survey or code_to_spec worker SHALL NOT be able to add or remove a
[Module](../../glossary.json#concept.module), which only the `scaffold`
[execution command](../../glossary.json#concept.execution-command) of
[Scaffold](../scaffold/module.md) does, from an admitted survey.

### req.adoption.relative-paths — A path inside the worktree is made project-relative

When a path of these worker claims begins with the worktree's absolute path, or its real path,
followed by `/`, the survey and code_to_spec hosts SHALL write it relative to the worktree before
checking it:

- A survey's child entries, external paths, check inputs and open questions' evidence.
- A code_to_spec run's promise `tests` and open questions' evidence.

A worker's tools take absolute paths, and such a path names exactly one project path. Any other
path is left as the worker wrote it. The checks report it. When an open question's evidence is
still absolute, it fails these runs, with a line suffix such as `:12` allowed:

- A survey with `inconsistent_proposal`.
- A code_to_spec run with `inconsistent_description`.

## Honest description

### req.adoption.open-questions — Doubtful intent is never a promise

A code_to_spec worker SHALL report every behaviour whose intent the code does not settle as an
[open question](../../glossary.json#concept.open-question) instead of writing it as a requirement,
scenario or contract.

The Spec may name such a behaviour as an honest unknown so that a reader is warned. Until an answer
states a promise about it, the Spec states none.

### req.adoption.decisions-listed — Every open choice is listed

A survey or code_to_spec worker SHALL list every choice it took between options the code left open
as a decision with its options, choice and reason.

### req.adoption.answers-followed — Answers are followed

When its output does not follow every answer in the forms below, a survey or code_to_spec run
given `--answers` SHALL end `failed`:

- A decision answer as a decision with that identity.
- A question answer in a survey by no longer listing the question.
- A question answer in a code_to_spec run as a promise with source `answer` naming the question.

The host records an answered decision's choice itself, by
[req.adoption.decisions-by-host](#req.adoption.decisions-by-host), so the worker only has to list it.

A deviation never replaces that promise. When the code does otherwise, the run lists the promise
and, by [req.adoption.deviation-reported](#req.adoption.deviation-reported), a deviation as well.
The Spec states the intent. The deviation tells later `implement` work that the code does not
follow it yet.

### req.adoption.decisions-by-host — The host writes the chosen option

The survey and code_to_spec hosts SHALL record each decision of their output with the texts of
the options the worker listed and these fields:

- For a decision no answer settles, `chosen` is the text of the option whose identity the worker
  named, with `decided_by` `worker`.
- For a decision an answer settles, `chosen` is the answer, with `decided_by` the answer's
  `answered_by`.

The worker never copies an option's text, so a paraphrase cannot make its choice fall outside its
options.

### req.adoption.unchosen-decision-fails — A decision without a valid choice fails the run

The survey and code_to_spec hosts SHALL end the run `failed`, listing each such decision, when
either condition holds:

- The worker names for a decision an identity none of its options has.
- The worker names none for a decision no answer settles.

### req.adoption.deviation-reported — Intent that the code misses is reported

A code_to_spec run SHALL report as a deviation every answered
[open question](../../glossary.json#concept.open-question) whose stated intent differs from the
behaviour the worker observed in the code.

A decision answer chooses among options the code leaves open, so it has no observed behaviour to
deviate from.

### req.adoption.step-output — Decision points are declared in the step output

Every `ok` survey and code_to_spec run SHALL list these under the
[step output convention](../../workflows/contracts.md#contract.workflows.step-output) of its output:

- As [decision points](../../glossary.json#concept.decision-point), every open question and, for a
  survey, every decision its worker took itself.
- As decisions, every decision it reports. A decision point of kind `decision` keeps the identity
  of its decision.
- As deviations, every deviation.
- For a survey, as a note, every proposed check.

A decision that follows an answer is no decision point, since it is already settled. The lists
repeat what the Spec description or
[decomposition proposal](../../glossary.json#concept.decomposition-proposal) holds, in the shape any
workflow reads, so that a workflow stops for exactly these points without knowing Adoption's
contracts.

## Survey

### req.adoption.proposal-checked — A proposal fits the worktree

The survey host SHALL end the run `failed` with every inconsistency listed when the proposal
names any of these:

- A child identity or title that is already registered or repeated.
- Two children whose documents would share a folder.
- An entry that the surveyed Module's realizations do not cover.
- An entry that lies in a directory their exclusion rule skips.
- An entry that is reached through a symbolic link.
- An entry that does not exist.
- A `uses` target that is neither another child nor a registered Module.
- A check for a Module that is neither the surveyed Module nor a child.
- A check that is already configured or proposed twice.
- A check input that is not a canonical project-relative path.
- An external that is not a path the surveyed Module binds.
- An external that is a child's entry or a directory containing one.
- An external that takes Concorde installation files.
- An external that is proposed twice.
- An external that is used by neither the surveyed Module nor a child.
- A decision or open question identity used twice.
- An open question's evidence that is an absolute path.

### req.adoption.inventory — The survey worker gets an inventory

The survey host SHALL give its worker, as task material, every file the surveyed Module binds with
its size in lines, apart from that Module's Concorde installation.

The inventory is a file of the run's [trace node](../../glossary.json#concept.trace-node) that the
worker may read beside its grant. The brief names it with a summary, so that no number of files
makes the brief too long and none is left out.

### req.adoption.installation-stays — Concorde's own files stay where they are

When a child entry covers a file of the surveyed Module's Concorde installation realization, the
survey host SHALL end the run `failed` with `inconsistent_proposal`.

The skill, workflows and agents Concorde installed configure the agents, not the project. The
installer replaces them on every update.

### req.adoption.survey-after-scaffold — A scaffold's writes need a fresh workspace

Before launching a worker, the survey host SHALL end a bound survey `failed` with
`fresh_workspace_required` when both conditions hold:

- The surveyed Module's entry metadata names a contained Module or an external inclusion.
- The same metadata at the workspace's base commit does not name that contained Module or
  external inclusion.

These are the additions a scaffold makes to the Module it applies a proposal to. The workspace
therefore already holds a scaffold's writes. The Module is narrowed and its children are
registered. A survey replayed there would propose against them, while nothing undoes them.
After its scaffold runs, revising a survey requires a fresh workspace. In that workspace, the
survey runs again with the answers that revise it. The survey undoes nothing in the first
workspace. An unbound survey has no workspace a scaffold could have written to.

### req.adoption.one-module-surveyed — One Module per survey

A survey SHALL be bound to exactly one Module.

## Code to spec

### req.adoption.stubs-prepared — Implementation documents are prepared

Before freezing the grant, the code_to_spec host SHALL create the `requirements.md`, `scenarios.md`
and `contracts.md` stubs that a bound Module lacks.

### req.adoption.stubs-removed — Unused stubs are removed on every way out

Before the run ends, whichever step stops it, the code_to_spec host SHALL remove every prepared
stub the worker left unchanged or had deleted, with its place among the Module's documents.

### req.adoption.answers-first — Answers are checked before anything happens

The survey and code_to_spec hosts SHALL end a run `failed` with `invalid_answers` before writing
a file or launching a worker when either condition holds:

- The run's answers file is unreadable.
- The run's answers file breaks its contract.

### req.adoption.own-errors-count — Errors in the described documents always count

The code_to_spec host SHALL count every structural error located in a document a described Module
owns as introduced by the run, whether or not the baseline had it.

The worker rewrites those documents. A retry after a failed attempt would otherwise take that
attempt's errors as the project's and let the same errors pass.

### req.adoption.errors-left-block — Errors left after the last round stop the run

When structural errors it counts as introduced remain after its worker's last round, the
code_to_spec host SHALL end the run `blocked`, with every such error as a cause.

The [resume rounds](../../glossary.json#concept.resume-round) of
[req.adoption.self-repair](#req.adoption.self-repair) come first, so only errors the worker did not
repair stop the run.

### req.adoption.mirror-reconciled — The registry mirror follows the entries

After the worker's change, the code_to_spec host SHALL regenerate the registry's mirrored fields
of existing Modules, without adding or removing a Module record.
