# Issues

## Purpose

Issues keeps one durable, project-wide record of each concrete problem found while working on a
project, outliving the conversation, worker or task that found it: Issue records the primary
worktree keeps under `.concorde/issues/`, the open ones there and the closed ones in its `closed/`
folder, the store that alone writes them and commits each write on the primary branch, dispositions
closing or reopening one, and the bookkeeping command, whose actions the issues part also registers
as tools with the [project MCP server](../glossary.json#concept.project-mcp-server), that sessions
record, close, reopen, list, show and check them with. Every report carries a **[tier](../glossary.json#concept.issue-tier)** saying who
may handle the problem and a **[severity](../glossary.json#concept.issue-severity)** saying how much
it matters, so that work can start from the most severe Issues. Recording never stops the reporter, starts a repair or changes the outcome
of a task, and it grants nobody read/write access; Issues neither solves problems nor decides who
may close one — a task fixes an [Issue](../glossary.json#concept.issue) with ordinary work on its
[Module](../glossary.json#concept.module), and whoever disposes it answers for the evidence cited.
A failure of the Issue system itself is never recorded as an Issue.

Issues is the issues [part](../glossary.json#concept.part), and it depends on the
[Kernel](../kernel/module.md) alone: its records are [typed values](../glossary.json#concept.typed-value)
written through [file transactions](../glossary.json#concept.file-transaction), every write takes
the [merge lock](../glossary.json#concept.merge-lock) and every refusal is a link of the
[error chain](../glossary.json#concept.error-chain). Two features reach further, as
[optional integrations](../glossary.json#concept.optional-integration): an Issue's Module is checked
against the [registry](../glossary.json#concept.registry) only where the spec part is installed, and
is a plain label otherwise; and a write is refused while a task's merge is unfinished only where the
coordination part is installed, since without it there is no task merge to wait for. Which
Operations report Issues, and which task merges close them, are those parts' own integrations with
this one.

## Core concepts

### Issues and their reports

<a id="concept.issue"></a><a id="concept.issue-report"></a>

Each Issue is one file of the primary worktree, holding its reports, dispositions and status:
`.concorde/issues/I-<32 hex digits>.md` while it is open and `.concorde/issues/closed/I-<32 hex
digits>.md` once it is closed, so that the records seen directly in `.concorde/issues/` are the open
Issues. Its identity is unique in the project from the moment it is
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
[defect report](../glossary.json#concept.defect-report) handed to the
[Concorde repository](../glossary.json#concept.concorde-repository), and carry the whole
[error chain](../glossary.json#concept.error-chain). The observation's origin is distinct from the
provenance of the command that records it here.

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

Sessions record and read Issues with the bookkeeping command, directly or through the Issue tools
on the project MCP server, which go through the Issue store; the store relies on the Kernel for its
records, its file transactions and the merge lock, the command on Tracing for the error chains it
checks and prints; where they are installed, the command reads Spec core's registry for which
Modules exist and the store reads Tasks' [task records](../glossary.json#concept.task-record) for an unfinished merge, each through the
file its owner's Spec defines and never through that part's code, and Tasks closes through the
command the Issues a merged task resolves.

```d2
issues: Issues
kernel: Kernel
core: Spec core
tasks: Tasks
tracing: Tracing
session: Main session
issues -> kernel
issues -> tracing
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
[merge lock](../glossary.json#concept.merge-lock), publishes the record in the folder its status
names and commits that one record on the primary branch, in a commit of its own whose trailer
`Concorde-Issue` names the Issue, before it answers; a disposition that changes the status moves the
record into the other folder in that same commit; other changes of the primary worktree, staged or not, stay as they were. So the records are
versioned with the project and, once acknowledged, are committed; a write never lands between a
task's merge commit and the checks that decide whether the merge stays, and, where the
coordination part is installed, while a task's merge is unfinished no write is made at all.

Only committed records count. Every read takes the records of the primary worktree's last commit,
never its files, so a record is visible exactly when it is committed, and a receipt names a report
the commit holds. A write that fails after publishing its record puts it back before it refuses.
Only when that putting back fails, or the writing process is killed, does a record stay published
but not committed: no read shows it, and it is put back before any further write acts, as
[recovering uncommitted records](#recovering-uncommitted-records) explains.

### Recovering uncommitted records

Every write, holding the merge lock and before it reads the record it changes, looks for what an
earlier write published but did not commit: a record file of `.concorde/issues/` or its `closed/`
folder whose state, staged or not, differs from the last commit, and the temporary files of an
interrupted [file transaction](../glossary.json#concept.file-transaction). A record file that holds
a valid record of its Issue continuing the committed one, if any, with more reports or
dispositions, is what a write leaves behind: it is put back to its committed version, or removed
when no commit holds it, and the temporaries are removed. A write that moves a record between the
folders publishes it in one before it removes it from the other, so a committed record whose file
is gone while the other folder holds such a continuation is a move's leftover too: the record is
restored where it was committed and the new file removed. Nothing is committed in recovery, because a write that
gave no receipt recorded nothing: whoever made it was refused or never answered, and may repeat
it. Any other change of a record, such as a deleted, edited or invalid record, was made by no
write, so recovery leaves it as it is, and only a write of that very Issue is refused, with
`uncommitted_change`, until someone inspects and reverts it; writes of other Issues go on. Recovery
touches nothing outside `.concorde/issues/`, and nothing there but those records and temporaries.

`concorde issues recover` runs the same recovery without writing an Issue, and says what it put
back and which changes it left. The main agent runs it when such a record keeps the primary
worktree from being clean, as before a task's merge, or after a refusal with `recovery_failed`
once the cause the refusal names is fixed.

A task branch holds the copy of `.concorde/issues/`, both folders, of the commit it started from
and never changes it: a task that finds, fixes or closes a problem changes the primary worktree's records directly,
never its own copy, so a task branch brings no Issue change into its merge and Issue records never
conflict in Git.

### Lifecycle

An **Issue status** starts `open`. A **disposition**
records a decision to close or reopen it, with a reason, note, evidence and actor, and moves the
record into the folder of the new status in the same commit. `resolved`,
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

A record lies in the folder of its status: `.concorde/issues/` while open, `.concorde/issues/closed/`
once closed. A record that lies in the other folder is **misplaced**, such as a closed record
committed before closed Issues had a folder of their own or one moved by hand. It is still read,
listed, shown and written like any other, and a write leaves it in its place; `check` reports it,
and `concorde issues archive` moves every misplaced record into its place, unchanged, in one commit
under the merge lock. An Issue lives in exactly one place: one committed in both folders is refused
by every read until someone removes the copy that is not its whole history.

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

A failure of the Issue system itself, of its store, its bookkeeping command or its Issue tools, is
never reported as an Issue: an Issue system that failed cannot be trusted
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
is `python3 scripts/concorde.py issues`, which routes to the issues part's command entry, the one
`python3 scripts/issues.py` also runs. The issues part registers the same actions with the project MCP server as the tools `issue_list`,
`issue_show`, `issue_check`, `issue_report`, `issue_close` and `issue_reopen`, which answer and
refuse exactly as the command does; `recover` and `archive` are the command's alone. A session, the main agent or a [task session](../glossary.json#concept.task-session), uses
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
duplicate closure also needs `--duplicate-of <other-id>`. Each prints the record's revision and its
path, in `closed/` after a close and back in `.concorde/issues/` after a reopening. The command
records `main-agent` as actor;
the tools record the session. Each disposition needs a nonblank note and at least one evidence item.
The store validates their form and the transition; it does not establish that the evidence proves
the decision or that the actor had authority. Whoever disposes answers for that judgment. Closed
records remain readable in `closed/` and are never deleted by the store. The exact state rules are in the
[record interface](interface.md#record-file).

### Inspection and refusals

`list` prints a summary row per committed Issue that passes its filters, with its severity and
tier, by identity or, with `--sort severity` (the tool's `sort`), most severe first; `show <id>`
the complete committed record, its revision and its path, and `check` validates every record file
of the worktree it runs in, in both folders: in the primary worktree the project's Issues, in a
task worktree the copy its branch holds, which proves the branch's code still reads the records.
`recover` puts back what writes left uncommitted, and `archive` moves misplaced records into their
place. These commands never launch a model. The
[configured check](../glossary.json#concept.configured-check) `check.issues.store` runs `check`
whenever this Module's checks run; it fails malformed, misnamed, misplaced or inconsistent records,
an Issue recorded in both folders and, where the spec part is installed, open Issues with
unregistered owners, naming the repair of each, but only notes closed Issues with unregistered
owners. Validating the records is this check's, never `concorde spec-validation`'s, so the Spec
tooling knows nothing of Issues. An open
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
where the issues part contributes its section of that guidance, and the issues part registers the
command's actions as tools with the project MCP server, Distribution's host. Tasks relies on Issues to check
the Issues a task names as resolving and to close them when the task merges, which it does by
running `concorde issues close` for each, handing that process the merge lock it holds, as the
[interface](interface.md#disposing-under-a-held-lock) states.

For provenance the command asks Git for the reporting worktree's `HEAD` and records `null` when Git
fails.

<a id="uses-tracing"></a>

**Tracing** provides the Framework's
[error contract](../kernel/tracing/contracts.md#contract.tracing.error), on which the command relies twice:
it checks a report's `error_chain` against it, refusing one the contract does not accept, and it
prints every refusal as one `component` link of it, so that a session or run carries the refusal on
in its own error chain unchanged.

<a id="uses-kernel"></a>

The **Kernel** provides the [typed-value](../glossary.json#concept.typed-value) format Issues' shapes
register with, the [file transaction](../glossary.json#concept.file-transaction) a digest-bound
record publishes through, and the [merge lock](../glossary.json#concept.merge-lock) every write
holds or relies on its caller holding, as a merge closing the Issues its task resolves does once it
has closed the task. A stale transaction is refused, reported `stale_issue`, writing nothing. The
store's error type, `IssueError`, is Issues' own, with its own codes, and the command prints each of
its refusals as a `component` link, as the [interface](interface.md#store-operations) says.

<a id="uses-spec"></a>

**Spec core** is an [optional integration](../glossary.json#concept.optional-integration), reached
through its registry mirror alone, the [registry file](../spec-tooling/spec/contracts.md#registry-file)
`.concorde/specs.json` Spec core defines, never through the spec part's code:
the file itself tells whether the spec part is installed, a worktree without it having none. Where
it is there, the command reads the [registry](../glossary.json#concept.registry) for which Modules
exist, which is root, and which digest names a report's context: a report's owner must be a
registered Module, a `null` owner falls to the root Module, and the store check fails an open Issue
whose owner is not registered. Where it is not, a Module is a plain label: a report must name its
owner, which nothing checks, its context digest is that of no registry, and the store check judges
no owner and says, in a note, that the spec part is not installed.

<a id="uses-tasks"></a>

**Tasks** is an optional integration, reached through its
[task records](../coordination/tasks/contracts.md#contract.tasks.record) alone, never through
the coordination part's code. Where the coordination part is installed, Tasks records
[before its merge touches the primary branch](../coordination/tasks/requirements.md#req.tasks.merging-recorded)
that a task is `merging`, and before every write the store reads the records of the current tasks,
`.concorde/tasks/*/task.json`, and refuses the write with `merge_incomplete` while one is stored
`merging`, its message
[Tasks' account of that merge](../coordination/tasks/requirements.md#req.tasks.merge-incomplete-refused)
built from the record's `merging`: the merging task, its process and start, its commits, where the
primary branch is now and the `--resume` and `--abort` that finish it. A record that does not read
as JSON cannot be told `merging` and is passed over, Tasks refusing its own commands on it. Where
the coordination part is not installed there is no `.concorde/tasks/`, no task merge, and no write
waits for one. The primary worktree of any worktree of the repository the store finds through Git's
common directory itself, needing no part.

A merge that holds the merge lock and closes the Issues its task resolves through the bookkeeping
command hands the lock on to the command's process, as the Kernel's
[merge lock](../glossary.json#concept.merge-lock) allows: the command's write then adopts the lock
instead of waiting for it. That is the only way a write runs under a lock its caller holds; no
entry of the store skips taking the lock.

### Inside

<a id="realization.issues.store"></a>

**The Issue store** is the only code that creates, appends to, disposes or moves an Issue record,
and it never deletes a committed record: moving one between the folders removes it from one only
in the commit that adds it to the other. Each file holds one identity heading and one JSON record, so no prose
copy can drift from it, and reports are never rewritten: a later observation that classifies the
problem differently is a new report. Each write refuses a root that is not the primary worktree,
holds the merge lock, refuses while a task's merge is unfinished where the coordination part is
installed, puts back what earlier writes
left uncommitted, checks the revision its caller read against the committed record, publishes
through a [file transaction](../glossary.json#concept.file-transaction) in the folder of the
record's status, removes it from the other folder when it moves, syncs, and commits the record
alone, with the path it left, with `git commit --only`, so success means the record is committed
and a concurrent writer is never silently overwritten. A failure after publication, a commit Git refuses among
them, puts the record back as it was and refuses the write. Reads ask Git for the records of the
last commit, so they need no lock and see one commit's records at once. Identities are derived from
the reporting invocation and the reporter's key rather than counted, so no allocation state is
shared. Report and receipt shapes are [typed values](../glossary.json#concept.typed-value)
registered as `concorde-issue-report@3` and `concorde-issue-receipt@2`, which no other part
knows.

The view below follows one write and what each refusal leaves; every refusal before publication
leaves the record as it was committed.

```d2 illustrative
direction: down
check: "check the request\n(the report or disposition, the root)"
lock: "take the merge lock,\nor the caller holds it"
merge: "no task stored merging?"
recover: "put back what earlier\nwrites left uncommitted"
revision: "committed record at the\nrevision the caller read?"
publish: "publish through a file\ntransaction and sync"
commit: "git commit --only\nof the record"
done: "receipt or revision:\nthe record is committed"
putback: "put the record back"
refused: "refused: nothing written,\nthe committed record stands"
failed: "recovery_failed: the record\nstays uncommitted, no read\nshows it, the next write\nputs it back"
check -> lock
lock -> merge
merge -> recover: yes
recover -> revision
revision -> publish: yes
publish -> commit
commit -> done
check -> refused: invalid_issue, not_primary
lock -> refused: merge_busy
merge -> refused: merge_incomplete
recover -> refused: uncommitted_change
recover -> failed: a record not put back
revision -> refused: stale_issue, closed_issue, open_issue
publish -> putback: failure
commit -> putback: commit_failed
putback -> refused: put back
putback -> failed: putting back failed
```

<a id="realization.issues.command"></a>

**The bookkeeping command** is the sessions' face of the store — `report`/`close`/`reopen` write,
`recover` puts back, `archive` moves misplaced records, `list`/`show`/the store check read — kept in `src/concorde/issues/command.py` so that
its command line `src/concorde/issues/cli.py`, which `concorde issues` and `scripts/issues.py`
run, and the Issue tools `src/concorde/issues/tools.py` share every answer and refusal; the issues
part's [part registration](../glossary.json#concept.part-registration) names both. Where the spec part is
installed it reads the [registry](../glossary.json#concept.registry) for which Modules exist, which
is root, and which digest names a report's context; elsewhere a Module is a label. It supplies provenance rather than trusting report-file
claims; the report's optional `origin` describes a separate, cross-project observation. An owner
given as `null` falls to the root Module. Attribution as `main-agent` or `task-session` is a
convention of the command and the tools, not authentication: the library accepts provenance from its
caller. It is used by a model, which can only fix a request it understands, so every refusal names
the Issue, report file and field or argument and says what is wrong, passing the store's own errors
on unchanged. A part that may not import Issues' code, such as the method part's reviews, records
the reports of its own run through the command too, giving with `--provenance` the provenance it
vouches for, which the command records as given, as the store's library does for its callers.

The store check is this Module's own, `concorde issues check` and the tool `issue_check`, and its
configured check rather than part of Spec validation, so the Spec tooling stays unaware of Issues and
the records are still checked whenever this Module's checks run. An
open Issue with an unregistered owner fails it because nobody can be asked to solve it; a closed one
is only noted.

<a id="realization.issues.tests"></a>

The **Issues tests** cover the store on Git repositories (the merge lock, commits, concurrent
writers, malformed records, failed publications and commits, reads of committed records only,
recovery after failed and killed writes, moves between the folders and their recovery, archiving,
tiers, severities and the order by severity), every bookkeeping-command
action with its refusals, from the primary and a linked worktree, and the configured store check on
a fixture project.

<a id="realization.issues.guidance"></a>

The **Issues guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance), kept in `prompts/guidance/issues/` and
registered under `guidance` in the part's registration, which
[Distribution](../distribution/module.md#guidance-composition) composes after Coordination's working
method wherever the part is installed: the project skill's and the task-session prompt's "Issues":
recording, tiers, severities, fixing and failures of the Issue system. Each section says what
happens where a part it mentions is not installed.
