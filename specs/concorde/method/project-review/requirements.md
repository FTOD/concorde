# Project review requirements

[Project review](module.md) has these Module-wide obligations. The result's and the record's shapes
are in the [contracts](contracts.md). The [scenarios](scenarios.md) show the obligations in concrete
situations.

## What a review covers

### req.project-review.covered-modules — Every registered Module by default

When `--modules` is not given, the `project_review` [Operation](../../glossary.json#concept.operation)
SHALL cover every [Module](../../glossary.json#concept.module) the examined worktree registers, in a
bound and an [unbound run](../../glossary.json#concept.unbound-run) alike.

### req.project-review.module-panel — A Spec panel per Module

For each covered Module that passes structural validation, whose grants can be computed and whose
Spec panel is not skipped, the Operation SHALL run a
[Spec](../../glossary.json#concept.spec) panel of `--reviewers` reviewers and a chair without
architects.

### req.project-review.module-code-review — A code review per Module

For each covered Module that passes structural validation, whose grants can be computed and whose
code review is not skipped, the Operation SHALL run a code review of Module scope, whether or not
its Spec panel is skipped.

### req.project-review.architecture-once — One architecture review per run

Unless `--architects` is 0 or the review is skipped, the Operation SHALL run one architecture review
for the whole project in each run: `--architects` architects and a chair, each under the
`review-architecture` [grant](../../glossary.json#concept.grant) of every Module.

### req.project-review.worker-ids — Each worker under its own worker id

The Operation SHALL launch every worker under the [worker id](../../glossary.json#concept.worker-id)
of its seat: `reviewer1` to `reviewer5` and `chair` for a Spec panel, `architect1`, `architect2` and
`arch_chair` for the architecture review, and `code_reviewer` for a code review.

### req.project-review.parallel — At most --parallel reviews at once

The Operation SHALL run at most `--parallel` Spec panels and code reviews at the same time.

### req.project-review.read-only — The review changes nothing it examines

The Operation SHALL change no file of the examined worktree: it launches only reading workers, and
it publishes the Issues and the review record only through commits of their own on the primary
branch.

## Deterministic findings

### req.project-review.checks-every-run — The checks run on every run

On every run it does not refuse, whether or not a part of a Module's review is skipped, the
Operation SHALL run every
[configured check](../../glossary.json#concept.configured-check) of the work stage of every covered
Module.

### req.project-review.coverage-every-run — Uncovered scenarios are found on every run

On every run it does not refuse, the Operation SHALL find each covered Module's scenarios that no
[verification declaration](../../glossary.json#concept.verification-declaration) in a file a Module
binds names.

### req.project-review.unowned-every-run — Unowned files are found on every run

On every run it does not refuse and in which Git lists the tracked files, the Operation SHALL find
the files Git tracks that no Module binds.

### req.project-review.deterministic-issues — Each deterministic problem is one Issue

Where the issues part is installed, the Operation SHALL report each failed or timed-out check, each
covered Module's uncovered scenarios and the files bound to no Module as one
[Issue](../../glossary.json#concept.issue) each, with this title, tier and severity:

| Problem | The Issue's Module | Title | Tier | Severity |
| --- | --- | --- | --- | --- |
| A configured check failed | the check's Module | `Configured check <check> does not pass` | `obvious-fix` | `high` |
| A configured check timed out | the check's Module | `Configured check <check> does not pass` | `decision-needed` | `medium` |
| Scenarios that no verification declaration names | their Module | `Scenarios of <module> that no test verifies` | `obvious-fix` | `medium` |
| Tracked files bound to no Module | the root Module | `Tracked files bound to no Module` | `decision-needed` | `medium` |

### req.project-review.deterministic-earlier — An unchanged problem writes nothing

When the open Issue of a deterministic problem's Module, kind and title already states the problem
with the same text, tier and severity, the Operation SHALL list that Issue as carried, with no new
report.

### req.project-review.deterministic-resolved — A problem gone is listed resolved

When the run examined a Module's deterministic problems of one kind and found none with the title
of an open Issue of that Module and kind, the Operation SHALL list that Issue as resolved, leaving
it open for a task to close.

## Skipping and the record

### req.project-review.skip-unchanged — A part whose input is unchanged is skipped

Unless `--full` is given, where the issues part is installed, the Operation SHALL skip a Module's
Spec panel, a Module's code review or the architecture review when the identity of what it would
judge equals the identity the [review record](module.md#the-review-record) holds for that part.

### req.project-review.nothing-to-review — A run with every worker part skipped is refused

When every covered Module's Spec panel and code review would be skipped, and so would the
architecture review unless `--architects` is 0, the Operation SHALL refuse the run with
`nothing_to_review` before any step.

A refused run runs no check and finds no uncovered scenario and no unowned file. It writes no Issue
and no review record. Its error names `--full` as the way to review the parts anyway.

### req.project-review.no-skip-without-issues — Nothing is skipped without Issues

Where the issues part is not installed, the Operation SHALL skip no part by its identity.

### req.project-review.no-record-without-issues — No record without Issues

Where the issues part is not installed, the Operation SHALL write no review record.

### req.project-review.record-completed — Only completed parts are recorded

The Operation SHALL record a part in the review record only when the part's workers finished and all
of its Issues were written.

### req.project-review.record-commit — The record is committed alone under the merge lock

When a completed part changes the review record, the Operation SHALL commit the record alone on the
primary branch while it holds the [merge lock](../../glossary.json#concept.merge-lock), before it
returns its result.

### req.project-review.record-refused — A refused record fails the run, not the verdict

When the committed record is not valid, the record file holds a change other than a valid record
an interrupted write left, or the commit fails, the Operation SHALL leave the committed record as
it was and end the run `failed` with `record_unpublished` while keeping the verdict in its output.

### req.project-review.record-leftover — An interrupted write's record is put back

When the record file holds a valid record no commit holds, the Operation SHALL put the file back to
its committed version before it writes the record.

### req.project-review.skipped-resolutions — A skipped part's resolutions still hold

The Operation SHALL count an earlier Issue as resolved only while its revision equals the one
offered to the part that found it resolved, whether that part ran in this run or its record entry
lists the resolution for a skipped part.

## Issues and the verdict

### req.project-review.phases — Each report names its kind of review

The Operation SHALL give every [Issue report](../../glossary.json#concept.issue-report) the
provenance `phase` of the part that made it:
`spec-panel`, `code-review`, `architecture`, `check`, `coverage` or `unowned`.

### req.project-review.outcome-standing — Outcomes come from the Issues that stand

Where the issues part is installed, after every part, the Operation SHALL derive each complete
Module's outcome from the open Issues that `spec_panel`, `code_review` or `project_review` made for
it and that no part of the run found resolved: `changes_required` when one of a blocking tier
stands, `accepted` otherwise.

### req.project-review.outcome-findings — Without Issues, outcomes come from the findings

Where the issues part is not installed, the Operation SHALL derive each complete Module's outcome
from the findings of this run that concern it, as from the Issues they would become.

### req.project-review.issue-failures — A failure of the Issue system is never an Issue

When the Issue store refuses a read or a write, the Operation SHALL carry the store's error in the
result's [error chain](../../glossary.json#concept.error-chain), never as an Issue.
