# Issues

## Purpose

Issues keeps a durable record of concrete problems found while working on a project, so that a
problem outlives the conversation, worker or task that found it. It owns the Issue records under
`.concorde/issues/`, the store that is the only code writing them, the reporting service through
which a caller records one reporter's observations under explicit limits, dispositions that close
or reopen an Issue, and the bookkeeping command that lists, shows and checks the records. Recording
a problem never stops anyone, never starts a repair and never grants read or write access to the
project. Issues does not solve problems and decides nothing about who may close an Issue: the main
agent solves an Issue by running ordinary Operations on the Issue's Module, and whoever disposes an
Issue is responsible for the evidence it cites.

## Terminology

| Term | Definition |
| --- | --- |
| Issue | A durable, branch-local record of one concrete problem, holding every report made about it and its disposition history. |
| Issue report | One immutable observation inside an Issue: what was seen, why it matters, the basis for the claim, evidence locations and who reported it. |
| Disposition | A recorded decision that closes an Issue as resolved, duplicate or not actionable, or reopens a closed one, with a note, evidence and the actor. |
| [Developer](../vocabulary.md#concept.concorde.developer) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Module](../vocabulary.md#concept.concorde.module) | |
| [Evidence](../vocabulary.md#concept.concorde.evidence) | |
| [Registry](../spec-tooling/spec/module.md#concept.spec.registry) | |
| [Typed value](../spec-tooling/spec/module.md#concept.spec.typed-value) | |
| [File transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) | |

An Issue is the problem; an Issue report is one observation of it; a Disposition is the decision
that the problem is settled or needs attention again. Keeping observations and decisions apart is
the main idea of the Module: anyone may observe cheaply, while closing requires evidence.

## Usage

<a id="concept.issues.issue"></a><a id="concept.issues.report"></a>

**What an Issue is.** Each Issue is one file, `.concorde/issues/I-<32 hex digits>.md`, committed
with the branch like any other project file. It holds the Issue's reports, its dispositions and a
status of `open` or `closed`. Each report is classified as a `bug`, a `gap` (an
implementation/Spec mismatch, a conflict between Specs or a missing necessary promise) or a
`limitation`, and names the Module that owns the broken promise, or `null` when the reporter does
not know; the Issue's owner is then the reporting Module. For example, the observation that no
Spec says how often a failed payment is retried is a `gap` of subtype `missing-contract` with
owner `module.payments`, citing the Spec file that shows the omission. Reports are never
edited: a later observation is appended as a new report. Because the files travel with Git, an
Issue closed in a task worktree is still open on the primary branch until the task branch is
merged.

**Recording a report.** Reports reach the store only through the reporting service, which a caller
binds for one reporter with explicit limits: the Modules it may name as owner, the files it may
cite, the Issues it may append to, and the provenance of every report, which the caller supplies
and the reporter cannot forge. The service answers with a [receipt](interface.md#contract.issues.receipt) and the
record's new revision only after the record is on disk. Submitting the identical report again
returns the same receipt. No command exposes the service yet, and no Operation records Issues on
its own in this version: the main agent decides which problems deserve an Issue, typically a Spec
gap or failure an Operation result reported that the current task will not fix.

<a id="concept.issues.disposition"></a>

**Closing and reopening.** A disposition has a reason (`resolved`, `duplicate`, `not-actionable` or
`reopened`), a note, at least one evidence reference and the actor; `duplicate` names another open
Issue. Only an open Issue can be closed and only a closed one reopened. Closed Issues keep all
their reports, because reopening needs them. The store checks the form of a disposition, not
whether its evidence is true, so the caller that disposes an Issue is accountable for it.

**Solving an Issue.** Solving is ordinary work. The main agent reads the Issue, opens a task for its
owning Module, runs the Operations that fix the problem, such as `understand`, `specify` or
`implement`, and closes the Issue on the task branch with the evidence of the delivered change, so
the closure is merged together with the fix.

**Bookkeeping and the store check.** `python3 scripts/issues.py list` prints a summary row per
Issue, `show <id>` prints one record with its revision, and `check` validates every record; the
command refuses a directory that is not an initialized Concorde project and never launches a model.
The configured check `check.issues.store` runs `check` whenever this Module's checks run. It fails
for a malformed, misnamed or inconsistent record and for an open Issue whose owner is no longer a
registered Module; a closed Issue with an unknown owner is only noted. Such an Issue is still listed
and shown, and is repaired by appending a report naming a registered owner or by closing it. The
command does not record reports or dispositions yet; those are store operations a host-side caller
performs. Requests naming an unknown Issue, a stale revision, a closed Issue to append to, a reused
report key with other content or anything outside the reporter's limits are refused and write
nothing. The exact shapes, operations and error codes are in the [Issue interface](interface.md).

## Design

<a id="realization.issues.store"></a>

**The Issue store** is the only code that creates, appends to, disposes or restores an Issue
record; Git moves of committed files between branches are not store writes, and the store never
runs Git. Each file holds one identity heading and one JSON record, so there is no prose copy to
drift. Each write checks the revision its caller read, publishes through a
[file transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) and syncs before
acknowledging, all under one exclusive lock kept in the worktree's own `.concorde/runs/`. The
record shapes are registered as [typed values](../spec-tooling/spec/module.md#concept.spec.typed-value).
The store checks form, not truth.

<a id="realization.issues.reporting"></a>

**The reporting service** takes its limits and the provenance from its caller before the reporter
starts, so reporting cannot become a write grant or a way to forge who said what, and it saves each
report at once, so reports survive a reporter that later fails. The same realization holds
reference helpers that check that a result cites only reports its reporter made or was given and
build the text of cited reports for a later reader; no caller uses them in this version.

<a id="realization.issues.command"></a>

**The bookkeeping command** `scripts/issues.py` is the read-only face of the store: `list`, `show`
and the store check. It reads the [registry](../spec-tooling/spec/module.md#concept.spec.registry)
only to know which Modules still exist.

<a id="realization.issues.tests"></a>

The **Issues tests** cover the store on temporary directories, concurrent writers, malformed
records and failed publications, the reporting service's limits, and the configured store check
run as its configured command on a fixture project.

The reasons behind these choices, and what the code still carries from the previous design, are in
[Issues design](design.md).

## Relationships

```mermaid
flowchart LR
    accTitle: Issues structure
    accDescr: The reporting service records reports through the store, the store keeps Issues, an Issue holds reports, dispositions close or reopen Issues, the command reads the store, and the store writes through Spec core.
    reporting[Reporting service] -->|records reports through| store[Issue store]
    command[Bookkeeping command] -->|reads| store
    store -->|keeps| issue[Issue]
    issue -->|holds| report[Issue report]
    disposition[Disposition] -->|closes or reopens| issue
    store -->|writes records through| spec[Spec core]
```

Nothing outside the store writes a record. The reporting service is the only way to add a report
with limits, and dispositions are written by whoever owns that decision, in the worktree it runs
in; the main agent usually does it on the task branch that fixed the problem. The
[Main session](../main-session/module.md) guidance tells the main agent when to record, solve and
close Issues; Issues itself relies on nobody but Spec core.

<a id="uses-spec"></a>

**Spec core** provides the [typed-value](../spec-tooling/spec/module.md#concept.spec.typed-value)
machinery with which Issues registers and checks its shapes, the
[file transaction](../spec-tooling/spec/module.md#concept.spec.file-transaction) through which the
store publishes a record bound to its previous digest, and the
[registry](../spec-tooling/spec/module.md#concept.spec.registry) the store check reads to know which
Modules exist. A transaction refused as stale is reported as `stale_issue`, and nothing is written.
