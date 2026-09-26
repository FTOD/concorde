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

<a id="concept.issues.issue"></a><a id="concept.issues.report"></a>

**What an Issue is.** Each Issue is one file, `.concorde/issues/I-<32 hex digits>.md`, holding its
reports, dispositions and a status of `open`/`closed`. Each report is a `bug`, a `gap` (an
implementation/Spec mismatch, a Spec conflict or a missing promise) or a `limitation`, naming the
owning Module or `null` if unknown — the Issue's owner is then the reporting Module, the root
Module for a command-recorded report. A report may also name its **origin**, when the problem was
seen in another project than the one recording it, such as a
[defect report](../dogfooding/module.md#concept.dogfooding.defect-report) a project using Concorde
hands to the Concorde repository, and may carry the failure's whole
[error chain](../vocabulary.md#concept.concorde.error-chain), so that the chain reaches whoever
solves the Issue as structured data rather than prose. Reports are only appended, never edited; since files travel
with Git, a task-worktree closure stays open on the primary branch until the branch merges.

**Recording a report.** The main agent writes it as JSON and runs
`python3 scripts/issues.py report --file <report.json> [--task <task-id>]`; the command refuses an
unregistered owner, evidence absent from the project (or from the origin project a report names)
or an error chain that breaks the Framework's error contract, and adds its own provenance (reporter,
reporting Module, registry digest, task, Git `HEAD`) so a report can't claim another origin. It
answers with a [receipt](interface.md#contract.issues.receipt) and the new revision once the
record is on disk; naming an open Issue and its revision appends rather than creates, and the same
file run twice records two Issues. No Operation records Issues on its own in this version — the
main agent decides, typically for a Spec gap or an unfixed reported failure.

<a id="concept.issues.disposition"></a>

**Closing and reopening.** A disposition has a reason (`resolved`, `duplicate`, `not-actionable`,
`reopened`), a note, at least one evidence reference and the actor (`duplicate` names another open
Issue); only an open Issue closes, only a closed one reopens, both keeping all reports. The main
agent runs `close <id> --reason <reason> --note <text> --evidence <item>...` or `reopen ...`; the
command records the main agent as the actor. The store checks a disposition's form, not its
evidence's truth, so whoever disposes an Issue answers for it.

**Solving an Issue** is ordinary work: the main agent reads it, opens a task for its owning Module,
runs the Operations that fix the problem, and closes the Issue on the task branch with the
delivered change's evidence, merging the closure with the fix.

**Bookkeeping and the store check.** `list` prints a summary row per Issue, `show <id>` one record
with its revision, and `check` validates every record; the command refuses a directory that is not
an initialized Concorde project and never launches a model. The configured check
`check.issues.store` runs `check` whenever this Module's checks run, failing a malformed, misnamed
or inconsistent record and an open Issue with an unregistered owner (closed ones are only noted,
still listed/shown, repaired by a new report or by closing). An unknown Issue, a stale revision, a
closed Issue to append to or close, an open Issue to reopen, an unregistered owner or missing
evidence is refused, writing nothing and printing an error code and message, exiting 2 (unusable)
or 1 (refused) — shapes, operations, codes in the [Issue interface](interface.md).

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
root, and which digest names a report's context. Because it supplies provenance, a report file
cannot claim another origin and the main agent never learns its shape; an owner given as `null`
falls to the root Module, which the store check always accepts. It has no counter, so a repeated
run records a second Issue, and the main agent checks `list` first. It is used by a model, which can
only fix a request it understands, so every refusal names the Issue, report file and field or
argument and says what is wrong, passing the store's own errors on unchanged.

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
