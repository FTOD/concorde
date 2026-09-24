# Issues design

This topic explains the choices the [Issues](module.md) entry summarizes: how the store keeps
records safe, what its lock serializes, why the command supplies provenance, and why store validity
is a configured check. Shapes and operations are in the
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

## Provenance from the command

The main agent writes only the report; the command adds who reported, the reporting Module, the
registry digest, the task and the Git `HEAD`. A report file therefore cannot claim another origin,
and the main agent needs no knowledge of the provenance shape. The command refuses an unregistered
owner and evidence that does not exist, because the store check would fail for such an Issue and
evidence that cannot be opened helps nobody solve it. When the main agent does not know the owner,
it says so with `null`, and the Issue falls to the root Module, which the store check always
accepts. A report is saved the moment the command accepts it, so it survives the task that found
the problem; that says nothing about whether the task succeeded.

Every run of the command is a new invocation, so identity stays derived without a counter, but a
repeated run records a second Issue rather than finding the first. The main agent checks `list`
before recording a problem it may have recorded already.

## Refusals that say what is wrong

The command is used by a model, which can only correct a request it understands. Every refusal
therefore names the Issue, report file and field, or argument concerned, and states what is wrong,
and the store's own errors name the Issue so that the command can pass them on unchanged. Exit
status 2 means the request must be rewritten; 1 means the Issue rules refused a well-formed request.

## Store validity as a configured check

Spec core validates Specs and knows nothing of Issues. Checking the records as this Module's
configured check keeps that separation and still runs whenever this Module's checks run. An open
Issue whose owner was removed fails the check because nobody can be asked to solve it; a closed one
is only noted.

## Typed values

The report and receipt shapes are registered with Spec core's typed-value registry as
`concorde-issue-report@1` and `concorde-issue-receipt@1`; Spec core does not know them. The shapes
live in `src/concorde/issues/shapes.py`.
