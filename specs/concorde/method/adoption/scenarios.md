# Adoption scenarios

Concrete situations that show the [requirements](requirements.md) of [Adoption](module.md). The
shapes are in the [contracts](contracts.md).

## Survey

### scenario.adoption.survey-proposes — A survey proposes children

- GIVEN an initialized project whose root [Module](../../glossary.json#concept.module) `module.shop` binds `src/`, `tests/`, `README.md` and `pyproject.toml`
- AND a task worktree whose binding names the workspace `adopt` and `module.shop`
- AND a survey worker that proposes the children `module.checkout` binding `src/checkout/` and `module.inventory` binding `src/inventory/`
- WHEN the caller runs `concorde run survey --modules module.shop` there
- THEN the worker's grant reads the Specs and the code `module.shop` binds and writes nothing
- AND its brief lists every bound file with its size in lines
- AND the result is `ok` with a [decomposition proposal](../../glossary.json#concept.decomposition-proposal) naming `module.checkout` and `module.inventory` with their entries
- AND the proposal's remaining entries are the root's entries without the children's paths
- AND no file of the worktree changed

### scenario.adoption.installation-stays — Concorde's installed files stay with the root

- GIVEN a root Module whose Concorde installation realization binds `.claude/skills/concorde/SKILL.md`
- WHEN a survey runs for it
- THEN the inventory in its brief does not list the skill
- AND a proposal giving the skill to a child fails with `inconsistent_proposal` naming the Concorde installation

### scenario.adoption.survey-no-task — An unbound survey before any task

- GIVEN an initialized project whose primary worktree has no [workspace binding](../../glossary.json#concept.workspace-binding), and no task
- WHEN the [main agent](../../glossary.json#concept.main-agent) runs `concorde run survey --modules module.shop` in the primary worktree
- THEN the run is unbound and the result is `ok` with `workspace` null and a decomposition proposal
- AND no [task record](../../glossary.json#concept.task-record) exists or changes

### scenario.adoption.survey-checks — Proposed checks take the configuration's form

- GIVEN a survey whose worker proposes a check with the inputs `src/checkout/` and `tests/` and the env `{"PYTHONPATH": "src"}`
- WHEN the survey ends
- THEN the proposed check's inputs are `src/checkout` and `tests`, as [configured check](../../glossary.json#concept.configured-check) inputs are written, and its env is kept
- AND the worker was asked to name the project's interpreter as `{python}` rather than an interpreter on `PATH`
- BUT a proposed input that is not a canonical project-relative path, such as `../elsewhere`, fails the survey with `inconsistent_proposal` naming it

### scenario.adoption.survey-inconsistent — A proposal that does not fit

- GIVEN a survey worker whose proposal gives a child the entry `lib/` that `module.shop` does not bind, and reuses the registered title `Shop`
- WHEN the host checks the proposal
- THEN the result is `failed`
- AND the [Operation](../../glossary.json#concept.operation)'s link lists both inconsistencies with `capability` as its reason
- AND the worker's proposal stays in the result's `worker` field only

### scenario.adoption.survey-answers — A survey follows the answers and records who settled them

- GIVEN an `ok` survey run whose decision `d.db-helper` chose to keep the database helper with the root
- AND an answers file answering `d.db-helper` with "a Module of its own", answered by the [main agent](../../glossary.json#concept.main-agent)
- AND a survey worker that follows the answer and lists `d.db-helper` without naming a choice
- WHEN the caller runs the survey again with `--answers` and `--input` naming the first run
- THEN the new proposal has a child for the database helper
- AND its decision `d.db-helper` chose "a Module of its own", decided by the main agent, as the host records it
- BUT a proposal that leaves `d.db-helper` out fails with `inconsistent_proposal` naming the answer

### scenario.adoption.decision-by-option — A decision names its choice, the host writes it

- GIVEN a survey or code_to_spec worker whose decision `d.db-helper` lists the options `own-module` "a Module of its own" and `stay-root` "stay with the root" and names `stay-root` as chosen
- WHEN the run ends
- THEN the output's decision has the options "a Module of its own" and "stay with the root", chosen "stay with the root" and `decided_by` `worker`
- AND the worker's claim stays as it was in the result's `worker` field
- BUT a decision that names an identity none of its options has, or names none while no answer settles it, fails the run naming the decision

### scenario.adoption.survey-absolute-paths — Absolute paths in a proposal become project-relative

- GIVEN a survey worker that writes a child entry, a check input and an open question's evidence as absolute paths inside the task worktree, one of them through the worktree's real path
- WHEN the host checks the proposal
- THEN the result is `ok` and each of them is the project-relative path, a directory keeping its trailing `/`
- BUT an absolute path outside the worktree is left as written and fails the survey with `inconsistent_proposal` naming it

## Code to spec

### scenario.adoption.describe-module — A Module's code becomes its Spec

- GIVEN the scaffolded Module `module.checkout` binding `src/checkout/`
- WHEN the caller runs `concorde run code_to_spec --modules module.checkout` in the workspace `adopt`
- THEN the worker's grant reads `src/checkout/` and writes only `module.checkout`'s documents
- AND the worker has no tool that runs commands
- AND the result is `ok` with a Spec description whose changed documents include the entry document `module.md`
- AND the stubs the worker did not fill are removed again
- AND no implementation file changed

### scenario.adoption.open-question — Doubtful behaviour becomes a question

- GIVEN checkout code that retries a declined payment but not a timed-out one, with nothing explaining the difference
- WHEN a code_to_spec worker describes `module.checkout`
- THEN the [Spec](../../glossary.json#concept.spec) states no requirement or scenario about retrying payments
- AND the result is `ok` with an [open question](../../glossary.json#concept.open-question) naming the behaviour, the file, why it is uncertain and the options

### scenario.adoption.answered-deviation — An answer that the code does not follow

- GIVEN the open question about payment retries and an answer "retry both once"
- WHEN the caller runs code_to_spec again with `--answers` and `--input` naming the earlier run
- THEN the Spec states that both declined and timed-out payments are retried once
- AND the result lists that promise with source `answer`
- AND the result lists a deviation with the intended and the observed behaviour

### scenario.adoption.describe-self-repair — The worker repairs what validation reports

- GIVEN a code_to_spec worker whose first round leaves a scenario of `module.checkout` without a THEN step
- WHEN the host validates the Specs after that round
- THEN it resumes the same worker with the structural error, and after a round that repairs it the run ends `ok` with no new error

### scenario.adoption.describe-own-errors — The worker learns the errors it must repair

- GIVEN a scaffolded `module.checkout` whose entry has a structural error, left by an earlier description
- WHEN the caller runs code_to_spec for it again
- THEN the worker's brief lists that error with its rule and document, as one its description must repair

### scenario.adoption.tests-linked — The tests a scenario came from are marked

- GIVEN a code_to_spec run for `module.checkout` whose worker writes `scenario.checkout.submit` and names `tests/test_checkout.py::test_submit`, a test that does not exist and a Spec document as its tests
- WHEN the run ends
- THEN `tests/test_checkout.py` has a `verifies` decorator naming `scenario.checkout.submit` above `test_submit` and a no-op `verifies` definition, and nothing else changed in it
- AND `linked_tests` names that test, and `unlinked_tests` names the other two with their reasons
- AND the decorated file imports nothing of Concorde, and linking the same test again adds nothing

### scenario.adoption.describe-absolute-paths — Absolute test paths in a description still link

- GIVEN a code_to_spec worker whose scenario promise names `<task worktree>/tests/test_checkout.py::test_submit` as its test and whose open question names `<task worktree>/src/checkout/payment.py` as evidence
- WHEN the run ends
- THEN the promise names `tests/test_checkout.py::test_submit`, which `linked_tests` lists
- AND the open question's evidence is `src/checkout/payment.py`

### scenario.adoption.foreign-verifies — A test file with its own `verifies` stays as it is

- GIVEN a code_to_spec run for `module.checkout` whose worker names `tests/test_checkout.py::test_submit` as a test of `scenario.checkout.submit`
- AND `tests/test_checkout.py` imports a `verifies` of its own from the project's test utilities
- WHEN the run ends
- THEN `tests/test_checkout.py` is unchanged
- AND `unlinked_tests` names that test with a reason naming the file's own `verifies` binding and its line
- BUT a file whose `verifies` is the host's no-op helper or Concorde's decorator imported from `concorde.spec.verification` gets the decorator and no second definition

### scenario.adoption.stub-deleted — A stub the worker deleted leaves its Module

- GIVEN the scaffolded Module `module.checkout` and a code_to_spec run that prepared its `contracts.md` stub
- WHEN the worker describes the Module and proposes deleting `contracts.md` and its metadata instead of leaving the stub as it is
- THEN `module.checkout` no longer owns `contracts.md`, the result lists it among the removed stubs, and the run ends `ok` without a structural error

### scenario.adoption.describe-stubs-cleaned — A run that stops early leaves no stubs

- GIVEN a scaffolded Module `module.checkout` without implementation documents
- WHEN a code_to_spec run for it prepares the stubs and its worker then ends `failed` without writing
- THEN the result is `failed` with the worker's chain
- AND none of the prepared stubs remains, and `module.checkout` owns only its entry document again

### scenario.adoption.invalid-answers — Answers that cannot be used

- GIVEN an answers file that is not valid JSON, or whose answer has no `id` or does not say who gave it
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
- THEN the worker is resumed twice with the error, and when it is still there the result is `blocked` with one `new_structural_errors` cause per new finding
- AND the change stays in the worktree for the task level to repair or discard within its authority
