# Code review requirements

[Code review](module.md) has these Module-wide obligations. The report's shape is in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete situations.

## Inputs

### req.code-review.diff-within-grant — The diff shows only readable contents

In a change review, the diff given to the reviewer SHALL show the contents of a changed path only
when the grant makes that path readable, listing every other changed path by name only.

### req.code-review.checks-by-host — Checks run through the Operation

The code review [Operation](../../glossary.json#concept.operation) SHALL run the
[configured checks](../../glossary.json#concept.configured-check) its scope selects through Check
execution before it launches a reviewer: in a change review those of the bound Modules and of every
Module that uses one of them, in a Module review those of each reviewed Module.

### req.code-review.module-scope — A Module review judges each Module whole

In a Module review, the code review Operation SHALL launch one reviewer per named
[Module](../../glossary.json#concept.module), under the `review-code`
[grant](../../glossary.json#concept.grant) of that Module alone, whose brief names the Module's own
Spec documents and code files and gives no diff.

### req.code-review.module-scope-no-base — A Module review has no base

When a Module review is given `--base`, the code review Operation SHALL end it `failed` with
`base_in_module_scope` before it launches a reviewer.

## Reviewing

### req.code-review.reads-check-logs — The reviewer reads the check logs

The code_review Operation SHALL let each reviewer read the log of every check the Operation ran for
the run.

### req.code-review.read-only — The reviewer cannot change or run anything

A reviewer's tool list SHALL contain only tools that read files, besides the
[worker backend](../../glossary.json#concept.worker-backend)'s tool for returning the
[worker result](../../glossary.json#concept.worker-result).

### req.code-review.no-edits — The worktree is left unchanged

The code review Operation SHALL leave every file of the workspace unchanged.

A change found by the [write audit](../../glossary.json#concept.write-audit) makes the reviewer's
Modules `incomplete` with the changed paths as host evidence.

### req.code-review.one-pass — Every blocking finding at once

A reviewer SHALL report every blocking finding it can establish in a single run.

### req.code-review.earlier-issues — The reviewer receives the earlier Issues

Before each reviewer judges, the code review Operation SHALL give it the
[Issues](../../glossary.json#concept.issue) that meet these conditions, each with its identity,
severity, tier, title, description and evidence as its latest report states them:

- The Issue is open and is an Issue of one of the reviewer's reviewed Modules.
- A `code_review` run made one of its reports.

Where the issues part is not installed, there are no earlier Issues. In that case, the reviewer
receives none.

## Findings

### req.code-review.evidence — Every finding names its basis and locations

Every finding SHALL name all of these:

- A reviewed Module.
- A basis: the requirement, scenario, contract, concept or [Spec](../../glossary.json#concept.spec)
  passage of that Module's [Spec context](../../glossary.json#concept.spec-context) against which
  the finding is judged.
- At least one location in the project's files that shows the finding.

### req.code-review.spec-challenge — A Spec the reviewer disputes is challenged

A reviewer that judges a requirement, scenario or contract of its reviewed Module unreasonable or
unrealizable SHALL report it as a finding of kind `spec-challenge` whose basis is that promise and
whose problem says why, rather than as a defect of the code.

### req.code-review.evidence-resolves — Cited evidence exists

The code review Operation SHALL report no finding that, after the reviewer's one
[resume round](../../glossary.json#concept.resume-round) to correct its citations, still has one of
these faults, listing each such finding as rejected with the reason and still reporting every other
finding of that reviewer:

- It names a Module the reviewer did not review.
- It cites a stable identity or document that the reviewed Modules' Spec context does not define.
- It names a location whose file is neither in the worktree nor a changed path of the diff.
- It names a location whose line lies beyond that file's end.

A citation that does not hold is usually a slip of an otherwise sound finding, such as a line range
a little past a file's end. The reviewer is therefore resumed once with every such citation to
correct. What still does not hold afterwards costs only that finding. The reviewer's other findings
stand. Its Modules' outcomes follow from them.

## Issues and verdict

### req.code-review.findings-as-issues — Every finding is reported as an Issue where Issues exist

The code review Operation SHALL report every finding of a Module whose evidence resolved through the
Issue store as one [Issue report](../../glossary.json#concept.issue-report) with the finding's
[tier](../../glossary.json#concept.issue-tier) and
[severity](../../glossary.json#concept.issue-severity), owned by the finding's Module, appending a
finding that names an offered earlier Issue to that Issue at the
[revision](../../glossary.json#concept.issue-revision) read just before, and creating an Issue for
every other finding, wherever the issues part is installed.

Where the issues part is not installed, the review does all of these:

- Keeps every finding in its report with its tier and severity.
- Records nothing outside the run.
- Says in its report that the findings were not recorded as Issues.

Issues is an [optional integration](../../glossary.json#concept.optional-integration) of the method
part. The review's judgement, its evidence checks and its verdict are the same either way.

### req.code-review.blank-earlier — An empty earlier names no Issue

The code review Operation SHALL treat a reviewer's finding whose `earlier` is empty or blank as
naming no earlier Issue, as if the field were left out, while every other `earlier` is checked
against the earlier Issues it offered.

### req.code-review.no-closing — The review closes no Issue

The code review Operation SHALL NOT close or reopen an Issue: it lists the earlier Issues the
reviewer found resolved in its report.

### req.code-review.store-refusal — A refusal of the Issue store is an error, not an Issue

When the Issue store refuses a report, the code review Operation SHALL make that Module `incomplete`
with `issues_unreported`, whose cause is the store's error, report none of that Module's later
findings, and record no Issue about the refusal.

### req.code-review.verdict-derived — The Operation derives the verdict

The code review Operation SHALL derive each reviewed Module's outcome as `incomplete` when it could
not be reviewed or its Issues could not be read or all written, `changes_required` when an Issue of
a blocking tier stands for it, reported by the run or an earlier Issue it carried — or, where the
issues part is not installed, when the run reports a finding of a blocking tier — and `accepted`
otherwise, and the verdict as `incomplete` when any Module is, else `changes_required` when any
Module is, else `accepted`.

### req.code-review.no-resume — No resume but to correct citations

After a reviewer returns its result, the code review Operation SHALL NOT resume it, except once,
with those citations to correct, when a finding's Module, basis or location does not hold.
