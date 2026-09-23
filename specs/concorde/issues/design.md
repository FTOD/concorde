# Issues design

This topic explains the choices the [Issues](module.md) entry summarizes: how the store keeps
records safe, what its lock serializes, how the reporting service stays within its limits, and why
store validity is a configured check. Shapes and operations are in the
[Issue interface](interface.md).

## One record, one source

Every Issue file holds one identity heading and one JSON record, so the JSON is the single source of
content and no prose copy can drift from it. An Issue's identity is derived from the reporting
invocation and the reporter's key, not from a counter, so two branches never allocate conflicting
identities and a retried report finds its earlier result. Reports are never rewritten; a later
observation may classify the problem differently or name another owner, and the first report stays
as it was accepted.

## Writes that never overwrite

Each write checks the file's current byte digest against the revision its caller read, publishes
through a file transaction and syncs the directory before acknowledging. A reply of success means
the record is on disk, and a concurrent writer is never silently overwritten. The store never
deletes a record file, and it never runs Git: moving committed record files between branches, by
committing on a task branch or merging it, is not a store write.

## One lock per worktree

All store writes into one worktree take one exclusive lock, `.concorde/runs/issues.lock` of that
worktree; the runs directory is ignored by Git, so the lock never enters history. Records are
per-branch files, so writers in different worktrees never touch the same file, and because
identities are derived rather than counted they need no shared allocation state either. The lock
orders writers inside one worktree, such as several threads of one host process. It is
cooperative: a hand edit bypasses it, and the revision check detects that edit at the next write.

## Form, not truth

The store checks shapes, digests and legal transitions; it cannot judge whether evidence is true.
That is why the decision to close or reopen an Issue stays with its caller, normally the main agent
on the branch that fixed the problem, so that the closure and the fix are merged together.

## The reporting service

The service takes its limits from its caller before the reporter starts. Because the reporter never
supplies provenance, a root path or a disposition, reporting cannot become a file-write grant or a
way to forge who said what. Reports are saved the moment they are accepted, so they survive a
reporter that later fails, times out or is cancelled; that survival says nothing about whether the
reporter's own task succeeded.

## Store validity as a configured check

Spec core validates Specs and knows nothing of Issues. Checking the records as this Module's
configured check keeps that separation and still runs whenever this Module's checks run. An open
Issue whose owner was removed fails the check because nobody can be asked to solve it; a closed one
is only noted.

## Typed values and leftovers

The report and receipt shapes are registered with Spec core's typed-value registry as
`concorde-issue-report@1` and `concorde-issue-receipt@1`; Spec core does not know them. The shapes
live in `src/concorde/issues/shapes.py`.

That file and the reference helpers still carry shapes of the removed autonomous Issue solving: a
task-local blocker, a review-finding reference and the typed values `concorde-issue-selection@1`
and `concorde-issue-context@1`. Nothing uses them, and this Specification makes no promise about
them; they are candidates for removal, or for a contract of their own if a worker Operation comes
to cite Issue reports in its result.
