# Specification scenarios

Concrete situations that show the [requirements](requirements.md) at work. The Spec change's shape
is in the [contracts](contracts.md).

## Changing Specs

### scenario.specification.change — A Spec change is made and validated

- GIVEN a task worktree whose Specs pass structural validation
- WHEN the main agent runs `specify` for a Module with an intent the worker can carry out
- THEN the worker edits only documents that Module owns
- AND the host regenerates the registry mirror and validates the task worktree
- AND the result has status `ok` with the changed documents, the affected Modules and no new finding

### scenario.specification.declare-pending — A new file is declared, not created

- GIVEN an intent that needs a new implementation file in a bound Module
- WHEN the worker adds the file as a pending entry of one of the Module's realizations
- THEN the Spec change lists the declared entry with its Module and realization
- BUT the file does not exist in the task worktree after the run

### scenario.specification.repair-broken — A run repairs Specs that were already invalid

- GIVEN a task worktree whose Specs already have structural errors
- WHEN the main agent runs `specify` with an intent that repairs some of them
- THEN the remaining baseline errors are reported as pre-existing
- AND the result has status `ok` when the change introduced no new error

## Stopping

### scenario.specification.new-error — A change that breaks the Specs stops the run

- GIVEN a worker whose edit introduces a structural error the baseline did not have
- WHEN the host validates the task worktree after the worker returned
- THEN the result has status `blocked` with the new findings as evidence
- AND the worker's edits stay in the task worktree for the main agent to inspect
- BUT the worker is not resumed

### scenario.specification.foreign-document — A needed document of another Module stops the run

- GIVEN an intent that can only be carried out by changing a document of a Module that is not bound
- WHEN the worker finds it cannot make the change within its grant
- THEN the result has status `blocked`
- AND its error chain ends in the worker's own link naming the other Module, the reason it could not change it and the options it sees

### scenario.specification.code-write — A write to code fails the run

- GIVEN a specify run whose write audit finds a changed implementation file
- WHEN the host evaluates the audit
- THEN the result has status `failed` with the changed path as host evidence
- BUT the host runs no validation for the run
