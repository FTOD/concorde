# Code review scenarios

Concrete situations that show the [requirements](requirements.md) at work. The report's shape is
in the [contracts](contracts.md).

## Reviewing

### scenario.code-review.clean — A change that keeps its promises

- GIVEN a task worktree whose changes to a bound Module's code keep every promise of its Spec
- WHEN the main agent runs `code_review` for that Module
- THEN the host computes the diff and runs the Module's configured checks before launching the reviewer
- AND the result has status `ok` and a report with verdict `clean`
- AND the report records the base and the check results it examined, and the host evidence the context identity

### scenario.code-review.all-blocking — Every blocking finding in one report

- GIVEN a change that violates two requirements of a bound Module and omits a test for one of its scenarios
- WHEN the reviewer reviews the change
- THEN one report lists all three problems as blocking findings, each naming its basis
- AND the verdict is `changes_required`
- BUT the reviewer is not resumed and nothing in the worktree changes

### scenario.code-review.spec-gap — Behaviour the Spec does not settle

- GIVEN a change whose behaviour the bound Module's Spec neither requires nor forbids
- WHEN the reviewer cannot judge whether the behaviour is correct
- THEN the report holds a finding of kind Spec gap naming the Spec passage that would have to settle it

### scenario.code-review.foreign-path — A changed file no Module binds is named only

- GIVEN a task diff that also changes a file of another Module and a file no Module binds
- WHEN the host prepares the diff for the reviewer
- THEN the reviewer receives the other Module's change in full, since code reviews read the whole project's implementation
- AND it receives the file no Module binds by its path only, without its contents
- AND the reviewer may report the change as a finding of kind out of scope

### scenario.code-review.failing-check — A failing check is reviewed, not fatal

- GIVEN a bound Module whose configured check fails on the task worktree
- WHEN the main agent runs `code_review` for that Module
- THEN the reviewer receives the failing check result and its log path
- AND the report keeps the host's check result unchanged
- BUT the run does not fail because of the failing check

## Host checks

### scenario.code-review.unknown-basis — A finding citing an unknown promise fails the run

- GIVEN a reviewer whose finding cites a requirement identity the bound Modules' Spec context does not define
- WHEN the host checks the findings
- THEN the result has status `failed` with the unresolved identity as host evidence
