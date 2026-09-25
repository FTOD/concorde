# Adoption scenarios

Concrete situations that show the [requirements](requirements.md) of [Adoption](module.md). The
shapes are in the [contracts](contracts.md).

## Survey

### scenario.adoption.survey-proposes — A survey proposes children

- GIVEN an initialized project whose root Module `module.shop` binds `src/`, `tests/`, `README.md` and `pyproject.toml`
- AND a task `adopt` bound to `module.shop`
- WHEN the main agent runs `concorde run survey --task adopt --modules module.shop`
- THEN the worker's grant reads the Specs and the code `module.shop` binds and writes nothing
- AND its brief lists every bound file with its size in lines
- AND the result is `ok` with a decomposition proposal naming `module.checkout` and `module.inventory` with their entries
- AND the proposal's remaining entries are the root's entries without the children's paths
- AND no file of the worktree changed

### scenario.adoption.installation-stays — Concorde's installed files stay with the root

- GIVEN a root Module whose Concorde installation realization binds `.claude/skills/concorde/SKILL.md`
- WHEN a survey runs for it
- THEN the inventory in its brief does not list the skill
- AND a proposal giving the skill to a child fails with `inconsistent_proposal` naming the Concorde installation

### scenario.adoption.survey-no-task — A survey before any task

- GIVEN an initialized project and no task
- WHEN the main agent runs `concorde run survey --modules module.shop` in the primary worktree
- THEN the result is `ok` with `task` null and a decomposition proposal
- AND no task record exists or changes

### scenario.adoption.survey-checks — Proposed checks take the configuration's form

- GIVEN a survey whose worker proposes a check with the inputs `src/checkout/` and `tests/` and the env `{"PYTHONPATH": "src"}`
- WHEN the survey ends
- THEN the proposed check's inputs are `src/checkout` and `tests`, as configured check inputs are written, and its env is kept
- AND the worker was asked to name the project's interpreter as `{python}` rather than an interpreter on `PATH`
- BUT a proposed input that is not a canonical project-relative path, such as `../elsewhere`, fails the survey with `inconsistent_proposal` naming it

### scenario.adoption.survey-inconsistent — A proposal that does not fit

- GIVEN a survey worker whose proposal gives a child the entry `lib/` that `module.shop` does not bind, and reuses the registered title `Shop`
- WHEN the host checks the proposal
- THEN the result is `failed`
- AND the Operation's link lists both inconsistencies with `capability` as its reason
- AND the worker's proposal stays in the result's `worker` field only

### scenario.adoption.survey-answers — A survey follows the developer's answers

- GIVEN an `ok` survey run whose decision `d.db-helper` chose to keep the database helper with the root
- AND an answers file answering `d.db-helper` with "a Module of its own"
- WHEN the main agent runs the survey again with `--answers` and `--input` naming the first run
- THEN the new proposal has a child for the database helper
- AND its decision `d.db-helper` is decided by the developer with that answer

## Scaffold

### scenario.adoption.scaffold-creates — A scaffold creates the proposed Modules

- GIVEN the task `adopt` with an `ok` survey proposing `module.checkout` bound to `src/checkout/` and `module.inventory` bound to `src/inventory/`, and a pytest check for checkout
- WHEN the main agent runs `concorde run scaffold --task adopt --input <survey run>`
- THEN `specs/shop/checkout/module.md` and `specs/shop/inventory/module.md` exist with their metadata, each stating its purpose and that its behaviour is not yet specified
- AND the root's entry contains both with an explaining paragraph each and its realization no longer binds `src/checkout/` or `src/inventory/`
- AND the root still binds every other file it bound under `src/`
- AND the registry has both records
- BUT the project configuration is unchanged, and the proposed check stays in the survey's proposal
- AND the worktree validates with no new error
- AND the result is `ok` with a scaffold record listing every file written

### scenario.adoption.scaffold-stale — A proposal overtaken by the worktree

- GIVEN a survey proposing `module.checkout` bound to `src/checkout/`
- AND `src/checkout/` was removed from the task worktree after the survey
- WHEN the main agent runs the scaffold with that survey as input
- THEN the result is `blocked` with `stale_proposal` naming the missing entry
- AND no file was written

### scenario.adoption.scaffold-refused-input — The scaffold needs one survey of its task

- GIVEN a task `adopt`
- WHEN the main agent runs the scaffold with no `--input`, with two, or with a run of the task that is not a survey
- THEN the result is `failed` with `invalid_request` naming what was given and what is needed
- AND no file was written
- BUT a survey of another task is refused before the run begins with `input_not_admissible`

## Code to spec

### scenario.adoption.describe-module — A Module's code becomes its Spec

- GIVEN the scaffolded Module `module.checkout` binding `src/checkout/`
- WHEN the main agent runs `concorde run code_to_spec --task adopt --modules module.checkout`
- THEN the worker's grant reads `src/checkout/` and writes only `module.checkout`'s documents
- AND the worker has no tool that runs commands
- AND the result is `ok` with a Spec description whose changed documents include the entry
- AND the stubs the worker did not fill are removed again
- AND no implementation file changed

### scenario.adoption.open-question — Doubtful behaviour becomes a question

- GIVEN checkout code that retries a declined payment but not a timed-out one, with nothing explaining the difference
- WHEN a code_to_spec worker describes `module.checkout`
- THEN the Spec states no requirement or scenario about retrying payments
- AND the result is `ok` with an open question naming the behaviour, the file, why it is uncertain and the options

### scenario.adoption.answered-deviation — An answer that the code does not follow

- GIVEN the open question about payment retries and an answer "retry both once"
- WHEN the main agent runs code_to_spec again with `--answers` and `--input` naming the earlier run
- THEN the Spec states that both declined and timed-out payments are retried once
- AND the result lists that promise with source `answer`
- AND the result lists a deviation with the intended and the observed behaviour

### scenario.adoption.stub-deleted — A stub the worker deleted leaves its Module

- GIVEN the scaffolded Module `module.checkout` and a code_to_spec run that prepared its `contracts.md` stub
- WHEN the worker describes the Module and proposes deleting `contracts.md` and its metadata instead of leaving the stub as it is
- THEN `module.checkout` no longer owns `contracts.md`, the result lists it among the removed stubs, and the run ends `ok` without a structural error

### scenario.adoption.describe-stubs-cleaned — A run that stops early leaves no stubs

- GIVEN a scaffolded Module `module.checkout` without implementation documents
- WHEN a code_to_spec run for it prepares the stubs and its worker then ends `failed` without writing
- THEN the result is `failed` with the worker's chain
- AND none of the prepared stubs remains, and `module.checkout` owns only its entry again

### scenario.adoption.invalid-answers — Answers that cannot be used

- GIVEN an answers file that is not valid JSON, or whose answer has no `id`
- WHEN a survey or code_to_spec run is given it with `--answers`
- THEN the result is `failed` with `invalid_answers` naming the file and what is wrong
- AND no worker ran and no file changed

### scenario.adoption.retry-counts-own-errors — A retry does not inherit a failed attempt's errors

- GIVEN a code_to_spec run for `module.checkout` that ended `blocked` because its scenario lacks a `THEN` step, the edit left in the worktree
- WHEN code_to_spec runs again for `module.checkout` and its worker leaves the scenario as it is
- THEN the run ends `blocked` with `new_structural_errors`, although the error was there before the run

### scenario.adoption.describe-invalid — A description that breaks the Specs

- GIVEN a code_to_spec worker whose change leaves a scenario without a `THEN` step
- WHEN the host validates the worktree again
- THEN the result is `blocked` with one `new_structural_errors` cause per new finding
- AND no resume round is started
- AND the change stays in the worktree for the main agent to repair or discard
