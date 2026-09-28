# Adoption requirements

The Module-wide obligations of [Adoption](module.md). The shapes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Reading and writing

### req.adoption.task-type — Adoption workers run under code-to-spec

The survey and code_to_spec hosts SHALL compute their workers' grants for [task type](../../../glossary.json#concept.task-type) `code-to-spec` from the Specs of the worktree the run works on.

### req.adoption.survey-read-only — A survey writes nothing

The survey host SHALL give its worker no writable path.

The survey withholds the [Spec](../../../glossary.json#concept.spec) side of the `code-to-spec`
grant, which the Protocol permits, so the survey may also run unbound.

### req.adoption.survey-change-fails — A change during a survey fails it

The survey host SHALL end the run `failed` when the audit finds any change.

### req.adoption.no-code-change — Adoption never changes code

No Adoption [Operation](../../../glossary.json#concept.operation) SHALL create, change or delete a file of the workspace other than Spec documents, the glossary entries of the Modules a code_to_spec run describes, the project registry and the `verifies` decorators and helper that code_to_spec's host adds to existing test files.

### req.adoption.self-repair — The worker repairs the Specs it breaks

The code_to_spec host SHALL resume its worker, at most twice, with every structural error its validation finds after a round in the documents the run describes or new since the baseline.

### req.adoption.own-errors-briefed — The worker is told the errors it must repair

The code_to_spec host SHALL list, in its worker's brief, every structural error already in the documents of the Modules it describes.

### req.adoption.tests-linked-by-host — The host alone marks tests

The code_to_spec host SHALL add a `verifies` decorator to each existing Python test in a Module's implementation file that a scenario promise of a described Module names in its `tests`, unless the decorated file would not parse.

A test that already declares the scenario gets no second decorator.

### req.adoption.test-edits-limited — Test files get decorators and one helper only

The code_to_spec host SHALL change an existing test file only by adding `verifies` decorators and, once in a file that does not already bind the name `verifies` at its top level, a two-line no-op definition of `verifies`.

### req.adoption.unlinked-reported — Links not made are reported

The code_to_spec host SHALL list in the result's `unlinked_tests` every test a scenario promise names that it did not link, with the reason.

### req.adoption.no-bash — Adoption workers cannot run code

The survey and code_to_spec workers SHALL NOT be given a tool that runs commands.

What the code does is established by reading it. Running it would make the description depend on
the environment of one run and would let a worker change files through a command.

### req.adoption.modules-by-host — Only the scaffold adds Modules

A survey or code_to_spec worker SHALL NOT be able to add or remove a [Module](../../../glossary.json#concept.module); only the `scaffold` [execution command](../../../glossary.json#concept.execution-command) of [Scaffold](../../commands/scaffold/module.md) does, from an admitted survey.

## Honest description

### req.adoption.open-questions — Doubtful intent is never a promise

A code_to_spec worker SHALL report every behaviour whose intent the code does not settle as an [open question](../../../glossary.json#concept.open-question) instead of writing it as a requirement, scenario or contract.

The Spec may name such a behaviour as an honest unknown so that a reader is warned; it states no
promise about it until an answer does.

### req.adoption.decisions-listed — Every open choice is listed

A survey or code_to_spec worker SHALL list every choice it took between options the code left open as a decision with its options, choice and reason.

### req.adoption.answers-followed — Answers are followed

A survey or code_to_spec run given `--answers` SHALL end `failed` when its output does not follow every answer: a decision answer as a decision `decided_by` developer with the answered choice, a question answer in a survey by no longer listing the question, and in a code_to_spec run as a promise with source `answer` naming the question.

A deviation never replaces that promise. When the code does otherwise, the run lists the promise
and, by [req.adoption.deviation-reported](#req.adoption.deviation-reported), a deviation as well:
the Spec states the intent, and the deviation tells later `implement` work that the code does not
follow it yet.

### req.adoption.deviation-reported — Intent that the code misses is reported

A code_to_spec run SHALL report as a deviation every answered [open question](../../../glossary.json#concept.open-question) whose stated intent differs from the behaviour the worker observed in the code.

A decision answer chooses among options the code leaves open, so it has no observed behaviour to
deviate from.

## Survey

### req.adoption.proposal-checked — A proposal fits the worktree

The survey host SHALL end the run `failed` with every inconsistency listed when the proposal names a child identity or title that is already registered or repeated, two children whose documents would share a folder, an entry that the surveyed Module's realizations do not cover or that does not exist, a `uses` target that is neither another child nor a registered Module, a check for a Module that is neither the surveyed Module nor a child, a check that is already configured or proposed twice, a check input that is not a canonical project-relative path, an external that is not a path the surveyed Module binds, is a child's entry or a directory containing one, takes Concorde installation files, is proposed twice or is used by neither the surveyed Module nor a child, a worker decision whose choice is none of its options, or a decision or open question identity used twice.

### req.adoption.inventory — The survey worker gets an inventory

The survey host SHALL give its worker, as task material, every file the surveyed Module binds with its size in lines, apart from its Concorde installation.

### req.adoption.installation-stays — Concorde's own files stay where they are

The survey host SHALL end the run `failed` with `inconsistent_proposal` when a child entry covers a file of the surveyed Module's Concorde installation realization.

The skill, workflows and agents Concorde installed configure the agents, not the project, and the
installer replaces them on every update.

### req.adoption.one-module-surveyed — One Module per survey

A survey SHALL be bound to exactly one Module.

## Code to spec

### req.adoption.stubs-prepared — Implementation documents are prepared

The code_to_spec host SHALL create the `requirements.md`, `scenarios.md` and `contracts.md` stubs that a bound Module lacks before freezing the grant.

### req.adoption.stubs-removed — Unused stubs are removed on every way out

The code_to_spec host SHALL remove every prepared stub the worker left unchanged or had deleted, with its place among the Module's documents, before the run ends, whichever step stops it.

### req.adoption.answers-first — Answers are checked before anything happens

The survey and code_to_spec hosts SHALL end a run whose answers file is unreadable or breaks its contract `failed` with `invalid_answers` before writing a file or launching a worker.

### req.adoption.own-errors-count — Errors in the described documents always count

The code_to_spec host SHALL count every structural error located in a document a described Module owns as introduced by the run, whether or not the baseline had it.

The worker rewrites those documents. A retry after a failed attempt would otherwise take that
attempt's errors as the project's and let the same errors pass.

### req.adoption.errors-left-block — Errors left after the last round stop the run

The code_to_spec host SHALL end the run `blocked`, with every structural error it counts as introduced as a cause, when such errors remain after its worker's last round.

The [resume rounds](../../../glossary.json#concept.resume-round) of
[req.adoption.self-repair](#req.adoption.self-repair) come first, so only errors the worker did not
repair stop the run.

### req.adoption.mirror-reconciled — The registry mirror follows the entries

The code_to_spec host SHALL regenerate the registry's mirrored fields of existing Modules after the worker's change, without adding or removing a Module record.
