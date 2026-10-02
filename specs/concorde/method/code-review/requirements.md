# Code review requirements

The Module-wide obligations of [Code review](module.md). The report's shape is in the
[contracts](contracts.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

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
[grant](../../glossary.json#concept.grant) of that Module alone, whose brief names the Module's
own Spec documents and code files and gives no diff.

### req.code-review.module-scope-no-base — A Module review has no base

The code review Operation SHALL end a Module review given `--base` `failed` with
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

The code review Operation SHALL give each reviewer, before it judges, the open
[Issues](../../glossary.json#concept.issue) of its reviewed Modules one of whose reports a
`code_review` run made, each with its identity, severity, tier, title, description and evidence as
its latest report states them.

## Findings

### req.code-review.evidence — Every finding names its basis and locations

Every finding SHALL name a reviewed Module, a basis, which is the requirement, scenario, contract,
concept or [Spec](../../glossary.json#concept.spec) passage of that Module's
[Spec context](../../glossary.json#concept.spec-context) it is judged against, and at least one
location in the project's files that shows it.

### req.code-review.spec-challenge — A Spec the reviewer disputes is challenged

A reviewer that judges a requirement, scenario or contract of its reviewed Module unreasonable or
unrealizable SHALL report it as a finding of kind `spec-challenge` whose basis is that promise and
whose problem says why, rather than as a defect of the code.

### req.code-review.evidence-resolves — Cited evidence exists

The code review Operation SHALL make a reviewer's Modules `incomplete` with `unresolved_evidence`,
reporting none of their findings, when a finding names a Module the reviewer did not review, cites
a stable identity or document that the reviewed Modules' Spec context does not define, or names a
location whose file is neither in the worktree nor a changed path of the diff, or whose line lies
beyond that file's end.

## Issues and verdict

### req.code-review.findings-as-issues — Every finding is reported as an Issue

The code review Operation SHALL report every finding of a Module whose evidence resolved through the
Issue store as one [Issue report](../../glossary.json#concept.issue-report) with the finding's
[tier](../../glossary.json#concept.issue-tier) and
[severity](../../glossary.json#concept.issue-severity), owned by the finding's Module, appending a
finding that names an offered earlier Issue to that Issue at the
[revision](../../glossary.json#concept.issue-revision) read just before, and creating an Issue
for every other finding.

### req.code-review.no-closing — The review closes no Issue

The code review Operation SHALL NOT close or reopen an Issue; it lists the earlier Issues the
reviewer found resolved in its report.

### req.code-review.store-refusal — A refusal of the Issue store is an error, not an Issue

When the Issue store refuses a report, the code review Operation SHALL make that Module `incomplete`
with `issues_unreported`, whose cause is the store's error, report none of that Module's later
findings, and record no Issue about the refusal.

### req.code-review.verdict-derived — The Operation derives the verdict

The code review Operation SHALL derive each reviewed Module's outcome as `incomplete` when it could
not be reviewed or its Issues could not be read or all written, `changes_required` when an Issue of a
blocking tier stands for it, reported by the run or an earlier Issue it carried, and `accepted`
otherwise, and the verdict as `incomplete` when any Module is, else `changes_required` when any
Module is, else `accepted`.

### req.code-review.no-resume — No automatic resume

The code review Operation SHALL NOT resume a reviewer after it has returned its result.
