# Code review requirements

[Code review](module.md) has these Module-wide obligations. The report's shape is in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete situations.

## Inputs

### req.code-review.diff-within-grant — The diff shows only readable contents

In a change review, the diff given to the reviewer SHALL show the contents of a changed path only
when the grant makes that path readable, listing every other changed path by name only.

### req.code-review.checks-by-host — Checks run through the Operation

Before it launches a reviewer, the code review [Operation](../../glossary.json#concept.operation)
SHALL run the [configured checks](../../glossary.json#concept.configured-check) through Check
execution according to its scope:

- In a change review, run those of the bound Modules and of every Module that uses one of them.
- In a Module review, run those of each reviewed Module.

### req.code-review.module-scope — A Module review judges each Module whole

In a Module review, the code review Operation SHALL launch one reviewer per named
[Module](../../glossary.json#concept.module), each with these:

- The `review-code` [grant](../../glossary.json#concept.grant) of that Module alone.
- A brief that names the Module's own Spec documents and code files and gives no diff.

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

- The Issue is open and is an Issue of one of its reviewed Modules.
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

When a reviewer judges a requirement, scenario or contract of its reviewed Module unreasonable or
unrealizable, it SHALL report it as a finding with all of these properties:

- Its kind is `spec-challenge`.
- Its basis is that promise.
- Its problem says why the reviewer judges it unreasonable or unrealizable.
- It is not a defect of the code.

### req.code-review.evidence-resolves — Cited evidence exists

After the reviewer's one [resume round](../../glossary.json#concept.resume-round) to correct its
citations, the code review Operation SHALL handle findings as follows:

- Report no finding that still names a Module the reviewer did not review.
- Report no finding that still cites a stable identity or document that the reviewed Modules' Spec
  context does not define.
- Report no finding that still names a location whose file is neither in the worktree nor a changed
  path of the diff.
- Report no finding that still names a location whose line lies beyond that file's end.
- List each such finding as rejected with the reason.
- Still report every other finding of that reviewer.

A citation that does not hold is usually a slip of an otherwise sound finding, such as a line range
a little past a file's end. The reviewer is resumed once with every such citation to correct.
What still does not hold afterwards costs only that finding. The reviewer's other findings stand.
Its Modules' outcomes follow from them.

## Issues and verdict

### req.code-review.findings-as-issues — Every finding is reported as an Issue where Issues exist

Wherever the issues part is installed, the code review Operation SHALL report every finding of a
Module whose evidence resolved through the Issue store as follows:

- Report it as one [Issue report](../../glossary.json#concept.issue-report) with the finding's
  [tier](../../glossary.json#concept.issue-tier) and
  [severity](../../glossary.json#concept.issue-severity).
- Assign ownership to the finding's Module.
- For a finding that names an offered earlier Issue, append it to that Issue at the
  [revision](../../glossary.json#concept.issue-revision) read just before.
- For every other finding, create an Issue.

Where the issues part is not installed, the review does all of these:

- Keeps every finding in its report with its tier and severity.
- Records nothing outside the run.
- Says in its report that the findings were not recorded as Issues.

Issues is an [optional integration](../../glossary.json#concept.optional-integration) of the method
part. The review's judgement, its evidence checks and its verdict are the same either way.

### req.code-review.blank-earlier — An empty earlier names no Issue

The code review Operation SHALL handle a reviewer's findings according to these field values:

- When `earlier` is empty or blank, treat the finding as naming no earlier Issue, as if the field
  were left out.
- For every other `earlier`, check it against the earlier Issues the Operation offered.

### req.code-review.no-closing — The review closes no Issue

The code review Operation SHALL NOT close or reopen an Issue.

It lists the earlier Issues the reviewer found resolved in its report.

### req.code-review.store-refusal — A refusal of the Issue store is an error, not an Issue

When the Issue store refuses a report, the code review Operation SHALL do all of these:

- Make that Module `incomplete` with `issues_unreported`, whose cause is the store's error.
- Report none of that Module's later findings.
- Record no Issue about the refusal.

### req.code-review.verdict-derived — The Operation derives the verdict

The code review Operation SHALL derive each reviewed Module's outcome and the verdict according to
these rules, in order:

- When a Module could not be reviewed or its Issues could not be read or all written, its outcome
  is `incomplete`.
- Otherwise, a Module's outcome is `changes_required` in either of these cases:
  - Where the issues part is installed, an Issue of a blocking tier stands for it, reported by the
    run or an earlier Issue it carried.
  - Where the issues part is not installed, the run reports a finding of a blocking tier.
- Otherwise, a Module's outcome is `accepted`.
- When any Module is incomplete, the verdict is `incomplete`.
- Otherwise, when any Module is `changes_required`, the verdict is `changes_required`.
- Otherwise, the verdict is `accepted`.

### req.code-review.no-resume — No resume but to correct citations

After a reviewer returns its result, the code review Operation SHALL NOT resume it except once to
correct citations when a finding's Module, basis or location does not hold.
