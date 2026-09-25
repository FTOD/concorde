# Adoption requirements

The Module-wide obligations of [Adoption](module.md). The shapes are in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete situations.

## Reading and writing

### req.adoption.task-type — Adoption workers run under code-to-spec

The survey and code_to_spec hosts SHALL compute their workers' grants for task type `code-to-spec` from the Specs of the worktree the run works on.

### req.adoption.survey-read-only — A survey writes nothing

The survey host SHALL give its worker no writable path and end the run `failed` when the audit finds any change.

The survey withholds the Spec side of the `code-to-spec` grant, which the Protocol permits, so the
survey may also run without a task.

### req.adoption.no-code-change — Adoption never changes code

No Adoption Operation SHALL create, change or delete a file of the task worktree other than Spec documents and the project registry.

### req.adoption.no-bash — Adoption workers cannot run code

The survey and code_to_spec workers SHALL NOT be given a tool that runs commands.

What the code does is established by reading it. Running it would make the description depend on
the environment of one run and would let a worker change files through a command.

### req.adoption.modules-by-host — Only the scaffold adds Modules

A survey or code_to_spec worker SHALL NOT be able to add or remove a Module; only the scaffold host does, from an admitted survey.

## Honest description

### req.adoption.open-questions — Doubtful intent is never a promise

A code_to_spec worker SHALL report every behaviour whose intent the code does not settle as an open question instead of writing it as a requirement, scenario or contract.

The Spec may name such a behaviour as an honest unknown so that a reader is warned; it states no
promise about it until an answer does.

### req.adoption.decisions-listed — Every open choice is listed

A survey or code_to_spec worker SHALL list every choice it took between options the code left open as a decision with its options, choice and reason.

### req.adoption.answers-followed — Answers are followed

A survey or code_to_spec run given `--answers` SHALL end `failed` when its output does not follow every answer: a decision answer as a decision `decided_by` developer with the answered choice, a question answer in a survey by no longer listing the question, and in a code_to_spec run as a promise with source `answer` or as a deviation.

### req.adoption.deviation-reported — Intent that the code misses is reported

A code_to_spec run SHALL report as a deviation every answer whose stated intent differs from the behaviour the worker observed in the code.

## Survey

### req.adoption.proposal-checked — A proposal fits the worktree

The survey host SHALL end the run `failed` with every inconsistency listed when the proposal names a child identity or title that is already registered or repeated, two children whose documents would share a folder, an entry that the surveyed Module's realizations do not cover or that does not exist, a `uses` target that is neither another child nor a registered Module, or a check for a Module that is neither the surveyed Module nor a child.

### req.adoption.inventory — The survey worker gets an inventory

The survey host SHALL give its worker, as task material, every file the surveyed Module binds with its size in lines.

### req.adoption.one-module-surveyed — One Module per survey

A survey SHALL be bound to exactly one Module.

## Scaffold

### req.adoption.scaffold-input — The scaffold applies one survey of its task

The scaffold host SHALL apply exactly one proposal, from an `ok` survey run admitted with `--input`, refusing no input, several inputs or an input that is not a survey with `invalid_request`.

A run of another task never reaches the scaffold: the host refuses it before the run begins with
`input_not_admissible`, as for every Operation.

### req.adoption.checks-proposed-only — Proposed checks are never configured

The scaffold host SHALL NOT change the project configuration.

A proposed check is a command a model chose after reading code; the developer configures the ones
they accept.

### req.adoption.scaffold-rechecked — The proposal is checked again before writing

The scaffold host SHALL check the proposal against the task worktree again before writing, ending the run `blocked` with `stale_proposal` and every mismatch listed when it no longer fits or a file it would create exists.

### req.adoption.scaffold-atomic — A scaffold is kept whole or not at all

The scaffold host SHALL write all its changes in one file transaction that is kept only when it adds no structural error.

### req.adoption.parent-narrowed — A child's paths leave the parent

After a scaffold, the parent's realizations SHALL bind no path that a created child binds.

A parent directory entry that contains a child's entry is replaced by the entries below it that no
child took, a directory staying one entry when no child took anything inside it.

### req.adoption.stub-honest — A scaffolded entry states what is unknown

Every entry the scaffold creates SHALL state the survey's purpose and say in its Usage, Design and Relationships sections that the Module's behaviour and design are not yet specified.

## Code to spec

### req.adoption.stubs-prepared — Implementation documents are prepared and tidied

The code_to_spec host SHALL create the `requirements.md`, `scenarios.md` and `contracts.md` stubs that a bound Module lacks before freezing the grant and remove every stub the worker left unchanged before the run ends, whichever step stops it.

### req.adoption.answers-first — Answers are checked before anything happens

The survey and code_to_spec hosts SHALL end a run whose answers file is unreadable or breaks its contract `failed` with `invalid_answers` before writing a file or launching a worker.

### req.adoption.no-resume-on-spec — A Spec error stops the run

The code_to_spec host SHALL end the run `blocked` with every new structural error as a cause, without a resume round, when the change adds a structural error.

### req.adoption.mirror-reconciled — The registry mirror follows the entries

The code_to_spec host SHALL regenerate the registry's mirrored fields of existing Modules after the worker's change, without adding or removing a Module record.
