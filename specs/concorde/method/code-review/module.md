# Code review

## Purpose

Code review gives callers an independent judgement of code against the
[Specs](../../glossary.json#concept.spec) and records every problem it finds as an
[Issue](../../glossary.json#concept.issue) of the project where the issues part is installed, and
in its run result alone where it is not. It provides the `code_review`
[Operation](../../glossary.json#concept.operation), which judges in one of two scopes: a
**change review** judges a workspace's code changes since a base commit, and a **Module review**
judges each named [Module](../../glossary.json#concept.module)'s whole code against all of its
Specs. A reviewer worker reads the Specs, code and tests, changes nothing, and reports every problem
it can establish in one pass, each tied to the promise it judges the code against and to the code
that shows it; when code and Spec disagree it says which side is wrong, and may challenge a Spec
requirement it judges unreasonable or unrealizable. The Operation checks every finding's evidence,
reports each finding as an Issue where it can and derives the verdict from the tiers of what stands; acting on them
is later work of the task. The reviewer never edits a file or runs a command; the Operation's host
steps compute the diff and run the configured checks through Check execution, and leave the
workspace unchanged. A review without findings is evidence about the reviewed inputs only, not proof
of no other defect.

## Core concepts

### Two scopes

A **change review** (`--scope change`, the default) judges what a workspace changed: one reviewer
receives the diff from the base commit to the worktree and judges it against the bound Modules'
Specs, the usual review after `implement`. A **Module review** (`--scope module`) judges what a
Module is: one reviewer per named Module reads all of that Module's Specs and all of its code and
tests and judges whether the code is right, with no diff and no base. It suits a whole-Module check
after a large change, on code an earlier version wrote, or on a project whose code came before its
Specs. Both scopes share the reviewer's brief, the findings, the checks, the Issue reporting and the
report's shape.

### Findings and their evidence

Each **finding** names the reviewed Module it concerns, its kind, its
[severity](../../glossary.json#concept.issue-severity), its
[tier](../../glossary.json#concept.issue-tier), a title, the problem, its impact, its basis, the
code locations that show it, the evidence it quotes and a suggested repair. Its kind says which
side the reviewer judges wrong:

- the code: a **violation** of a stated promise, a **defect** the Spec's promises imply, a
  **missing test** for a scenario the reviewed code touches, or a change **out of scope**, outside
  the reviewed Modules' code;
- neither yet: a [Spec gap](../../glossary.json#concept.spec-gap), where the code does something
  the Spec neither requires nor forbids;
- the Spec: a **Spec challenge**, a requirement, scenario or contract the reviewer judges
  unreasonable or unrealizable, saying why, for example because two promises contradict each other
  or because what it requires cannot be observed or built with what the Module may use.

Every finding names its **basis**, a stable identity (requirement, scenario, contract or concept)
or a Spec passage from the reviewed Module's [Spec context](../../glossary.json#concept.spec-context),
the promise it is judged against, the passage that would have to settle a Spec gap or the passage a
Spec challenge disputes; and its **locations**, the files and lines of the project's code that show
it. The reviewer judges only against the Specs in its context, never against taste or another
Module's code, so a disputed finding traces to a written promise and to the code in question.

A finding's tier says who may act on it, as for every Issue: `suggestion` for code that keeps its
promises but could serve them better, and otherwise a blocking tier, `obvious-fix`,
`preferred-fix` or `decision-needed`. A Spec challenge is usually `decision-needed`, since changing
what a Module promises is decided above the task. Its severity says, independently, how much the
problem matters to the callers and the later tasks relying on the code, from `critical`, such as
wrong results or lost data, down to `low`, something cosmetic.

### Earlier Issues

A reviewed Module's **earlier Issues** are its open Issues one of whose reports a `code_review` run
made. The reviewer receives them before it judges, so that a problem already recorded is reported
again only when it changed, as a finding naming that Issue, never as a new one; it lists each
earlier Issue the code no longer has, with its reason, as **resolved**, and an earlier Issue it
neither names nor resolves still stands, **carried**. The Operation, never the reviewer, writes the
Issues: it appends a finding that names an earlier Issue to that Issue and records every other
finding as a new Issue. It closes none: the resolved Issues are listed in the report for the task
to close.

Earlier Issues exist only where the issues part is installed. Without it the review reads none,
reports nothing outside the run, keeps every finding in its report with its tier and severity, lists
no Issue as carried or resolved, and says in its report that its findings were not recorded as
Issues ([req.code-review.findings-as-issues](requirements.md#req.code-review.findings-as-issues)).

### The verdict

Each reviewed Module's **outcome** is `changes_required` when an Issue of a blocking tier stands for
it, reported by this review or carried from an earlier one — or, without the issues part, when this
review reports a finding of a blocking tier — `accepted` when none does, and `incomplete` when it
could not be reviewed or its Issues could not be written. The report's verdict
is `incomplete` when any Module is, else `changes_required` when any Module is, else `accepted`. The
Operation derives it itself from the tiers; it verifies what it can decide, that every basis and
location exists and which verdict follows, and otherwise keeps findings as the reviewer's claims.

### One pass

There is no [resume round](../../glossary.json#concept.resume-round): a reviewer reports every
blocking finding in one pass, since another round re-reads everything and lets one fix hide the
next — also why a review is not repeated automatically after `implement`.

## Overview

A review in three hands: the Operation prepares the code and the evidence, the reviewer judges it
once, the Operation checks the findings, reports them as Issues and settles the verdict, and the
task level acts on the Issues by their tier.

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
worktree it starts in. `--modules` names the reviewed Modules (the binding's by default; an
[unbound run](../../glossary.json#concept.unbound-run) must name them, or its grant cannot be
computed and it ends `failed` with `grant_unavailable`) and `--focus` a concern to look at first,
never narrowing what may be reported. In a change review `--base` names the diff's start commit
(the binding's base commit by default; required for an unbound run, which judges the `HEAD` of the
worktree it starts in, such as the primary worktree, since that commit, reading it from its
[unbound checkout](../../glossary.json#concept.unbound-checkout)); a Module review has no base
and refuses `--base`. For example, `code_review --modules module.issues` gives one reviewer the
Issues Spec, code and tests, read access to the rest of the project's code, the workspace's diff
since its base and the checks of Issues and of the Modules that use it, while
`code_review --scope module --modules module.issues,module.tasks` gives each of the two Modules its
own reviewer of its whole code, with its own checks. Either way the Issues go to the project's
Issues, which the primary worktree keeps.

| Status | Code | Reason | Detail |
| --- | --- | --- | --- |
| `ok` | — | — | every reviewed Module reviewed and its Issues written, any verdict |
| `blocked` | `review_incomplete` | `decision` | a Module is `incomplete` only because its reviewer ended `blocked`, for example when it could not judge at all; one cause per incomplete Module |
| `failed` | `review_incomplete` | `decision` | a Module is `incomplete` for another cause: its grant, its reviewer failing, an audit-found change, unresolved evidence or a refusal of the Issue store; one cause per incomplete Module |
| `failed` | a code of the [worker sequence](../workers.md#errors-of-the-worker-sequence) | as that table gives | the change review's grant could not be computed, or the configured checks could not be started |
| `failed` | `no_base` | `input` | an unbound change review without `--base`, or a binding without a base commit |
| `failed` | `unresolved_base` | `input` | `--base` or the binding's base names no commit; Git's message as cause |
| `failed` | `base_in_module_scope` | `input` | `--base` given to a Module review, which has no diff |

A run that stops in steps 1 or 2, before it turns to any Module's reviewer, carries no report and
names as host evidence what those steps established: the base once resolved, the diff's paths once
computed and the check results once the checks ran. Every other run carries the report, including
for `blocked` and `failed`, even when no reviewer could be launched, so each Module's outcome and the
findings of the Modules that were reviewed are never lost; an incomplete Module keeps its reviewer's
summary when one returned and lists its earlier Issues, once read, as carried. The error of an incomplete Module is
the Operation's link for it: the worker sequence's own link, with the worker's below it when the
worker ended `blocked` or `failed` and the audit's violations when it found a change,
`unresolved_evidence` naming every finding whose basis, location or
Module does not hold, or `issues_unreadable` and `issues_unreported` with the Issue store's error as
cause. In a change review, whose one reviewer judges every bound Module, a reviewer or evidence
failure makes every bound Module incomplete with that one link.

The task handles the Issues as it handles a Spec review's, by their tier, as the
[main-session guidance](../../coordination/main-session/module.md#issues) says: it fixes an
`obvious-fix` or `preferred-fix` Issue in later `implement` or `specify` work, escalates a
`decision-needed` one, every Spec challenge among them, by its identity, leaves a `suggestion`, and
closes each Issue the review lists as resolved.

## How it is built

The Operation is worker-backed, run by the
[Execution runner](../../glossary.json#concept.execution-runner) with
[task type](../../glossary.json#concept.task-type) `review-code`: a reviewer reads its Modules'
Spec context and external material and the whole project's implementation, and writes nothing; a
changed file no Module binds reaches it by name only. The diff is
[task context](../../glossary.json#concept.task-context): it adds no source, and the Operation
cuts it to what the grant already makes readable. A change review launches one reviewer under the
grant of all bound Modules; a Module review launches one per Module, one after another, each under
the grant of its Module alone.

| # | Step | Actor | Stops when |
| --- | --- | --- | --- |
| 1 | Change review: freeze the bound Modules' `review-code` [grant](../../glossary.json#concept.grant), resolve the base, diff base→worktree, untracked included, keeping readable paths' contents and listing the rest by name | Operation, Spec core | grant unavailable, no or unresolved base (`failed`) |
| 2 | Run the [configured checks](../../glossary.json#concept.configured-check) outside the worker: in a change review those of the bound Modules and of every Module that uses one of them, in a Module review those of each reviewed Module | Operation, Check execution | a check won't start (`failed`); a check that fails goes on to the reviewer |
| 3 | Per reviewer: read its Modules' [earlier Issues](#earlier-issues), then build [worker settings](../../glossary.json#concept.worker-settings), tools and [brief](../../glossary.json#concept.brief): scope, focus, the reviewed Module's documents and code files (Module review) or the diff and named-only paths (change review), its [check results](../../glossary.json#concept.check-result) with every log's path and the last part of every log that did not pass, the earlier Issues; the run's check logs stay readable to the reviewer besides its grant | Operation (Issues), Workers | Issues unreadable: its Modules `incomplete` |
| 4 | Launch the reviewer, await its [worker result](../../glossary.json#concept.worker-result) | Workers, worker | launch error, timeout, `blocked` or `failed`: its Modules `incomplete` |
| 5 | [Audit](../../glossary.json#concept.write-audit) the worktree (no writable path, so any change is a violation); write the [run record](../../glossary.json#concept.run-record) | Workers | any change: its Modules `incomplete` |
| 6 | Check every finding's Module, basis and locations | Operation, Spec core | any that does not hold: its Modules `incomplete`, nothing reported for them |
| 7 | Settle the earlier Issues; report every finding as an Issue, Module by Module | Operation (Issues) | a store refusal: that Module `incomplete`, its later findings unreported |
| 8 | Derive each Module's outcome and the verdict, and return the run's output | Operation, Execution runner | — |

A reviewer gets reading tools only — Read, Glob and Grep on Claude Code; read, grep, find and ls on
pi, beside pi's tool for returning the worker result — and no Edit, Write, Bash, web or MCP, so the
Operation runs checks first and hands over the results; a failing check is for the reviewer to
interpret, and it reads any check's full log at the path the brief gives. A very large diff is cut
short in the brief, and the reviewer reads the current contents of the remaining changed files
through its grant; the base side of the omitted part and the contents of deleted files are then not
available to it.

The Operation reports each finding through the Issue store as one
[Issue report](../../glossary.json#concept.issue-report), in bound and unbound runs alike, and
supplies its provenance itself, as Spec review does: `report_key` `<module>/<n>`, the finding's
position among its Module's findings; the finding's tier, severity, title and impact; its problem followed by
its suggested repair as the description; as basis the run, the scope, the kind, the cited basis and
the quoted evidence; the finding's Module as owner; and as evidence each location's file and the
basis's document. Violations, missing tests and Spec challenges are `gap` reports of subtype
`implementation-spec-mismatch`, Spec gaps `gap` of subtype `missing-contract`, defects and changes
out of scope `bug`. A finding that names an earlier Issue is appended at the
[revision](../../glossary.json#concept.issue-revision) read just before. A failure of the Issue
system is never reported as an Issue: it stays an
[error chain](../../glossary.json#concept.error-chain) in the result. See the
[requirements](requirements.md) and [scenarios](scenarios.md) for the precise obligations.

<a id="realization.code-review.operation"></a>

The **Code review Operation** realization holds the Operation steps, the Issue reporting, the
`review-code` worker instructions, the result schema and its tests: the reviewer returns only
findings, resolutions and a summary; the Operation adds the scope, base, paths, check results,
Issues, outcomes and verdict.

## What it relies on

- <a id="uses-operations"></a>**Operations**, Execution's Operation framework, is what `code_review`
  plugs into: Method registers its definition as an Operation that writes nothing and may run
  unbound, naming this Module as its provider
  ([Method](../module.md#the-operations-and-commands-it-provides)). Code review calls no other
  Operation. It relies on Method's review Issue helpers to read, settle and report its
  [earlier Issues](#earlier-issues) by the rules every review shares, supplying only its own
  Operation, the reason it gives a finding that names no Issue offered for its Module and the Issue
  report of a finding.
- <a id="uses-execution"></a>**Execution**'s runner runs the Operation's steps: it reads the
  [workspace binding](../../glossary.json#concept.workspace-binding), settles the Modules,
  records the run and wraps the report in the
  [run result](../../glossary.json#concept.run-result). Code review relies on it for the
  binding's base commit, the default of `--base`, for the worktree the run started in, whose
  primary worktree keeps the Issues, and for recording the run.
- <a id="uses-workers"></a>**Workers**, in the worker harness, receives each frozen grant as data
  through Method's [standard worker sequence](../../glossary.json#concept.standard-worker-sequence),
  turns it into worker settings, launches each reviewer with this Module's instructions, collects its worker result, audits the worktree and writes the
  run record.
- <a id="uses-checks"></a>**Check execution** runs the configured checks the scope selects and
  returns a check result for each, passed to the reviewer with its log path; the report carries each
  result in the shape its [contract](contracts.md#contract.code-review.review) gives, without the
  digests.
- <a id="uses-spec"></a>**Spec core** computes the `review-code` grants, decides which changed paths
  the diff may show in full, lists a Module's documents and code files and resolves findings' basis
  identities. Code review never computes a boundary itself.
- <a id="uses-issues"></a>**Issues** is an
  [optional integration](../../glossary.json#concept.optional-integration): where the issues part is
  installed, it keeps the project's Issues in the primary worktree, whichever worktree the run works
  in; where it is not, the review reports its findings in its run result alone, as
  [Earlier Issues](#earlier-issues) says. Code review reaches Issues only through the issues part's
  [bookkeeping command](../../issues/interface.md#bookkeeping-command), `concorde issues`, never its
  code, giving each report's provenance with `report --provenance`; it relies on its store, through
  that command, to list a Module's open Issues with
  their latest [report](../../glossary.json#concept.issue-report) and
  [revision](../../glossary.json#concept.issue-revision), to record a new Issue or append a
  report at the revision read, committing it before it answers, and to refuse a stale append rather
  than overwrite it; on its [tiers](../../glossary.json#concept.issue-tier) for what a
  finding blocks; and on its [severities](../../glossary.json#concept.issue-severity) for how
  much a finding matters. A refusal of the store makes the Module `incomplete`, with the store's error as
  the cause; the Operation never retries it and never records it as an Issue.
