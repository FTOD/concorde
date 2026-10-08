# Code review

## Purpose

Code review gives callers an independent judgement of code against the
[Specs](../../glossary.json#concept.spec). Where the issues part is installed, it records every
problem it finds as an [Issue](../../glossary.json#concept.issue) of the project. Where it is not,
it records every problem in its run result alone. It provides the `code_review`
[Operation](../../glossary.json#concept.operation), which judges in one of two scopes:

- A **change review** judges a workspace's code changes since a base commit.
- A **Module review** judges each named [Module](../../glossary.json#concept.module)'s whole code
  against all of its Specs.

A reviewer worker reads the Specs, code and tests. It changes nothing. It reports every problem it
can establish in one pass. Each problem is tied to the promise it judges the code against and to
the code that shows it. When code and Spec disagree, it says which side is wrong. It may challenge
a Spec requirement it judges unreasonable or unrealizable. The Operation checks every finding's
evidence. Where it can, it reports each finding as an Issue. It derives the verdict from the tiers
of what stands. Acting on them is later work of the task. The reviewer never edits a file or runs
a command. The Operation's host steps compute the diff and run the configured checks through Check
execution. They leave the workspace unchanged. A review without findings is evidence about the
reviewed inputs only, not proof of no other defect.

## Core concepts

### Two scopes

A **change review** (`--scope change`, the default) judges what a workspace changed. One reviewer
receives the diff from the base commit to the worktree and judges it against the bound Modules'
Specs. This is the usual review after `implement`. A **Module review** (`--scope module`) judges
what a Module is. One reviewer per named Module reads all of that Module's Specs and all of its
code and tests. It judges whether the code is right, with no diff and no base. It suits a
whole-Module check in these cases:

- After a large change.
- On code an earlier version wrote.
- On a project whose code came before its Specs.

Both scopes share these:

- The reviewer's brief.
- The findings.
- The checks.
- The Issue reporting.
- The report's shape.

### Findings and their evidence

Each **finding** names these:

- The reviewed Module it concerns.
- Its kind.
- Its [severity](../../glossary.json#concept.issue-severity).
- Its [tier](../../glossary.json#concept.issue-tier).
- A title.
- The problem.
- Its impact.
- Its basis.
- The code locations that show it.
- The evidence it quotes.
- A suggested repair.

Its kind says which side the reviewer judges wrong:

- The code, in one of these ways:
  - A **violation** of a stated promise.
  - A **defect** the Spec's promises imply.
  - A **missing test** for a scenario the reviewed code touches.
  - A change **out of scope**, outside the reviewed Modules' code.
- Neither yet: a [Spec gap](../../glossary.json#concept.spec-gap), where the code does something
  the Spec neither requires nor forbids.
- The Spec: a **Spec challenge**, a requirement, scenario or contract the reviewer judges
  unreasonable or unrealizable. It says why, for example because two promises contradict each
  other or because what it requires cannot be observed or built with what the Module may use.

Every finding names its **basis** from the reviewed Module's
[Spec context](../../glossary.json#concept.spec-context). This is a stable identity (requirement,
scenario, contract or concept) or a Spec passage. The basis serves one of these roles:

- The promise it is judged against.
- The passage that would have to settle a Spec gap.
- The passage a Spec challenge disputes.

Every finding also names its **locations**, the files and lines of the project's code that show
it. The reviewer judges only against the Specs in its context, never against taste or another
Module's code. Thus, a disputed finding traces to a written promise and to the code in question.

A finding's tier says who may act on it, as for every Issue. For code that keeps its promises but
could serve them better, the tier is `suggestion`. Otherwise, it is a blocking tier, `obvious-fix`,
`preferred-fix` or `decision-needed`. Since changing what a Module promises is decided above the
task, a Spec challenge is usually `decision-needed`. Its severity says, independently, how much
the problem matters to the callers and the later tasks relying on the code. It ranges from
`critical`, such as wrong results or lost data, down to `low`, something cosmetic.

### Earlier Issues

A reviewed Module's **earlier Issues** are its open Issues one of whose reports a `code_review` run
made, or a [Project review](../project-review/module.md) run made with the provenance phase
`code-review`. The reviewer receives them before it judges. A problem already recorded is reported again only
when it changed, as a finding naming that Issue and never as a new one. It lists each earlier Issue
the code no longer has, with its reason, as **resolved**. An earlier Issue it neither names nor
resolves still stands, **carried**. The Operation, never the reviewer, writes the Issues. It appends
a finding that names an earlier Issue to that Issue. It records every other finding as a new Issue.
It closes none. The resolved Issues are listed in the report for the task to close.

Earlier Issues exist only where the issues part is installed. Without it, the review does these:

- Reads none.
- Reports nothing outside the run.
- Keeps every finding in its report with its tier and severity.
- Lists no Issue as carried or resolved.
- Says in its report that its findings were not recorded as Issues
  ([req.code-review.findings-as-issues](requirements.md#req.code-review.findings-as-issues)).

### The verdict

Each reviewed Module's **outcome** follows these rules:

- When an Issue of a blocking tier stands for it, reported by this review or carried from an
  earlier one, its outcome is `changes_required`.
- Without the issues part, a finding of a blocking tier reported by this review gives the same
  outcome.
- When none does, its outcome is `accepted`.
- When it could not be reviewed or its Issues could not be written, its outcome is `incomplete`.

The report's verdict follows these rules, in order:

- When any Module is incomplete, the verdict is `incomplete`.
- Otherwise, when any Module requires changes, the verdict is `changes_required`.
- Otherwise, the verdict is `accepted`.

The Operation derives it itself from the tiers. It verifies what it can decide: that every basis
and location exists and which verdict follows. Otherwise, it keeps findings as the reviewer's
claims.

### One pass

A reviewer reports every blocking finding in one pass. Another round of judging re-reads
everything and lets one fix hide the next. This is also why a review is not repeated automatically
after `implement`. The one [resume round](../../glossary.json#concept.resume-round) a reviewer may
get judges nothing anew. When a finding's Module, basis or location does not hold, the reviewer is
resumed once with those citations to correct. It returns its whole result again.

## Overview

A review is in three hands:

- The Operation prepares the code and the evidence.
- The reviewer judges it once.
- The Operation checks the findings, reports them as Issues and settles the verdict.
- The task level acts on the Issues by their tier.

```d2 illustrative
direction: down
classes: {
  agent: {style: {fill: "#e8edff"; stroke: "#3b5bdb"; stroke-width: 2; border-radius: 6}}
  program: {style: {fill: "#f3f4f6"; stroke: "#6b7280"; stroke-width: 2; border-radius: 6}}
}
prepare: "Operation: freeze the review-code grant,\ndiff the workspace from its base (change scope),\nrun the configured checks,\nread the earlier Issues" {class: program}
judge: "Reviewer: judges the change, or the whole\nModule, against the Specs, in one pass" {class: agent}
settle: "Operation: check every basis and location,\nreport each finding as an Issue,\nderive the verdict" {class: program}
issues: "Issues of the project" {shape: cylinder}
accepted: "Task level: move to validation" {class: agent}
spec: "Task level: specify, or escalate\na decision-needed Issue" {class: agent}
code: "Task level: usually implement" {class: agent}
prepare -> judge -> settle
settle -> issues: "append or create"
settle -> accepted: accepted
settle -> spec: "changes_required:\nSpec gaps and challenges"
settle -> code: "changes_required:\nother blocking Issues"
```

## Running code_review

```text
concorde run code_review [--scope change|module] [--modules <module-id>[,<module-id>…]]
                         [--base <ref>] [--focus "<text>"]
```

The run judges the [workspace](../../glossary.json#concept.workspace) whose binding lies in the
worktree it starts in. `--modules` names the reviewed Modules, the binding's by default. An [unbound
run](../../glossary.json#concept.unbound-run) must name them. Otherwise, its grant cannot be
computed and it ends `failed` with `grant_unavailable`. `--focus` names a concern to look at first,
never narrowing what may be reported.

In a change review, `--base` names the diff's start commit, the binding's base commit by default. An
unbound change review requires `--base`. That run judges the `HEAD` of the worktree it starts in,
such as the primary worktree, since that commit. It reads it from its [unbound
checkout](../../glossary.json#concept.unbound-checkout). A Module review has no base and refuses
`--base`.

For example, `code_review --modules module.issues` gives one reviewer these:

- The Issues Spec, code and tests.
- Read access to the rest of the project's code.
- The workspace's diff since its base.
- The checks of Issues and of the Modules that use it.

By contrast, `code_review --scope module --modules module.issues,module.tasks` gives each of the
two Modules its own reviewer of its whole code, with its own checks. Either way the Issues go to
the project's Issues, which the primary worktree keeps.

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | every reviewed Module reviewed and its Issues written, any verdict |
| `blocked` | `review_incomplete` | `decision` | a Module is `incomplete` only because its reviewer ended `blocked`, for example when it could not judge at all; one cause per incomplete Module |
| `failed` | `review_incomplete` | `decision` | a Module is `incomplete` for another cause: its grant, its reviewer failing, an audit-found change or a refusal of the Issue store; one cause per incomplete Module |
| `failed` | a code of the [worker sequence](../workers.md#errors-of-the-worker-sequence) | as that table gives | the change review's grant could not be computed, or the configured checks could not be started |
| `failed` | `no_base` | `input` | an unbound change review without `--base`, or a binding without a base commit |
| `failed` | `unresolved_base` | `input` | `--base` or the binding's base names no commit; Git's message as cause |
| `failed` | `base_in_module_scope` | `input` | `--base` given to a Module review, which has no diff |

When a run stops in steps 1 or 2, before it turns to any Module's reviewer, it carries no report.
It names as host evidence what those steps established:

- The base, once resolved.
- The diff's paths, once computed.
- The check results, once the checks ran.

Every other run carries the report, including for `blocked` and `failed`, even when no reviewer
could be launched. Thus, each Module's outcome and the findings of the Modules that were reviewed
are never lost. When its reviewer returned a summary, an incomplete Module keeps it. Once its
earlier Issues are read, it lists them as carried. The error of an incomplete Module is the
Operation's link for it, one of these:

- The worker sequence's own link, with the worker's below it when the worker ended `blocked` or
  `failed`. When the audit found a change, this link includes the audit's violations.
- `issues_unreadable` and `issues_unreported`, with the Issue store's error as cause.

In a change review, one reviewer judges every bound Module. In that case, a reviewer failure makes
every bound Module incomplete with that one link. When a finding's basis, location or Module does
not hold, it makes no Module incomplete. It is listed under its Module's `rejected` with the
reason, as host evidence names each failed check. The reviewer's other findings are reported.

The task handles the Issues as it handles a Spec review's, by their tier, as the
[main-session guidance](../../coordination/main-session/module.md#issues) says:

- It fixes an `obvious-fix` or `preferred-fix` Issue in later `implement` or `specify` work.
- It escalates a `decision-needed` one, every Spec challenge among them, by its identity.
- It leaves a `suggestion`.
- It closes each Issue the review lists as resolved.

## How it is built

The Operation is worker-backed, run by the
[Execution runner](../../glossary.json#concept.execution-runner) with
[task type](../../glossary.json#concept.task-type) `review-code`. A reviewer reads these:

- Its Modules' Spec context.
- Its Modules' external material.
- The whole project's implementation.

It writes nothing. A changed file no Module binds reaches it by name only. The diff is
[task context](../../glossary.json#concept.task-context). It adds no source. The Operation cuts it
to what the grant already makes readable. A change review launches one reviewer under the grant
of all bound Modules. A Module review launches one per Module, one after another, each under the
grant of its Module alone.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Change review: freeze the bound Modules' `review-code` [grant](../../glossary.json#concept.grant), resolve the base, diff base→worktree, untracked included, keeping readable paths' contents and listing the rest by name | Operation, Spec core | grant unavailable, no or unresolved base (`failed`) |
| 2 | Run the [configured checks](../../glossary.json#concept.configured-check) outside the worker: in a change review those of the bound Modules and of every Module that uses one of them, in a Module review those of each reviewed Module | Operation, Check execution | a check won't start (`failed`); a check that fails goes on to the reviewer |
| 3 | Per reviewer: read its Modules' [earlier Issues](#earlier-issues), then build [worker settings](../../glossary.json#concept.worker-settings), tools and [brief](../../glossary.json#concept.brief): scope, focus, the reviewed Module's documents and code files (Module review) or the diff and named-only paths (change review), its [check results](../../glossary.json#concept.check-result) with every log's path and the last part of every log that did not pass, the earlier Issues; the run's check logs stay readable to the reviewer besides its grant | Operation (Issues), Workers | Issues unreadable: its Modules `incomplete` |
| 4 | Launch the reviewer, await its [worker result](../../glossary.json#concept.worker-result); when a finding's Module, basis or location does not hold (step 6's check), resume it once with those citations to correct, its last result counting | Workers, worker | launch error, timeout, `blocked` or `failed`: its Modules `incomplete` |
| 5 | [Audit](../../glossary.json#concept.write-audit) the worktree (no writable path, so any change is a violation); write the [run record](../../glossary.json#concept.run-record) | Workers | any change: its Modules `incomplete` |
| 6 | Check every finding's Module, basis and locations in the last result | Operation, Spec core | — (a finding that still does not hold is rejected alone, with the reason) |
| 7 | Settle the earlier Issues; report every finding as an Issue, Module by Module | Operation (Issues) | a store refusal: that Module `incomplete`, its later findings unreported |
| 8 | Derive each Module's outcome and the verdict, and return the run's output | Operation, Execution runner | — |

A reviewer gets reading tools only:

- On Claude Code, Read, Glob and Grep.
- On pi, read, grep, find and ls, beside pi's tool for returning the worker result.

It gets no Edit, Write, Bash, web or MCP. Therefore, the Operation runs checks first and hands over
the results. A failing check is for the reviewer to interpret. It reads any check's full log at
the path the brief gives. A very large diff is cut short in the brief. The reviewer reads the
current contents of the remaining changed files through its grant. In that case, the base side of
the omitted part and the contents of deleted files are not available to it.

In bound and unbound runs alike, the Operation reports each finding through the Issue store as
one [Issue report](../../glossary.json#concept.issue-report). As Spec review does, it supplies its
provenance itself:

- `report_key` `<module>/<n>`, the finding's position among its Module's findings.
- The finding's tier, severity, title and impact.
- Its problem followed by its suggested repair as the description.
- The run, the scope, the kind, the cited basis and the quoted evidence as basis.
- The finding's Module as owner.
- Each location's file and the basis's document as evidence.

The report types follow these rules:

- Violations, missing tests and Spec challenges are `gap` reports of subtype
  `implementation-spec-mismatch`.
- Spec gaps are `gap` reports of subtype `missing-contract`.
- Defects and changes out of scope are `bug` reports.

A finding that names an earlier Issue is appended at the
[revision](../../glossary.json#concept.issue-revision) read just before. When a refusal of the Issue
store leaves a finding unreported, that finding keeps no `earlier` and the earlier Issue it named is
carried. A failure of the Issue system is never reported as an Issue. It stays an [error
chain](../../glossary.json#concept.error-chain) in the result. See the
[requirements](requirements.md) and [scenarios](scenarios.md) for the precise obligations.

Project review runs one Module review of a Module for each Module it covers, through the same
reviewer step, with its own [worker id](../../glossary.json#concept.worker-id) and the provenance
phase `code-review` for its reports.

<a id="realization.code-review.operation"></a>

The **Code review Operation** realization holds these:

- The Operation steps.
- The Issue reporting.
- The `review-code` worker instructions.
- The result schema and its tests.

The reviewer returns only findings, resolutions and a summary. The Operation adds the scope,
base, paths, check results, Issues, outcomes and verdict.

## What it relies on

- <a id="uses-operations"></a>**Operations**, Execution's Operation framework, is what `code_review`
  plugs into. Method registers its definition as an Operation that writes nothing and may run
  unbound. The definition names this Module as its provider
  ([Method](../module.md#the-operations-and-commands-it-provides)). Code review calls no other
  Operation. It relies on Method's review Issue helpers to read, settle and report its
  [earlier Issues](#earlier-issues) by the rules every review shares. It supplies only these:
  - Its own Operation.
  - The reason it gives a finding that names no Issue offered for its Module.
  - The Issue report of a finding.
- <a id="uses-execution"></a>**Execution**'s runner runs the Operation's steps:
  - It reads the [workspace binding](../../glossary.json#concept.workspace-binding).
  - It settles the Modules.
  - It records the run.
  - It wraps the report in the [run result](../../glossary.json#concept.run-result).

  Code review relies on it for these:
  - The binding's base commit, the default of `--base`.
  - The worktree the run started in, whose primary worktree keeps the Issues.
  - Recording the run.
- <a id="uses-workers"></a>**Workers**, in the worker harness, receives each frozen grant as data
  through Method's [standard worker sequence](../../glossary.json#concept.standard-worker-sequence).
  It does these:
  - Turns it into worker settings.
  - Launches each reviewer with this Module's instructions.
  - Collects its worker result.
  - Audits the worktree.
  - Writes the run record.
- <a id="uses-checks"></a>**Check execution** runs the configured checks the scope selects.
  It returns a check result for each, passed to the reviewer with its log path. The report carries
  each result in the shape its [contract](contracts.md#contract.code-review.review) gives, without
  the digests.
- <a id="uses-spec"></a>**Spec core** does these:
  - Computes the `review-code` grants.
  - Decides which changed paths the diff may show in full.
  - Lists a Module's documents and code files.
  - Resolves findings' basis identities.

  Code review never computes a boundary itself.
- <a id="uses-issues"></a>**Issues** is an
  [optional integration](../../glossary.json#concept.optional-integration). Where the issues part
  is installed, it keeps the project's Issues in the primary worktree, whichever worktree the run
  works in. Where it is not, the review reports its findings in its run result alone, as
  [Earlier Issues](#earlier-issues) says. Code review reaches Issues only through the issues part's
  [bookkeeping command](../../issues/interface.md#bookkeeping-command), `concorde issues`, never
  its code. It gives each report's provenance with `report --provenance`. Through that command,
  it relies on the store for these:
  - Listing a Module's open Issues with their latest
    [report](../../glossary.json#concept.issue-report) and
    [revision](../../glossary.json#concept.issue-revision).
  - Recording a new Issue or appending a report at the revision read, committing it before it
    answers.
  - Refusing a stale append rather than overwriting it.

  It relies on its [tiers](../../glossary.json#concept.issue-tier) for what a finding blocks.
  It relies on its [severities](../../glossary.json#concept.issue-severity) for how much a finding
  matters. When the store refuses, the Module is `incomplete`, with the store's error as the cause.
  The Operation never retries it. It never records it as an Issue.
