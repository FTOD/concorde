# Issues

## Purpose

Issues keeps one durable, project-wide record of each concrete problem found while working on a
project. The record outlives whoever or whatever found the problem:

- The conversation.
- The worker.
- The task.

Issues covers these elements:

- Issue records that the primary worktree keeps under `.concorde/issues/`, with open records there
  and closed records in its `closed/` folder.
- The store that alone writes the records and commits each write on the primary branch.
- Dispositions that close or reopen an Issue.
- The bookkeeping command that sessions use to manage the records.

The issues part also registers the bookkeeping command's actions as tools with the
[project MCP server](../glossary.json#concept.project-mcp-server). Sessions use the command to:

- Record Issues.
- Close Issues.
- Reopen Issues.
- List Issues.
- Show Issues.
- Check Issues.

Every report carries a **[tier](../glossary.json#concept.issue-tier)** saying who may handle the
problem. Every report carries a **[severity](../glossary.json#concept.issue-severity)** saying how
much it matters, so that work can start from the most severe Issues. Recording never does any of
these things:

- Stop the reporter.
- Start a repair.
- Change the outcome of a task.
- Grant anybody read/write access.

Issues does not solve problems. Issues does not decide who may close an Issue.
A task fixes an [Issue](../glossary.json#concept.issue) with ordinary work on its
[Module](../glossary.json#concept.module). Whoever disposes the Issue answers for the evidence cited.
A failure of the Issue system itself is never recorded as an Issue.

Issues is the issues [part](../glossary.json#concept.part). It depends on the
[Kernel](../kernel/module.md) alone:

- Its report and receipt shapes are registered as
  [typed-value](../glossary.json#concept.typed-value) types.
- Its records are written through [file transactions](../glossary.json#concept.file-transaction).
- Every write takes the [merge lock](../glossary.json#concept.merge-lock).
- Every refusal is a link of the [error chain](../glossary.json#concept.error-chain).

Two features reach further, as [optional integrations](../glossary.json#concept.optional-integration).
Only where the spec part is installed, an Issue's Module is checked against the
[registry](../glossary.json#concept.registry). Otherwise, its Module is a plain label.
Only where the coordination part is installed, a write is refused while a task's merge is
unfinished. This is because without the coordination part there is no task merge to wait for.
Which Operations report Issues is those parts' own integration with this one.
Which task merges close Issues is those parts' own integration with this one.

## Core concepts

### Issues and their reports

<a id="concept.issue"></a><a id="concept.issue-report"></a>

Each Issue is one file of the primary worktree. The file holds:

- Its reports.
- Its dispositions.
- Its status.

While the Issue is open, its file is `.concorde/issues/I-<32 hex digits>.md`.
Once the Issue is closed, its file is `.concorde/issues/closed/I-<32 hex
digits>.md`. This placement ensures that the records seen directly in `.concorde/issues/` are the
open Issues. From the moment the Issue is reported, its identity is unique in the project for these
reasons:

- The identity is derived from the reporting invocation and the reporter's key.
- Every worktree writes the same store.

Each report classifies the problem as one of these:

- A `bug`.
- A `gap`.
- A `limitation`.

A `gap` is one of these:

- An implementation/[Spec](../glossary.json#concept.spec) mismatch.
- A Spec conflict.
- A missing promise.

Each report states the problem completely, so that whoever receives the escalated Issue can act
on it by its identity alone. The report states:

- The problem's description.
- The problem's impact.
- The problem's basis.
- The problem's evidence.

The latest report supplies the current values of:

- The title.
- The tier.
- The severity.
- The classification.
- The owning Module.

When that report's owner is `null`, ownership falls to its reporting Module.
For a command-recorded report, the reporting Module is the root Module.
Appending a new observation can therefore correct these values without rewriting an earlier
report:

- Ownership.
- Tier.
- Severity.
- Classification.

Ownership identifies the Module whose promise needs attention. Ownership does not assign an agent.
Ownership does not grant permission to change that Module.

When the problem was seen in another project, a report may name its **origin**.
An example is a [defect report](../glossary.json#concept.defect-report) handed to the
[Concorde repository](../glossary.json#concept.concorde-repository).
A report may carry the whole [error chain](../glossary.json#concept.error-chain).
The observation's origin is distinct from the provenance of the command that records it here.

### Tiers

<a id="concept.issue-tier"></a>

A report's **tier** says whether AI may handle the problem without the level above it.
The levels above are the main agent and then the developer. There are four tiers, weakest first:

| Tier | Name | The problem | Who handles it |
| --- | --- | --- | --- |
| 1 | `suggestion` | none today, only a suggestion | whoever takes it up; nobody need |
| 2 | `obvious-fix` | obvious, and so is its fix | the session fixing it, alone |
| 3 | `preferred-fix` | simple, with several possible fixes of which one is clearly better | the session fixing it, which reports the fix it chose to the level above |
| 4 | `decision-needed` | unclear, or clear but with an uncertain fix | the level above decides before anyone fixes it |

A `suggestion` is advisory. The other three tiers are **blocking**. The reporter chooses the tier
as part of its observation. A later report may change the tier like any other classification.
Issues records the tier. Issues never acts on the tier.
The [main-session guidance](../coordination/main-session/module.md#issues) determines which session
fixes an Issue and when. Records written before tiers existed hold reports without one.
Until a tiered report is appended, such an Issue has no tier.

### Severities

<a id="concept.issue-severity"></a>

A report's **severity** says how much the problem matters: what goes wrong, and for whom, while it
stands. Severity is independent of the tier, which says who may handle the problem.
An obvious fix may be critical. A problem awaiting a decision may be low.
There are four severities, most severe first:

| Severity | The problem's consequence while it stands |
| --- | --- |
| `critical` | wrong results, lost or corrupted data, a security exposure, or a core flow broken with no workaround |
| `high` | a main flow broken or wrong although a workaround exists, or a promise that leads the work relying on it to act wrongly |
| `medium` | a secondary flow or an edge case fails, or a gap that slows the work without misleading it |
| `low` | cosmetic, such as wording, naming or layout: nothing goes wrong |

The reporter chooses the severity as part of its observation. A later report may change the
severity like the tier. Issues records the severity. When asked to list by severity, Issues
acts on it, and only then. `list` sorted by severity puts the most severe Issues first, so that whoever chooses
what to fix next starts there. Records written before severities existed hold reports without one.
Until a report with a severity is appended, such an Issue has these properties:

- It has no severity.
- It sorts after every Issue with a severity.

### Issue revisions

<a id="concept.issue-revision"></a>

An [Issue revision](../glossary.json#concept.issue-revision) identifies the exact file contents,
independently of status. Appending a report changes the revision while leaving the Issue open.
These actions return revisions:

- `show`.
- `report`.
- `close`.
- `reopen`.

Appending uses the revision its reporter read as `expected_revision`.
`close` and `reopen` read the current revision themselves. These actions submit the disposition
against that revision. Their CLI has no argument binding the write to an earlier `show`.
When a concurrent change follows the command's read, the write is refused with
`stale_issue`. Follow these steps:

- Read the Issue again.
- Reconsider the action.
- Retry against its current record.

Never erase a concurrent report to make an old request succeed.

## Overview

### Structure

Sessions record and read Issues with the bookkeeping command, directly or through the Issue tools
on the project MCP server. The command and tools go through the Issue store.
The store relies on the Kernel for:

- Its records.
- Its file transactions.
- The merge lock.

The command relies on Tracing for the error chains it checks and prints.
Where Spec core is installed, the command reads Spec core's registry for which Modules exist.
The command reads the registry through the file that Spec core's Spec defines.
Where Tasks is installed, the store reads Tasks' [task records](../glossary.json#concept.task-record)
for an unfinished merge. The store reads the task records through the file that Tasks' Spec defines.
Neither reads through that part's code. Through the command, Tasks closes the Issues a merged task
resolves.

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

The store alone decides what a record may hold. The store alone decides when a record is written.
The command adds what a session must not be able to claim. Everything else is ordinary work.

```d2
issues: Issues {
  store: Issue store {
    "store.py"
    "shapes.py"
  }
  command: Bookkeeping command {
    "command.py"
    "cli.py"
    "tools.py"
    "scripts/issues.py"
  }
  command -> store: records and reads Issues through
}
```

The command has two faces: its command line and the Issue tools. Both run the same actions.
This is why a tool answers and refuses exactly as the command does:

```d2 illustrative
direction: right
shell: "concorde issues,\nscripts/issues.py"
server: "project MCP server"
cli: "cli.py\n(command line)"
tools: "tools.py\n(Issue tools)"
actions: "command.py\n(the actions)"
store: "Issue store"
shell -> cli
server -> tools
cli -> actions: runs
tools -> actions: calls with the same arguments
actions -> store
```

### Where Issues are kept

Issues are project-level. The primary worktree keeps them, like tasks. The following read and
write the same records:

- Every worktree of the project.
- Every session.
- Every run.

From any worktree of the repository, the store resolves the primary worktree. The store reads the
records there. It writes only there. Before it answers, each write holds the primary worktree's
[merge lock](../glossary.json#concept.merge-lock) throughout these steps:

- It publishes the record in the folder its status names.
- It commits that one record on the primary branch in a commit of its own.

That commit's trailer `Concorde-Issue` names the Issue. When a disposition changes the status, it
moves the record into the other folder in that same commit. An archive commits the records it
moves, and only them, in one commit. Other changes of the primary worktree, staged or not, stay as
they were. So the records are versioned with the project. So, once acknowledged, the records are
committed. A write never lands between a task's merge commit and the checks that decide whether
the merge stays. Where the coordination part is installed, no write occurs while a task's merge
is unfinished.

Only committed records count. Every read takes the records of the primary worktree's last commit,
never its files. So a record is visible exactly when it is committed. A receipt names a report
the commit holds. A write that fails after publishing its record puts it back before it refuses.
A record stays published but not committed only when that putting back fails or the writing
process is killed. In that case, no read shows the record. Before any further write acts, the
record is put back, as [recovering uncommitted records](#recovering-uncommitted-records) explains.

### Recovering uncommitted records

While holding the merge lock, every write looks for what an earlier write published but did not
commit. This happens before the write reads the record it changes. The write looks for:

- A record file of `.concorde/issues/` or its `closed/` folder whose state, staged or not, differs
  from the last commit.
- The temporary files of an interrupted [file transaction](../glossary.json#concept.file-transaction).

A write leaves behind a record file that holds a valid record of its Issue with more reports or
dispositions. If a committed record exists, that valid record continues it. Such a file is put
back to its committed version. When no commit holds it, the file is removed instead. The
temporaries are removed. When a write moves a record between the folders, it publishes the record
in one before it removes the record from the other. So a move's leftover also occurs when both
these conditions hold:

- A committed record's file is gone.
- The other folder holds such a continuation.

In that case, the record is restored where it was committed. The new file is removed. Nothing is
committed in recovery, because a write that left an uncommitted record gave no receipt and
recorded nothing. Whoever made that write was refused or never answered, and may repeat it.
When a write is killed after its commit, it did record its report. The same holds when its answer
was lost after its commit. So a caller left without an answer reads `list` or `show` before it
repeats a creation. Any other change of a record was made by no write. Such changes include:

- A deleted record.
- An edited record.
- An invalid record.

So recovery leaves such a change as it is. Until someone inspects and reverts it, only a write of
that very Issue is refused, with `uncommitted_change`. Writes of other Issues go on. Recovery
touches nothing outside `.concorde/issues/`. Within that folder, recovery touches nothing but
those records and temporaries.

`concorde issues recover` runs the same recovery without writing an Issue. It says what it put
back and which changes it left. When such a record keeps the primary worktree from being clean,
the main agent runs it, as before a task's merge. After a refusal with `recovery_failed`, once the
cause the refusal names is fixed, the main agent also runs it.

A task branch holds the copy of `.concorde/issues/`, both folders, of the commit it started from.
The task branch never changes that copy. When a task does any of the following, it changes the
primary worktree's records directly, never its own copy:

- Finds a problem.
- Fixes a problem.
- Closes a problem.

So a task branch brings no Issue
change into its merge. For the same reason, Issue records never conflict in Git.

### Lifecycle

An **Issue status** starts `open`. A **disposition** records a decision to close or reopen it,
with these details:

- A reason.
- A note.
- Evidence.
- An actor.

The disposition moves the record into the folder of the new status in the same commit. The
following are closing reasons, not extra statuses:

- `resolved`.
- `duplicate`.
- `not-actionable`.

The only statuses are `open` and `closed`:

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

Only a disposition changes an existing Issue's status. None of the following is a disposition:

- Starting a repair.
- Running checks.
- Delivering a task.

There is no `in-progress` state. A duplicate closure changes only the Issue being closed. Its
reports stay there. Later changes to the referenced Issue do not propagate automatically.
Reopening retains the identity and history. After reopening, append a new observation if any of
these needs to change:

- The problem's description.
- The problem's tier.
- The problem's severity.
- The problem's classification.
- The problem's owner.

A closed Issue cannot receive a new report or close again. An open Issue cannot reopen. Rejected
actions leave its record unchanged.

A record lies in the folder of its status. While open, it lies in `.concorde/issues/`. Once closed,
it lies in `.concorde/issues/closed/`. A record that lies in the other folder is **misplaced**.
Examples include a closed record committed before closed Issues had a folder of their own or a
record moved by hand. Like any other record, a misplaced record is:

- Read.
- Listed.
- Shown.
- Written.

A write of a misplaced record moves it into the folder of its status in that write's commit. `check` reports a misplaced record. Under the merge lock,
`concorde issues archive` moves every misplaced record into its place, unchanged, in one commit.
An Issue lives in exactly one place. Until someone removes the copy that is not its whole
history, every read refuses an Issue committed in both folders.

### A repair

Solving an Issue is ordinary work. A task for its current owning Module fixes it. The task names
the Issues it resolves, with `concorde task open --resolves` or later `concorde task resolve`.
The fix reaches the primary branch with the task's merge. Only then is the problem solved there.
So, after the merge's checks pass, [Tasks](../coordination/tasks/module.md), still holding the
merge lock, closes each named Issue still open as `resolved`.
Tasks uses the merge commit as evidence for that closure. A task that ends without merging
closes nothing.

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

A failure of any of the following is never reported as an Issue:

- The Issue system itself.
- Its store.
- Its bookkeeping command.
- Its Issue tools.

This is because an Issue system that failed cannot be trusted to record its own failure.
Another reason is that a session waiting for it to do so would wait for ever. Such a failure travels as an
[error chain](../glossary.json#concept.error-chain) instead. For a session, it travels in the
task's [decision log](../glossary.json#concept.decision-log) and escalation. For a run, it travels
in that run's result. Every refusal whose reason is `environment` says so in its options.
Examples include:

- A busy merge lock.
- An unfinished merge.
- A failed commit.
- A file the operating system would not write.

When the Issue system can still record a report about a design gap of Issues, that report is an
ordinary Issue, such as a suggestion.

## Using Issues

### Sessions and Issues

The session that meets a problem decides whether it becomes an Issue.
The [main agent](../glossary.json#concept.main-agent) decides when to dispose one.
A worker's finding or an [Operation](../glossary.json#concept.operation)'s error reaches the session
in that run's result. Unless the Operation's own host records it through the store, neither creates
or closes an Issue by itself. A concrete problem the current task will not fix, such as another
Module's [Spec gap](../glossary.json#concept.spec-gap), is worth recording for later work.
Recording it does none of the following:

- Clear a blocker.
- Change a task's outcome.
- Schedule a repair.
- Notify another session.

Sessions discover recorded problems by reading `list` and `show`.

The bookkeeping command is the sessions' interface. In an installed project it is
`concorde issues` (`concorde` stands for `.concorde/bin/concorde`). In Concorde's source checkout it
is `python3 scripts/concorde.py issues`. This routes to the issues part's command entry, the one
`python3 scripts/issues.py` also runs. The issues part registers the same actions with the project
MCP server as these tools:

- `issue_list`
- `issue_show`
- `issue_check`
- `issue_report`
- `issue_close`
- `issue_reopen`

These tools answer and refuse exactly as the command does. `recover` and `archive` are the
command's alone. A session, either the main agent or a [task session](../glossary.json#concept.task-session), uses those tools.

The reason is that the tools record the calling session as reporter and actor, which the command
cannot know. The command serves a task session's shell and the runs it starts as well. Whichever
worktree a call starts from, it acts on the primary worktree's records.

### Recording and following up

Read `list` before recording. For a possible match, read `show <id>`.
A reporter appends to the Issue already tracking its problem instead of creating another.
Unless it is filtered, `list` returns every Issue, open and closed. These filters keep only the
Issues that match:

- `--status` (the tool's `status`) keeps Issues with that status.
- `--module` (the tool's `module`) keeps Issues concerning that Module as owner or reporting Module.
- `--tier` (the tool's `tier`) keeps Issues of those tiers.
- `--severity` (the tool's `severity`) keeps Issues of those severities.

Thus, `list --module <owner> --status open` reads the Issues a new report about that Module could
duplicate without reading the whole project's. A closed match may need reopening. When the problem
may have been fixed before, list the Module's closed Issues too. Write the report as JSON using the
[report contract](interface.md#contract.issues.report), with its tier and severity. Then run
`concorde issues report --file <report.json> [--task <task-id>]` or call `issue_report`.
The command checks the following:

- The owner against the primary worktree's registry.
- Evidence paths in the worktree the report is made in or the named origin.
- Any error chain.

The command supplies the following itself:

- The reporter.
- The reporting Module.
- The registry digest.
- The task.
- Git `HEAD`.

A successful reply gives a [receipt](interface.md#contract.issues.receipt) naming that immutable
report and the record's revision. Keep it as the reference for follow-up. `report --check` checks
the report without recording it. This is useful before handing a defect report to another project.
For a report with an `origin`, this check does not resolve its reporting Module.
The project recording the report resolves its reporting Module.

What `list` and `show` found decides what the report carries:

- When no matching Issue exists, omit `issue_id` and `expected_revision`. The report creates an
  Issue.
- For an open match, put its `issue_id` and the revision `show` printed as `expected_revision`.
  The report is appended to that Issue.
- When a new observation calls a closed match's closure into question or shows recurrence,
  `reopen` the Issue first. Then append as to an open match, with the revision `reopen` printed.
  Otherwise, record a new Issue.

Even when the file and report key are unchanged, running a creation twice creates two Issues.
This is because each command invocation has new provenance. The store's retry handling applies
only when a caller reuses the same invocation and report key, as the
[interface](interface.md#store-operations) explains. The store's retry handling does not
deduplicate separate CLI runs.

### Closing and reopening

A fixed Issue is closed by the merge of the task that resolves it, as [a repair](#a-repair) shows.
Close an Issue by hand only for another reason, or when it was fixed without such a task.
Use one of the following:

- `close <id> --reason <reason> --note <text> --evidence <item>...`
- `reopen <id> --note <text> --evidence <item>...`
- The tool `issue_close`.
- The tool `issue_reopen`.

For duplicate closure, also supply `--duplicate-of <other-id>`. Each prints the record's revision
and its path. After a close, the path is in `closed/`. After a reopening, the path is back in
`.concorde/issues/`. The command records `main-agent` as actor.
The tools record the session. Each disposition needs a nonblank note and at least one evidence item.
The store validates their form and the transition. The store does not establish that the evidence
proves the decision or that the actor had authority. Whoever disposes answers for that judgment.
Closed records remain readable in `closed/`. The store never deletes closed records. The exact
state rules are in the [record interface](interface.md#record-file).

### Inspection and refusals

For each committed Issue that passes its filters, `list` prints a summary row with its severity
and tier. With `--sort severity` (the tool's `sort`), it prints most severe first.
Otherwise, it prints by identity. `show <id>` prints the following:

- The complete committed record.
- Its revision.
- Its path.

`check` validates every record file of the worktree it runs in, in both folders:

- In the primary worktree, it validates the project's Issues.
- In a task worktree, it validates the copy its branch holds.

The task-worktree validation proves the branch's code still reads the records.
`recover` puts back what writes left uncommitted. `archive` moves misplaced records into their
place. These commands never launch a model. Whenever this Module's checks run, the
[configured check](../glossary.json#concept.configured-check) `check.issues.store` runs `check`.
It fails the following, naming the repair of each:

- Malformed records.
- Misnamed records.
- Misplaced records.
- Inconsistent records.
- An Issue recorded in both folders.
- Where the spec part is installed, open Issues with unregistered owners.

It only notes closed Issues with unregistered owners. Validating the records is this check's,
never `concorde spec-validation`'s. For this reason, the Spec tooling knows nothing of Issues.
An open Issue with a valid owner does not by itself fail this check.
Readiness to deliver work is a separate decision.

The following are refused without committing a record or leaving one a read shows:

- An unknown Issue.
- A stale revision.
- An action on the wrong status.
- An unregistered owner.
- Missing report evidence.
- A busy merge lock.
- An unfinished merge.
- An unreadable task record.
- A failed commit.
- A record that could not be put back.
- A record changed by hand.

The error names what applies from this list:

- The Issue.
- The file.
- The field.
- The argument.

The error gives a code and explanation so the caller can correct the request.
For an unusable request, the exit status is 2. For a refused request, the exit status is 1.
The [Issue interface](interface.md) gives the exact details:

- Shapes.
- Actions.
- Codes.

## How it is built

<a id="design"></a>

Issues' design has an outside: the Modules it relies on and those that rely on it.
Its design has an inside: the store and the bookkeeping command that divide its work.
### Around it

No program but the store writes a record. Nobody edits one by hand. Main session declares
`session -> issues` in the [structure](#structure) diagram. Its
[guidance](../coordination/main-session/module.md) says when sessions do the following:

- Record Issues.
- Fix Issues.
- Close Issues.

The issues part contributes its section of that guidance. The issues part registers the command's
actions as tools with the project MCP server, Distribution's host. Tasks relies on Issues to check
the Issues a task names as resolving. When the task merges, Tasks relies on Issues to close those
Issues. Tasks does this by running `concorde issues close` for each Issue. Tasks hands that process
the merge lock it holds, as the [interface](interface.md#disposing-under-a-held-lock) states.

For provenance the command asks Git for the reporting worktree's `HEAD`. When Git fails, the
command records `null`.

<a id="uses-distribution"></a>

**Distribution** is the installation host present in every installation. It installs the issues
part from its [part registration](../glossary.json#concept.part-registration). The
[registration contract](../distribution/contracts.md#contract.distribution.part-registration)
defines this plain data:

- The `issues` command.
- The `issue_*` tools.
- The typed value types of reports and receipts.
- The part's guidance sections.
- `scripts/issues.py`.

Issues relies on Distribution routing the command to its entry. Issues also relies on the
[project MCP server](../glossary.json#concept.project-mcp-server) answering each tool call with a
fresh process of the primary worktree's Concorde. Issues also relies on the server returning its
answer or refusal unchanged. Because of this routing and tool-call behavior, a session's tool call and its shell's
`concorde issues` write the same records under the same lock. Issues imports nothing of Distribution.

<a id="uses-tracing"></a>

**Tracing** provides the Framework's
[error contract](../kernel/tracing/contracts.md#contract.tracing.error). The command relies on it
twice. The command checks a report's `error_chain` against the contract. When the contract does
not accept a report, the command refuses it. The command prints every refusal as one `component`
link of the contract. The command does this so that a session or run carries the refusal on in
its own error chain unchanged.

<a id="uses-kernel"></a>

The **Kernel** provides the following:

- The [typed-value](../glossary.json#concept.typed-value) format Issues' shapes register with.
- The [file transaction](../glossary.json#concept.file-transaction) a digest-bound record publishes
  through.
- The [merge lock](../glossary.json#concept.merge-lock) every write holds or relies on its caller
  holding. A write relies on its caller holding the lock when a merge that has closed its task
  closes the Issues its task resolves.

When a transaction is stale, it is refused. The refusal reports `stale_issue`. The transaction
writes nothing. The store's error type,
`IssueError`, is Issues' own. It has its own codes. The command prints each of the store's refusals
as a `component` link, as the [interface](interface.md#store-operations) says.

<a id="uses-spec"></a>

**Spec core** is an [optional integration](../glossary.json#concept.optional-integration).
Issues reaches it through its registry mirror alone, never through the spec part's code. This
mirror is the [registry file](../spec-tooling/spec/contracts.md#registry-file)
`.concorde/specs.json` Spec core defines. The file itself tells whether the spec part is installed.
A worktree without the file has no spec part. Where the file is present, the command reads the
[registry](../glossary.json#concept.registry) for the following:

- Which Modules exist.
- Which Module is root.
- Which digest names a report's context.

In that case, the following applies:

- A report's owner must be a registered Module.
- A `null` owner falls to the root Module.
- The store check fails an open Issue whose owner is not registered.

Where the file is absent, a Module is a plain label. In that case, the following applies:

- A report must name its owner.
- Nothing checks that owner.
- The report's context digest is that of no registry.
- The store check judges no owner.
- The store check says, in a note, that the spec part is not installed.

When `report --check` checks a report with an `origin` before handoff to another project, it
resolves no reporting Module either way. The project that records the report resolves a reporting
Module, so the report's `null` owner is never refused here.

<a id="uses-tasks"></a>

**Tasks** is an optional integration. Issues reaches it through its
[task records](../coordination/tasks/contracts.md#contract.tasks.record) alone, never through the
coordination part's code. Where the coordination part is installed, the following applies:

- Tasks records that a task is `merging`
  [before its merge touches the primary branch](../coordination/tasks/requirements.md#req.tasks.merging-recorded).
- Before every write, the store reads the records of the current tasks,
  `.concorde/tasks/*/task.json`.
- While one task is stored `merging`, the store refuses the write with `merge_incomplete`.
  Its message is
  [Tasks' account of that merge](../coordination/tasks/requirements.md#req.tasks.merge-incomplete-refused),
  built from the record's `merging`. The message names the following:
  - The merging task.
  - Its process and start.
  - Its commits.
  - Where the primary branch is now.
  - The `--resume` and `--abort` that finish it.
- A record that does not read as a JSON object cannot be told not to be `merging`.
  That record may be the very record of the merge.
  For these reasons, until the main agent repairs the record, the store refuses the write with
  `unreadable_task_record`. This is an environment refusal naming the record, as Tasks refuses its
  own commands on it.

Where the coordination part is not installed, the following applies:

- There is no `.concorde/tasks/`.
- There is no task merge.
- No write waits for a task merge.

The store itself finds the primary worktree of any worktree of the repository through Git's common
directory. This needs no part.

For a merge that holds the merge lock and closes the Issues its task resolves through the
bookkeeping command, the following applies:

- The merge hands the lock on to the command's process, as the Kernel's
  [merge lock](../glossary.json#concept.merge-lock) allows.
- The command's write then adopts the lock instead of waiting for it.

That is the only way a write runs under a lock its caller holds.
No entry of the store skips taking the lock.

### Inside

<a id="realization.issues.store"></a>

**The Issue store** is the only code that performs these actions on an Issue record:

- Creating the record.
- Appending to the record.
- Disposing the record.
- Moving the record.

The store never deletes a committed record. When moving a record between the folders, the store
removes it from one only in the commit that adds it to the other. Each file holds the record alone,
so no prose copy can drift from it. Reports are never rewritten. A later observation that classifies
the problem differently is a new report. The merge lock serializes writes. Before each write
answers, it performs these steps:

- Putting back what earlier writes left uncommitted.
- Checking the revision its caller read against the committed record.
- Committing the record alone.

Because of these steps, success means the record is committed. These steps also ensure that a
concurrent writer is never silently overwritten. After a failure following publication, the store
puts the record back as it was. The store then refuses the write. The
[record file](interface.md#record-file) and the [store operations](interface.md#store-operations)
give these exact details:

- The layout.
- The order of steps.
- The Git commands.

Reads ask Git for the records of the last commit, so they need no lock. For the same reason, reads
see one commit's records at once. Identities are derived from the reporting invocation and the
reporter's key rather than counted, so no allocation state is shared. The report and receipt
shapes are registered as [typed-value](../glossary.json#concept.typed-value) types so that another
part's schema could embed one by name. Issues itself exchanges and checks these items as they are,
without an envelope:

- Reports.
- Receipts.
- Records.

No other part knows the types.

The view below follows one write and what each refusal leaves. When a refusal occurs before
publication, it leaves the record as it was committed.

```d2 illustrative
direction: down
check: "check the request\n(the report or disposition, the root)"
lock: "take the merge lock,\nor the caller holds it"
merge: "every task record read,\nnone stored merging?"
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
merge -> refused: merge_incomplete, unreadable_task_record
recover -> refused: uncommitted_change
recover -> failed: a record not put back
revision -> refused: stale_issue, closed_issue, open_issue
publish -> putback: failure
commit -> putback: commit_failed
putback -> refused: put back
putback -> failed: putting back failed
```

<a id="realization.issues.command"></a>

**The bookkeeping command** is the sessions' face of the store. Its actions are:

- `report` writes.
- `close` writes.
- `reopen` writes.
- `recover` puts back.
- `archive` moves misplaced records.
- `list` reads.
- `show` reads.
- The store check reads.

The command is kept in `src/concorde/issues/command.py` so that its command line and the Issue
tools share every answer and refusal. Its command line is `src/concorde/issues/cli.py`, which
`concorde issues` and `scripts/issues.py` run. The Issue tools are in
`src/concorde/issues/tools.py`. The issues part's
[part registration](../glossary.json#concept.part-registration) names both. Where the spec part is
installed, the command reads the [registry](../glossary.json#concept.registry) for these details:

- Which Modules exist.
- Which Module is root.
- Which digest names a report's context.

Elsewhere, a Module is a label. The command supplies provenance rather than trusting report-file
claims. The report's optional `origin` describes a separate, cross-project observation. An owner
given as `null` falls to the root Module. Attribution as `main-agent` or `task-session` is a
convention of the command and the tools, not authentication. The library accepts provenance from
its caller. A model uses the command. The model can only fix a request it understands, so every
refusal names these details:

- The Issue.
- The report file.
- The field or argument.

For the same reason, every refusal says what is wrong. For the same reason, the command passes
the store's own errors on unchanged in its refusals. A part that may not import Issues' code records the reports of its own run through
the command too. The method part's reviews are an example. With `--provenance`, the part gives
the provenance it vouches for. The command records that provenance as given, as the store's library
does for its callers.

The store check is this Module's own. Its interfaces are `concorde issues check` and the tool
`issue_check`. It is this Module's configured check rather than part of Spec validation. Because
of this separation, the Spec tooling stays unaware of Issues. For the same reason, whenever this
Module's checks run, the records are still checked. An open Issue with an unregistered owner fails
the store check because nobody can be asked to solve it. A closed Issue with an unregistered owner
is only noted.

<a id="realization.issues.tests"></a>

The **Issues tests** cover the store on Git repositories in these areas:

- The merge lock.
- Commits.
- Concurrent writers.
- Malformed records.
- Failed publications and commits.
- Reads of committed records only.
- Recovery after failed and killed writes.
- Moves between the folders and their recovery.
- Archiving.
- Tiers.
- Severities.
- The order by severity.

The tests cover every bookkeeping-command action with its refusals, from the primary and a linked
worktree. The tests also cover the configured store check on a fixture project.

<a id="realization.issues.guidance"></a>

The **Issues guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance). The sections are kept in
`prompts/guidance/issues/`. The part's registration registers them under `guidance`. Wherever the
part is installed, [Distribution](../distribution/module.md#guidance-composition) composes the
sections after Coordination's working method. They are the project skill's and the task-session
prompt's "Issues" sections. They cover these subjects:

- Recording.
- Tiers.
- Severities.
- Fixing.
- Failures of the Issue system.

Each section says what happens where a part it mentions is not installed.
