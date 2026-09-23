# Candidate worktrees in detail

This topic extends the [Candidate worktrees](module.md) entry with the reasoning a maintainer of this
Module needs. Consumers do not need it: the entry states every promise they rely on, and the precise
obligations and formats are in [requirements](requirements.md), [scenarios](scenarios.md) and
[records](records.md).

## Creating a candidate

A candidate is created only from the primary worktree on an attached branch. The Host makes a new
branch `concorde/<uuid>` at the primary's committed `HEAD`, adds a linked worktree for it in a
private temporary directory, copies the primary's vendored reference checkouts into it without the
network, and registers the change. Uncommitted primary edits are never carried over, so a candidate
always starts from a state someone else can reproduce. In a consumer project the Host appends a
marked guidance block to the candidate's `AGENTS.md`, telling a fresh agent session where it is and
how delivery works; a failed registration rolls it back, and the deliverable snapshot strips it.

## One authority, in the primary

A candidate can be deleted, renamed or recreated at the same path, so it cannot hold the only copy
of a change's history. Every durable record lives in the primary worktree, located through Git's
shared repository directory rather than a directory name. Without the primary, a write stops with
`primary_unavailable`; no replacement record is ever created inside a candidate, which holds only
scratch files.

A change's worktree is also identified by an incarnation token written into Git's private
administrative directory for that worktree. Git deletes it with the worktree, so a worktree
recreated at the same path, branch and commit cannot inherit the old change, while renaming the
branch keeps it.

## Concurrent writers

The relaying process in the primary, the relayed launcher in the candidate and the user session's
command line may all write status. Every write takes a repository-wide lock and replaces the whole
record only if its revision is the one the writer read, else `stale_status`. Nothing is merged field
by field, so a stale writer never erases a newer provider section or lifecycle change. Status and run
directories are excluded from Git through the repository's local exclude file, and a write stops if
they are ever tracked.

## Why provider sections

If this Module understood plans, gaps, delivery records or Issue journals, it would depend on every
provider. A declared, typed, opaque section keeps the one-writer revision check and the primary
authority for everyone while the meaning stays with the provider. For the same reason workspace
facts hold only identity and lifecycle; a provider that wants an Agent to see its records supplies
them as a stage input. Each provider reads and writes its own section through its own code, and
keeps the rules of its records there, such as the revision of Planning's progress entries.

## Inventory without trespassing

The summary of other worktrees comes from Git's worktree list and the primary's status records only.
Reading another worktree's files would make one change's draft visible to another and let a stale
candidate influence a request that never ran there.

## Deliverable snapshots and the boundary check

A deliverable snapshot is computed in a private Git index that removes the control paths under
`.concorde/` and strips exactly the recorded guidance block; edited or duplicated markers block it.
The caller's index, the working files and the status record are untouched, and run records use the
same snapshot as a run's exact input tree.

The worktree boundary check reports a directory's Git identity and whether it is a linked worktree,
reading no file contents. It lives with the lifecycle's worktree identity code.

## Not a sandbox

A candidate keeps a change's files away from the primary until delivery. It does not stop a process
running in the candidate from reading or writing any path its user can reach.

## Open questions

Provider sections are declared in code at import time; no command lists which sections a project's
changes carry.
