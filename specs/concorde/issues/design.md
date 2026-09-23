# Issues design

This topic explains the choices the [Issues](module.md) entry summarizes: how the store keeps
records safe, why one lock serves the whole repository, how the reporting service stays within its
limits, and why store validity is a configured check. Shapes and operations are in the
[Issue interface](interface.md).

## One record, one source

Every Issue file holds one identity heading and one JSON record, so the JSON is the single source of
content and no prose copy can drift from it. An Issue's identity is derived from the reporting
invocation and the reporter's key, not from a counter, so two branches never allocate the same
identity and a retried report finds its earlier result. Reports are never rewritten; a later
observation may classify the problem differently or name another owner, and the first report stays
as it was accepted.

## Writes that never overwrite

Each write checks the file's current byte digest against the revision its caller read, publishes
through a file transaction and syncs the directory before acknowledging. A reply of success means
the record is on disk, and a concurrent writer is never silently overwritten. The store never
deletes a record file, and it never runs Git: moving committed record files between branches, by
creating a candidate, delivering or merging, is not a store write.

## One lock for the repository

All store writes of every worktree take one exclusive lock, `.concorde/runs/issues.lock` in the
primary worktree's run records. Records are per-branch files, but one Host process may write in a
candidate and in the primary, and identities are allocated without a counter; a single lock keeps
allocation and publication from interleaving anywhere in the repository. The lock is cooperative:
it orders the Host's own writers, and a hand edit bypasses it, which the revision check then detects
at the next write. When the primary worktree cannot be found, the store refuses to write rather than
lock locally.

## Form, not truth

The store checks shapes, digests and legal transitions; it cannot judge whether evidence is true.
That is why deciding who may close or reopen an Issue stays with the capabilities that do it.

## The reporting service

The service takes its limits from its caller before the reporter starts. Because the reporter never
supplies provenance, a root path or a disposition, reporting cannot become a file-write grant or a
way to forge who said what. Reports are saved the moment they are accepted, so they survive a
reporter that later fails, times out, is cancelled or submits an invalid result; that survival says
nothing about whether the reporter's own task succeeded.

## Reports, Blockers and dispositions

Reports are cheap and immediate, so workers can record everything they notice without ending their
task. Blockers are task-local judgments recorded by the stage that made them, so replanning cannot
lose a dependency and closing the Issue cannot silently release it. Dispositions need evidence, so a
closed Issue means something was checked, not merely that someone stopped looking.

## Store validity as a configured check

Spec tooling validates Specs and knows nothing of Issues. Checking the records as this Module's
configured check keeps that separation and still runs on every delivery, which runs every
configured check; Issue bytes are part of no other Module's evidence. An open Issue whose owner was
removed fails the check because it can no longer be solved; a closed one is only reported.

## Typed values

The report, receipt, Blocker, selection and context shapes are registered with Spec tooling's
typed-value registry by this Module; Spec tooling does not know them. The shapes live in
`src/concorde/issues/shapes.py`.
