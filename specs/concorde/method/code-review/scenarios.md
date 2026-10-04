# Code review scenarios

Concrete situations that show the [requirements](requirements.md) at work. The report's shape is
in the [contracts](contracts.md).

## Change review

### scenario.code-review.clean — A change that keeps its promises

- GIVEN a workspace whose changes to a bound [Module](../../glossary.json#concept.module)'s code keep every promise of its [Spec](../../glossary.json#concept.spec)
- WHEN the caller runs `code_review` for that Module
- THEN the [Operation](../../glossary.json#concept.operation) computes the diff and runs the Module's [configured checks](../../glossary.json#concept.configured-check) before launching the reviewer
- AND the result has status `ok` and a report with verdict `accepted`
- AND the report records the scope, the base and the [check results](../../glossary.json#concept.check-result) it examined, and the run's host evidence carries the [context identity](../../glossary.json#concept.context-identity)

### scenario.code-review.all-blocking — Every blocking finding in one report, each an Issue

- GIVEN a change that violates two requirements of a bound Module and omits a test for one of its scenarios
- WHEN the reviewer reviews the change
- THEN one report lists all three problems as findings of a blocking tier, each naming its basis and locations
- AND the Operation reports each as a new [Issue](../../glossary.json#concept.issue) owned by that Module with the finding's severity and tier, and names the Issue in the finding
- AND the verdict is `changes_required`
- BUT the reviewer is not resumed, since every citation holds, and nothing in the worktree changes

### scenario.code-review.spec-gap — Behaviour the Spec does not settle

- GIVEN a change whose behaviour the bound Module's Spec neither requires nor forbids
- WHEN the reviewer cannot judge whether the behaviour is correct
- THEN the result has status `ok`, not `blocked`
- AND the report holds a finding of kind [Spec gap](../../glossary.json#concept.spec-gap) whose basis is the passage of the bound Module's Spec context that would have to settle it, which resolves in that context

### scenario.code-review.foreign-path — A changed file no Module binds is named only

- GIVEN a workspace diff that also changes a file of another Module and a file no Module binds
- WHEN the Operation prepares the diff for the reviewer
- THEN the reviewer receives the other Module's change in full, since code reviews read the whole project's implementation
- AND it receives the file no Module binds by its path only, without its contents
- AND the reviewer may report the change as a finding of kind out of scope located at that path

### scenario.code-review.failing-check — A failing check is reviewed, not fatal

- GIVEN a bound Module whose configured check fails on the workspace
- WHEN the caller runs `code_review` for that Module
- THEN the reviewer receives the failing check result and its log path
- AND the report carries that check result with outcome `failed`, its exit code and its log path
- BUT the run does not fail because of the failing check

## Module review

### scenario.code-review.module-review — Each Module judged whole by its own reviewer

- GIVEN two Modules named with `--scope module`
- WHEN the caller runs `code_review`
- THEN the Operation runs each Module's own configured checks and launches one reviewer per Module under that Module's grant alone
- AND each reviewer's brief names its Module's Spec documents and code files and gives no diff
- AND the report has one entry per Module, with its own outcome, context identity, summary and findings, and no base

### scenario.code-review.module-review-base — A Module review refuses a base

- GIVEN a caller that runs `code_review --scope module --base HEAD`
- WHEN the Operation checks its arguments
- THEN the result has status `failed` with `base_in_module_scope`
- AND no reviewer was launched

### scenario.code-review.spec-challenge — A reviewer challenges an unrealizable requirement

- GIVEN a Module whose requirement cannot be realized with what the Module may use, and whose code therefore does not keep it
- WHEN its reviewer judges the Module
- THEN it reports a finding of kind `spec-challenge`, usually `decision-needed`, whose basis is that requirement, whose problem says why it cannot be realized and whose locations show the code concerned
- AND the Operation reports it as an Issue of the Module like any other finding

### scenario.code-review.unbound-module-review — A Module review of the primary worktree

- GIVEN a worktree without a [workspace binding](../../glossary.json#concept.workspace-binding), such as the primary worktree
- WHEN the caller runs `code_review --scope module --modules <id>` there, without `--base`
- THEN the review judges that Module as committed at the worktree's `HEAD`
- AND reports its findings as Issues of the project without a workspace

## Issues

### scenario.code-review.earlier-issue — A problem already recorded is updated, not duplicated

- GIVEN a Module with an open Issue an earlier `code_review` reported and another an earlier review found resolved in the code
- WHEN its reviewer names the first in a finding and lists the second as resolved
- THEN the Operation appends the finding to the first Issue instead of creating one
- AND lists the second under `resolved` in the report, without closing it
- AND an earlier Issue the reviewer neither names nor resolves is listed as `carried` and, when of a blocking tier, makes the outcome `changes_required`

### scenario.code-review.blank-earlier — An empty earlier names no earlier Issue

- GIVEN a reviewer that returns new findings, one with `earlier` empty and one with `earlier` blank
- WHEN the Operation reports them
- THEN the run ends `ok` and each finding is recorded as a new Issue
- BUT no finding names an earlier Issue and none is listed as ignored

### scenario.code-review.store-refusal — A refusal of the Issue store

- GIVEN a review whose report the Issue store refuses
- WHEN the Operation reports a Module's findings
- THEN that Module is `incomplete` with `issues_unreported`, whose cause is the store's error
- AND the result is `failed`, still carrying every finding
- BUT no Issue records the refusal

### scenario.code-review.without-issues — Without the issues part the findings stay in the report

- GIVEN a project whose `concorde` does not offer `issues`, the issues part not being installed
- WHEN the Operation reviews a change whose reviewer returns a finding of a blocking tier
- THEN the Module is `changes_required`, its finding keeps `issue` null and its `earlier_issues` is null
- AND the result's summary says the findings were not recorded as Issues
- BUT no Issue is recorded

## Host checks

### scenario.code-review.citation-resume — A reviewer corrects its citations once

- GIVEN a reviewer whose finding names lines beyond its file's end, beside a finding that holds
- WHEN the Operation checks the reviewer's result
- THEN it resumes the reviewer once, its repair naming the location that does not hold and the finding's title
- AND when the resumed reviewer returns the finding with a location that holds, both findings are reported as Issues and nothing is rejected

### scenario.code-review.unknown-basis — A finding citing an unknown promise is not reported

- GIVEN a reviewer that, also after its one [resume round](../../glossary.json#concept.resume-round), returns two findings
- AND its first finding cites a requirement identity the reviewed Modules' [Spec context](../../glossary.json#concept.spec-context) does not define and names an earlier Issue
- AND its second finding holds
- WHEN the Operation checks the findings
- THEN the first finding is reported as no Issue and listed under its Module's `rejected` without that earlier Issue, with the reason naming the unresolved identity, which is also host evidence
- AND the second finding is reported as an Issue, the Module is `changes_required` and the run ends `ok`

### scenario.code-review.unknown-location — A finding located in no file is not reported

- GIVEN a reviewer that, also after its one resume round, returns findings naming locations that do not hold
- AND those locations name a file that does not exist, lines beyond the file's end or a place outside the project
- AND the reviewer also returns one finding whose location holds
- WHEN the Operation checks the findings
- THEN each finding whose location does not hold is listed under `rejected` with the reason, and each such location is host evidence
- BUT the finding whose location holds is reported as an Issue and the run ends `ok`

### scenario.code-review.reviewer-change — A reviewer that changes a file fails the run

- GIVEN a reviewer that changes a file of the workspace
- WHEN the Operation audits the worktree
- THEN the result has status `failed` with the changed path in its `audit` host evidence
