# Issues

## Purpose

Issues keeps one durable, project-wide record of each concrete problem found while working on a
project, outliving the conversation, worker or task that found it: Issue records the primary
worktree keeps under `.concorde/issues/`, the store that alone writes them and commits each write on
the primary branch, dispositions closing or reopening one, and the bookkeeping command, which the
[project MCP server](../glossary.json#concept.project-mcp-server) also presents, that sessions
record, close, reopen, list, show and check them with. Every report carries a **[tier](../glossary.json#concept.issue-tier)** saying who
may handle the problem and a **[severity](../glossary.json#concept.issue-severity)** saying how much
it matters, so that work can start from the most severe Issues. Recording never stops the reporter, starts a repair or changes the outcome
of a task, and it grants nobody read/write access; Issues neither solves problems nor decides who
may close one — a task fixes an [Issue](../glossary.json#concept.issue) with ordinary work on its
[Module](../glossary.json#concept.module), and whoever disposes it answers for the evidence cited.
A failure of the Issue system itself is never recorded as an Issue.

## Core concepts

### Issues and their reports

<a id="concept.issue"></a><a id="concept.issue-report"></a>

Each Issue is one file, `.concorde/issues/I-<32 hex digits>.md` of the primary worktree, holding its
reports, dispositions and status. Its identity is unique in the project from the moment it is
reported, because it is derived from the reporting invocation and the reporter's key and every
worktree writes the same store. Each report classifies the problem as a `bug`, a `gap` (an
implementation/[Spec](../glossary.json#concept.spec) mismatch, a Spec conflict or a missing promise)
or a `limitation`, and states it completely: its description, impact, basis and evidence, so that
whoever the Issue is escalated to, by its identity alone, can act on it. The latest report supplies
the current title, tier, severity, classification and owning Module. When that report's owner is `null`,
ownership falls to its reporting Module, the root Module for a command-recorded report. Appending a
new observation can therefore correct ownership, tier, severity or classification without rewriting
an earlier report. Ownership identifies the Module whose promise needs attention; it does not assign an agent or
grant permission to change that Module.

A report may name its **origin**, when the problem was seen in another project, such as a
[defect report](../glossary.json#concept.defect-report) handed to the Concorde
repository, and carry the whole [error chain](../glossary.json#concept.error-chain).
The observation's origin is distinct from the provenance of the command that records it here.

### Tiers

<a id="concept.issue-tier"></a>

A report's **tier** says whether AI may handle the problem without the level above it, the main
agent and then the developer. There are four, weakest first:

| Tier | Name | The problem | Who handles it |
| --- | --- | --- | --- |
| 1 | `suggestion` | none today, only a suggestion | whoever takes it up; nobody need |
| 2 | `obvious-fix` | obvious, and so is its fix | the session fixing it, alone |
| 3 | `preferred-fix` | simple, with several possible fixes of which one is clearly better | the session fixing it, which reports the fix it chose to the level above |
| 4 | `decision-needed` | unclear, or clear but with an uncertain fix | the level above decides before anyone fixes it |

A `suggestion` is advisory; the other three tiers are **blocking**. The reporter chooses the tier as
part of its observation, and a later report may change it like any other classification. Issues
records the tier and never acts on it: which session fixes an Issue, and when, is the
[main-session guidance](../coordination/main-session/module.md#issues)'s. Records written before
tiers existed hold reports without one; such an Issue has no tier until a tiered report is appended.

### Severities

<a id="concept.issue-severity"></a>

A report's **severity** says how much the problem matters: what goes wrong, and for whom, while it
stands. It is independent of the tier, which says who may handle the problem: an obvious fix may be
critical and a problem awaiting a decision low. There are four, most severe first:

| Severity | The problem's consequence while it stands |
| --- | --- |
| `critical` | wrong results, lost or corrupted data, a security exposure, or a core flow broken with no workaround |
| `high` | a main flow broken or wrong although a workaround exists, or a promise that leads the work relying on it to act wrongly |
| `medium` | a secondary flow or an edge case fails, or a gap that slows the work without misleading it |
| `low` | cosmetic, such as wording, naming or layout: nothing goes wrong |

The reporter chooses the severity as part of its observation, and a later report may change it like
the tier. Issues records the severity and acts on it only when asked to list by it: `list` sorted by
severity puts the most severe Issues first, so that whoever chooses what to fix next starts there.
Records written before severities existed hold reports without one; such an Issue has no severity,
and sorts after every Issue with one, until a report with a severity is appended.

### Issue revisions

<a id="concept.issue-revision"></a>

An [Issue revision](../glossary.json#concept.issue-revision) identifies
the exact file contents, independently of status: appending a report changes the revision while
leaving the Issue open. `show`, `report`, `close` and `reopen` return revisions. Appending uses the
revision its reporter read as `expected_revision`; `close` and `reopen` read the current revision
themselves and submit the disposition against that revision. Their CLI has no argument binding the
write to an earlier `show`. A concurrent change after the command's read is refused with
`stale_issue`. Read the Issue again, reconsider the action and retry against its current record;
never erase a concurrent report to make an old request succeed.

## Overview

### Structure

Sessions record and read Issues with the bookkeeping command, directly or through the project MCP
server, which goes through the Issue store; the store relies on Spec core for its records and on
Tasks for the primary worktree and its merge lock, and Tasks closes through the command the Issues a
merged task resolves.

```d2
issues: Issues
core: Spec core
tasks: Tasks
session: Main session
issues -> core
issues -> tasks
tasks -> issues
session -> issues
```

The store alone decides what a record may hold and when it is written, and the command adds what a
session must not be able to claim; everything else is ordinary work.

```d2
issues: Issues {
  store: Issue store {
    "store.py"
    "shapes.py"
  }
  command: Bookkeeping command {
    "command.py"
    "scripts/issues.py"
  }
  command -> store: records and reads Issues through
}
```

### Where Issues are kept

Issues are project-level: the primary worktree keeps them, like tasks, and every worktree of the
project, every session and every run reads and writes the same records. The store resolves the
primary worktree from any worktree of the repository, reads the records there and writes only
there. Each write holds the primary worktree's
[merge lock](../glossary.json#concept.merge-lock), publishes the record and commits that one file on
the primary branch, in a commit of its own whose trailer `Concorde-Issue` names the Issue, before it
answers; other changes of the primary worktree, staged or not, stay as they were. So the records are
versioned with the project and, once acknowledged, are committed; a write never lands between a
task's merge commit and the checks that decide whether the merge stays, and while a merge is
unfinished no write is made at all.

Only committed records count. Every read takes the records of the primary worktree's last commit,
never its files, so a record is visible exactly when it is committed, and a receipt names a report
the commit holds. A write that fails after publishing its record puts it back before it refuses.
Only when that putting back fails, or the writing process is killed, does a record stay published
but not committed: no read shows it, and it is put back before any further write acts, as
[recovering uncommitted records](#recovering-uncommitted-records) explains.

### Recovering uncommitted records

Every write, holding the merge lock and before it reads the record it changes, looks for what an
earlier write published but did not commit: a record file of `.concorde/issues/` whose state,
staged or not, differs from the last commit, and the temporary files of an interrupted
[file transaction](../glossary.json#concept.file-transaction). A record file that holds a valid
record of its Issue continuing the committed one, if any, with more reports or dispositions, is
what a write leaves behind: it is put back to its committed version, or removed when no commit
holds it, and the temporaries are removed. Nothing is committed in recovery, because a write that
gave no receipt recorded nothing: whoever made it was refused or never answered, and may repeat
it. Any other change of a record, such as a deleted, edited or invalid record, was made by no
write, so recovery leaves it as it is, and only a write of that very Issue is refused, with
`uncommitted_change`, until someone inspects and reverts it; writes of other Issues go on. Recovery
touches nothing outside `.concorde/issues/`, and nothing there but those records and temporaries.

`concorde issues recover` runs the same recovery without writing an Issue, and says what it put
back and which changes it left. The main agent runs it when such a record keeps the primary
worktree from being clean, as before a task's merge, or after a refusal with `recovery_failed`
once the cause the refusal names is fixed.

A task branch holds the copy of `.concorde/issues/` of the commit it started from and never changes
it: a task that finds, fixes or closes a problem changes the primary worktree's records directly,
never its own copy, so a task branch brings no Issue change into its merge and Issue records never
conflict in Git.

### Lifecycle

An **Issue status** starts `open`. A **disposition**
records a decision to close or reopen it, with a reason, note, evidence and actor. `resolved`,
`duplicate` and `not-actionable` are closing reasons, not extra statuses. The only statuses are
`open` and `closed`:

```d2 illustrative
direction: right
start: New report
open: open
closed: closed
start -> open: create
open -> open: append report
open -> closed: close (resolved, duplicate, not-actionable)
closed -> open: reopen (reopened)
```

| Action | Before | After | Meaning |
| --- | --- | --- | --- |
| Create | No record | `open` | The first report establishes the Issue. |
| Append report | `open` | `open` | Add an observation, preserving previous reports and dispositions. |
| Close as `resolved` | `open` | `closed` | The cited evidence supports that the problem is fixed. |
| Close as `duplicate` | `open` | `closed` | Another named, open Issue tracks the same problem. |
| Close as `not-actionable` | `open` | `closed` | The note and evidence explain why no repair is warranted. |
| Reopen | `closed` | `open` | Evidence calls the previous closure into question or shows recurrence. |

Only a disposition changes an existing Issue's status. Starting a repair, running checks or
delivering a task is not a disposition; there is no `in-progress` state. A duplicate closure changes
only the Issue being closed: its reports stay there, and later changes to the referenced Issue do not
propagate automatically. Reopening retains the identity and history; append a new observation
afterwards if the problem's description, tier, severity, classification or owner needs to change. A closed
Issue cannot receive a new report or close again, and an open one cannot reopen. Rejected actions
leave its record unchanged.

### A repair

Solving an Issue is ordinary work: a task for its current owning Module fixes it, and the task names
the Issues it resolves, with `concorde task open --resolves` or later `concorde task resolve`. The
fix reaches the primary branch with the task's merge, and only then is the problem solved there, so
[Tasks](../coordination/tasks/module.md) closes each named Issue that is still open as `resolved`,
with the merge commit as evidence, once the merge's checks have passed and while it still holds the
merge lock. A task that ends without merging closes nothing.

```d2 illustrative
direction: right
a: Task A {
  found: "a worker or Operation reports a problem A will not fix"
  record: "record it: the primary worktree commits the Issue at once"
  found -> record
}
primary: Primary branch {
  issue: "the Issue is open here"
  merge_b: "merge B: the fix arrives,\nthen the Issue's closure"
}
b: Repair task B {
  open: "open B for the Issue's owner,\nnaming it with --resolves"
  fix: fix and verify
  deliver: deliver B
  open -> fix -> deliver
}
a.record -> primary.issue
primary.issue -> b.open
b.deliver -> primary.merge_b
```

### Failures of the Issue system

A failure of the Issue system itself, of its store, its bookkeeping command or the project MCP
server's Issue tools, is never reported as an Issue: an Issue system that failed cannot be trusted
to record its own failure, and a session waiting for it to do so would wait for ever. Such a failure
travels as an [error chain](../glossary.json#concept.error-chain) instead, in the task's
[decision log](../glossary.json#concept.decision-log) and escalation for a session, or in its run's
result for a run. Every refusal whose reason is `environment`, such as a busy merge lock, an
unfinished merge, a failed commit or a file the operating system would not write, says so in its
options. A report about a design gap of Issues that the Issue system can still record, such as a
suggestion, is an ordinary Issue.

## Using Issues

### Sessions and Issues

The session that meets a problem decides whether it becomes an Issue, and the [main agent](../glossary.json#concept.main-agent) decides
when to dispose one. A worker's finding or an [Operation](../glossary.json#concept.operation)'s error
reaches the session in that run's result; neither creates or closes an Issue by itself unless the
Operation's own host records it through the store. A concrete problem the current task will not fix,
such as another Module's [Spec gap](../glossary.json#concept.spec-gap), is worth recording for later
work. Recording it does not clear a blocker, change a task's outcome, schedule a repair or notify
another session. Sessions discover recorded problems by reading `list` and `show`.

The bookkeeping command is the sessions' interface. In an installed project it is
`concorde issues` (`concorde` stands for `.concorde/bin/concorde`); in Concorde's source checkout it
is `python3 scripts/concorde.py issues`, which routes to `python3 scripts/issues.py`. The project
MCP server presents the same actions as the tools `issue_list`, `issue_show`, `issue_check`,
`issue_report`, `issue_close` and `issue_reopen`, which answer and refuse exactly as the command
does; `recover` is the command's alone. A session, the main agent or a [task session](../glossary.json#concept.task-session), uses
those tools because they record the calling session as reporter and actor, which the command cannot
know; the command serves a task session's shell and the runs it starts as well. Whichever worktree a
call starts from, it acts on the primary worktree's records.

### Recording and following up

Read `list` before recording, and `show <id>` for a possible match: a reporter appends to the Issue
already tracking its problem instead of creating another. `list` returns every Issue, open and
closed, unless it is filtered: `--status`, `--module`, `--tier` and `--severity` (the tool's
`status`, `module`, `tier` and `severity`) keep only the Issues with that status, concerning that
Module as owner or reporting Module, or of those tiers or severities, so `list --module <owner> --status open` reads the Issues a new report
about that Module could duplicate without reading the whole project's. A closed match may need
reopening: list the Module's closed Issues too when the problem may have been fixed before. Write
the report as JSON using the [report contract](interface.md#contract.issues.report), with its tier
and severity, then run
`concorde issues report --file <report.json> [--task <task-id>]` or call `issue_report`. The
command checks the owner against the primary worktree's registry, evidence paths in the worktree the
report is made in or the named origin, and any error chain; it supplies the reporter, reporting
Module, registry digest, task and Git `HEAD` itself. A successful reply gives a
[receipt](interface.md#contract.issues.receipt) naming that immutable report and the record's
revision. Keep it as the reference for follow-up. `report --check` checks the report without
recording it, useful before handing a defect report to another project.

What `list` and `show` found decides what the report carries:

- no matching Issue: omit `issue_id` and `expected_revision`, and the report creates an Issue;
- an open match: put its `issue_id`, and the revision `show` printed as `expected_revision`, and
  the report is appended to it;
- a closed match whose closure the new observation calls into question or shows recurring: `reopen`
  it first, then append as to an open match, with the revision `reopen` printed; otherwise record a
  new Issue.

Running a creation twice creates two Issues even when the
file and report key are unchanged: each command invocation has new provenance. The store's retry
handling applies only when a caller reuses the same invocation and report key, as the
[interface](interface.md#store-operations) explains; it does not deduplicate separate CLI runs.

### Closing and reopening

A fixed Issue is closed by the merge of the task that resolves it, as [a repair](#a-repair) shows.
Close one by hand only for another reason, or when it was fixed without such a task: use
`close <id> --reason <reason> --note <text> --evidence <item>...` or
`reopen <id> --note <text> --evidence <item>...`, or the tools `issue_close` and `issue_reopen`;
duplicate closure also needs `--duplicate-of <other-id>`. The command records `main-agent` as actor;
the tools record the session. Each disposition needs a nonblank note and at least one evidence item.
The store validates their form and the transition; it does not establish that the evidence proves
the decision or that the actor had authority. Whoever disposes answers for that judgment. Closed
records remain readable and are never deleted by the store. The exact state rules are in the
[record interface](interface.md#record-file).

### Inspection and refusals

`list` prints a summary row per committed Issue that passes its filters, with its severity and
tier, by identity or, with `--sort severity` (the tool's `sort`), most severe first; `show <id>`
the complete committed record and revision, and `check` validates every record file of the
worktree it runs in: in the primary worktree the project's Issues, in a task worktree the copy its
branch holds, which proves the branch's code still reads the records. `recover` puts back what
writes left uncommitted. These commands never launch a model. The
[configured check](../glossary.json#concept.configured-check) `check.issues.store` runs `check`
whenever this Module's checks run; it fails malformed, misnamed or inconsistent records and open
Issues with unregistered owners, but only notes closed Issues with unregistered owners. An open
Issue with a valid owner does not by itself fail this check; readiness to deliver work is a separate
decision.

An unknown Issue, stale revision, action on the wrong status, unregistered owner, missing report
evidence, busy merge lock, unfinished merge, failed commit, record that could not be put back or
record changed by hand is refused without committing a record or leaving one a read shows.
The error names the Issue, file, field or argument and gives a code and explanation so the caller
can correct the request. The exit status is 2 for an unusable request and 1 for a refused one; exact
shapes, actions and codes are in the [Issue interface](interface.md).

## How it is built

<a id="design"></a>

Issues' design has an outside, the Modules it relies on and those that rely on it, and an
inside, the store and the bookkeeping command that divide its work.

### Around it

No program but the store writes a record, and nobody edits one by hand. Main session declares
`session -> issues` in the [structure](#structure) diagram: its
[guidance](../coordination/main-session/module.md) says when sessions record, fix and close Issues,
and its project MCP server presents the command's actions as tools. Tasks relies on Issues to check
the Issues a task names as resolving and to close them when the task merges.

It follows the Framework's
[error contract](../tracing/contracts.md#contract.tracing.error): the command checks a report's
`error_chain` against it and prints every refusal as one link of it. For provenance the command
asks Git for the reporting worktree's `HEAD` and records `null` when Git fails.

<a id="uses-spec"></a>

**Spec core** provides the [typed-value](../glossary.json#concept.typed-value)
machinery Issues' shapes register with, the
[file transaction](../glossary.json#concept.file-transaction) a digest-bound
record publishes through, the [registry](../glossary.json#concept.registry)
the command reads for which Modules exist, and the
[error type](../spec-tooling/spec/errors.md) the store's `IssueError` extends with its own codes. A
stale transaction is refused, reported `stale_issue`, writing nothing.

<a id="uses-tasks"></a>

**Tasks** provides the primary worktree of any worktree of the repository, and its
[merge lock](../glossary.json#concept.merge-lock) with the rule that no primary-branch change is made
while a task's merge is unfinished. The store holds that lock for each write, or relies on its
caller holding it, as a merge closing the Issues its task resolves does.

### Inside

<a id="realization.issues.store"></a>

**The Issue store** is the only code that creates, appends to or disposes an Issue record, and it
never deletes a committed record. Each file holds one identity heading and one JSON record, so no prose
copy can drift from it, and reports are never rewritten: a later observation that classifies the
problem differently is a new report. Each write refuses a root that is not the primary worktree,
holds the merge lock, puts back what earlier writes left uncommitted, checks the revision its
caller read against the committed record, publishes through a
[file transaction](../glossary.json#concept.file-transaction), syncs, and commits the record alone
with `git commit --only`, so success means the record is committed and a concurrent writer is never
silently overwritten. A failure after publication, a commit Git refuses among them, puts the
record back as it was and refuses the write. Reads ask Git for the records of the last commit, so
they need no lock and see one commit's records at once.
Identities are derived from the reporting invocation and the reporter's key rather than counted, so
no allocation state is shared. Report and receipt shapes are
[typed values](../glossary.json#concept.typed-value) registered as
`concorde-issue-report@3` and `concorde-issue-receipt@1`, which Spec core does not know.

<a id="realization.issues.command"></a>

**The bookkeeping command** is the sessions' face of the store — `report`/`close`/`reopen` write,
`recover` puts back, `list`/`show`/the store check read — kept in `src/concorde/issues/command.py` so that
`scripts/issues.py` and the project MCP server's Issue tools share every answer and refusal. It
reads the [registry](../glossary.json#concept.registry) for which Modules exist, which is root, and
which digest names a report's context. It supplies provenance rather than trusting report-file
claims; the report's optional `origin` describes a separate, cross-project observation. An owner
given as `null` falls to the root Module. Attribution as `main-agent` or `task-session` is a
convention of the command and the tools, not authentication: the library accepts provenance from its
caller. It is used by a model, which can only fix a request it understands, so every refusal names
the Issue, report file and field or argument and says what is wrong, passing the store's own errors
on unchanged.

The store check is this Module's configured check rather than part of Spec validation, so Spec core
stays unaware of Issues and the records are still checked whenever this Module's checks run. An
open Issue with an unregistered owner fails it because nobody can be asked to solve it; a closed one
is only noted.

<a id="realization.issues.tests"></a>

The **Issues tests** cover the store on Git repositories (the merge lock, commits, concurrent
writers, malformed records, failed publications and commits, reads of committed records only,
recovery after failed and killed writes, tiers, severities and the order by severity), every bookkeeping-command
action with its refusals, from the primary and a linked worktree, and the configured store check on
a fixture project.
