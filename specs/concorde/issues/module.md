# Issues

## Purpose

Issues keeps a durable record of concrete problems found while working on a project, outliving the
conversation, worker or task that found it: Issue records under `.concorde/issues/`, the store that
alone writes them, dispositions closing or reopening one, and the bookkeeping command the main
agent records, closes, reopens, lists, shows and checks them with. Recording never stops anyone,
starts a repair or grants read/write access; Issues neither solves problems nor decides who may
close one — the main agent solves an Issue with ordinary Operations on its Module, and whoever
disposes it answers for the evidence cited.

## Terminology

| Term | Definition |
| --- | --- |
| Issue | A durable, branch-local record of one concrete problem, holding every report made about it and its disposition history. |
| Issue report | One immutable observation inside an Issue: what was seen, why it matters, the basis for the claim, evidence locations and who reported it. |
| Disposition | A recorded decision that closes an Issue as resolved, duplicate or not actionable, or reopens a closed one, with a note, evidence and the actor. |
| Issue status | The open or closed state of an Issue in one worktree, determined by its disposition history starting from open. |
| Issue revision | The digest of an Issue record's exact bytes, used to refuse a write over a record that changed after it was read. |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Module](../vocabulary.md#concept.concorde.module) | |
| [Evidence](../vocabulary.md#concept.concorde.evidence) | |
| [Registry](../spec-tooling/spec/module.md#concept.spec.registry) | |
| [Typed value](../spec-tooling/spec/module.md#concept.spec.typed-value) | |
| [File transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) | |

An Issue is the problem, a report one observation of it, and a Disposition the decision that it is
settled or needs attention again; observing is cheap, while closing requires evidence.

## Usage

### The main agent and Issues

The main agent decides which observations become Issues and when to dispose them. A worker's
finding or an Operation's error reaches it in that run's result; neither automatically creates or
closes an Issue in this version. A concrete problem the current task will not fix, such as another
Module's Spec gap, is worth recording for later work. Recording it does not clear a blocker, change
a task's outcome, schedule a repair or notify another session. The main agent discovers recorded
problems by reading `list` and `show`.

The bookkeeping command is the main agent's interface. In an installed project it is
`concorde issues` (`concorde` stands for `.concorde/bin/concorde`); in Concorde's source checkout it
is `python3 scripts/concorde.py issues`, which routes to `python3 scripts/issues.py`. These reach
the same store. The [main-session guidance](../agents/main-session/module.md#issues) puts every
Issue write in a task worktree, with `--task <task-id>` on `report`; `close` and `reopen` take no
`--task`. Read-only inspection may use either worktree, and always describes that worktree's copy.
This is guidance to the main agent: the command still accepts an optional task on a report and
uses its selected project root, without enforcing the task workflow.

<a id="concept.issues.issue"></a><a id="concept.issues.report"></a>

**What an Issue is.** Each Issue is one file, `.concorde/issues/I-<32 hex digits>.md`, holding its
reports, dispositions and status. Each report classifies the problem as a `bug`, a `gap` (an
implementation/Spec mismatch, a Spec conflict or a missing promise) or a `limitation`. The latest
report supplies the current title, classification and owning Module. When that report's owner is
`null`, ownership falls to its reporting Module, the root Module for a command-recorded report.
Appending a new observation can therefore correct ownership or classification without rewriting
an earlier report. Ownership identifies the Module whose promise needs attention; it does not
assign an agent or grant permission to change that Module.

A report may name its **origin**, when the problem was seen in another project, such as a
[defect report](../dogfooding/module.md#concept.dogfooding.defect-report) handed to the Concorde
repository, and carry the whole [error chain](../vocabulary.md#concept.concorde.error-chain).
The observation's origin is distinct from the provenance of the command that records it here.

**Recording and following up.** Read `list` before recording, and `show <id>` for a possible match.
`list` includes open and closed Issues; a closed match may need reopening. Write the report as
JSON using the [report contract](interface.md#contract.issues.report), then run
`concorde issues report --file <report.json> --task <task-id>` in the task worktree. The command
checks the owner, evidence paths in this project or the named origin, and any error chain; it
supplies the reporter, reporting Module, registry digest, task and Git `HEAD` itself. A successful
reply gives a [receipt](interface.md#contract.issues.receipt) naming that immutable report and the
record's revision. Keep it as the reference for follow-up. `report --check` checks the report
without recording it, useful before handing a defect report to another project.

To append to an existing open Issue, put its `issue_id` and current `expected_revision` in the
new report. Omit both to create an Issue. Running a creation twice creates two Issues even when the
file and report key are unchanged: each command invocation has new provenance. The store's retry
handling applies only when a caller reuses the same invocation and report key, as the
[interface](interface.md#store-operations) explains; it does not deduplicate separate CLI runs.

### Lifecycle

<a id="concept.issues.status"></a><a id="concept.issues.disposition"></a>

An **Issue status** starts `open`. A **disposition** records a decision to close or reopen it,
with a reason, note, evidence and actor. `resolved`, `duplicate` and `not-actionable` are closing
reasons, not extra statuses. The only statuses are `open` and `closed`:

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

Only a disposition changes an existing Issue's status. Starting a repair, running checks,
delivering a task or merging it is not a disposition; there is no `in-progress` state. A duplicate
closure changes only the Issue being closed: its reports stay there, and later changes to the
referenced Issue do not propagate automatically. Reopening retains the identity and history;
append a new observation afterwards if the problem's description, classification or owner needs
to change. A closed Issue cannot receive a new report or close again, and an open one cannot
reopen. Rejected actions leave its record unchanged.

Use `close <id> --reason <reason> --note <text> --evidence <item>...` or
`reopen <id> --note <text> --evidence <item>...`; duplicate closure also needs
`--duplicate-of <other-id>`. The command records `main-agent` as actor. Each disposition needs a
nonblank note and at least one evidence item. The store validates their form and the transition;
it does not establish that the evidence proves the decision or that the actor had authority.
The main agent answers for that judgment. Closed records remain readable and are never deleted
by the store. The exact state rules are in the [record interface](interface.md#record-file).

<a id="concept.issues.revision"></a>

**Revision and retries.** An Issue revision identifies the exact file contents, independently of
status: appending a report changes the revision while leaving the Issue open. `show`, `report`,
`close` and `reopen` return revisions. Appending uses the revision the main agent read as
`expected_revision`; `close` and `reopen` read the current revision themselves and submit the
disposition against that revision. Their CLI has no argument binding the write to an earlier
`show`. A concurrent change after the command's read is refused with `stale_issue`. Read the
Issue again, reconsider the action and retry against its current record; never erase a concurrent
report to make an old request succeed. A revision protects writes in one worktree, not merges
between branches.

### Branch-local records and repair

The primary branch's records describe what the project has integrated; each task branch holds
its own copy. A receipt confirms a record is on disk in the selected worktree, not that Git has
committed or merged it. A new Issue in a task is absent from the primary branch until merged;
closing an existing Issue there leaves the primary branch's copy open until the closure merges.
The store never commits, merges or transfers records itself.

Solving an Issue is ordinary work: read it, open a task for its current owning Module, run the
Operations that fix it, and close it on the task branch with the fix's evidence before delivery.
Merge the closure with the fix. A typical deferred repair is:

```d2 illustrative
shape: sequence_diagram
main: Main agent
a: Task A worktree
primary: Primary branch
b: Repair task B worktree
a -> main: worker or Operation reports an unfixed problem
main -> a: inspect Issues; record report with task A; deliver
main -> primary: merge A, including the open Issue
main -> b: open B for the Issue's owner; fix and verify
main -> b: close Issue with evidence; deliver
main -> primary: merge B, including fix and closure
```

A task that ends without merging has not published its Issue changes to the primary branch. Closing a
task removes its worktree but retains its branch, task record and decision log, so committed Issue
records remain on that branch. Forced removal can discard uncommitted records and evidence. The
[main-session guidance](../agents/main-session/module.md#issues) tells the main agent to preserve
follow-up information before closing such a task, including how to find the report and evidence;
a decision-log entry alone does not make an Issue appear in `list` on the primary branch.

Changes to the same Issue on different branches may conflict in Git. The worktree lock and
revision checks do not reconcile those histories. The main agent resolves the conflict in the
task worktree, retaining accepted reports unchanged and reconciling the disposition history with
the decision it documents. Two competing closes cannot simply be concatenated, nor can a
reopening be invented merely to make them alternate. Preserve the competing decisions and their
evidence for review when deciding which history to carry forward. Run `concorde issues check`
explicitly on the result before validation and delivery: ordinary structural Spec validation does
not validate Issue records, and the store check cannot decide which closure is justified.

### Inspection and refusals

`list` prints a summary row per Issue, `show <id>` the complete record and revision, and `check`
validates every record. These commands never launch a model. The configured check
`check.issues.store` runs `check` whenever this Module's checks run; it fails malformed, misnamed
or inconsistent records and open Issues with unregistered owners, but only notes closed Issues
with unregistered owners. An open Issue with a valid owner does not by itself fail this check;
readiness to deliver work is a separate decision.

An unknown Issue, stale revision, action on the wrong status, unregistered owner or missing report
evidence is refused without writing a record. The error names the Issue, file, field or argument
and gives a code and explanation so the main agent can correct the request. The exit status is
2 for an unusable request and 1 for a refused one; exact shapes, actions and codes are in the
[Issue interface](interface.md).

## Design

The store alone decides what a record may hold, and the command adds what the main agent must not
be able to claim; everything else is ordinary work run through Operations.

```d2
issues: Issues {
  store: Issue store {
    "store.py"
    "shapes.py"
  }
  command: Bookkeeping command {
    "scripts/issues.py"
  }
  command -> store: records and reads Issues through
}
```

<a id="realization.issues.store"></a>

**The Issue store** is the only code that creates, appends to or disposes an Issue record — Git
moves of committed files aren't store writes, and it never runs Git or deletes a record file. Each
file holds one identity heading and one JSON record, so no prose copy can drift from it, and
reports are never rewritten: a later observation that classifies the problem differently is a new
report. Each write checks the revision its caller read, publishes through a
[file transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) and syncs before
acknowledging, so success means the record is on disk and a concurrent writer is never silently
overwritten. One exclusive lock per worktree, `.concorde/runs/issues.lock`, is enough: identities
are derived from the reporting invocation and the reporter's key rather than counted, so writers in
different worktrees share neither a file nor allocation state. The lock is cooperative; a hand edit
bypasses it and the revision check catches it at the next write. Report and receipt shapes are
[typed values](../spec-tooling/spec/module.md#concept.spec.typed-value) registered as
`concorde-issue-report@1` and `concorde-issue-receipt@1`, which Spec core does not know.

<a id="realization.issues.command"></a>

**The bookkeeping command** is the main agent's face of the store — `report`/`close`/`reopen` write,
`list`/`show`/the store check read — and reads the
[registry](../spec-tooling/spec/module.md#concept.spec.registry) for which Modules exist, which is
root, and which digest names a report's context. It supplies provenance rather than trusting
report-file claims; the report's optional `origin` describes a separate, cross-project observation.
An owner given as `null` falls to the root Module. Attribution as `main-agent` is a command
convention, not authentication: the library accepts provenance from its caller. It is used by a
model, which can only fix a request it understands, so every refusal names the Issue, report file
and field or argument and says what is wrong, passing the store's own errors on unchanged.

The store check is this Module's configured check rather than part of Spec validation, so Spec core
stays unaware of Issues and the records are still checked whenever this Module's checks run. An
open Issue with an unregistered owner fails it because nobody can be asked to solve it; a closed one
is only noted.

<a id="realization.issues.tests"></a>

The **Issues tests** cover the store (temporary directories, concurrent writers, malformed records,
failed publications), every bookkeeping-command action with its refusals, and the configured store
check on a fixture project.

## Relationships

```d2
issues: Issues
core: Spec core
session: Main session
issues -> core
session -> issues
```

Nothing outside the store writes a record; the bookkeeping command is how the main agent adds
reports and dispositions, usually closing an Issue on the task branch that fixed it. Main session
declares `session -> issues` above; its [guidance](../agents/main-session/module.md) says when to record,
solve and close Issues. Issues relies on nobody but Spec core.

<a id="uses-spec"></a>

**Spec core** provides the [typed-value](../spec-tooling/spec/module.md#concept.spec.typed-value)
machinery Issues' shapes register with, the
[file transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) a digest-bound
record publishes through, and the [registry](../spec-tooling/spec/module.md#concept.spec.registry)
the command reads for which Modules exist. A stale transaction is refused, reported `stale_issue`,
writing nothing.
