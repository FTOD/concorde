# Candidate worktrees requirements

These are the Module-wide obligations of [Candidate worktrees](module.md). The
[scenarios](scenarios.md) show them in concrete situations.

## Authority

### req.worktrees.primary-authority — Durable records live only in the primary worktree

The host SHALL write change status and run records only below `.concorde/status/` and
`.concorde/runs/` of the primary worktree.

The primary is found through Git's shared repository directory. If it cannot be found, the write
stops with `primary_unavailable`; a candidate never receives a replacement record. A candidate that
already holds its own `.concorde/runs/` directory is refused with `migration_required`.

### req.worktrees.revision-checked-write — Status writes never overwrite newer status

A change status write SHALL fail with `stale_status` when the revision it carries differs from the
stored record's revision.

A successful write increments the revision. Writing a record identical to the stored one changes
neither its bytes nor its revision.

### req.worktrees.owner-preserved — A change keeps its recorded intent

A request for an existing change SHALL NOT replace the task, target, focus or constraints recorded
for that change.

An omitted field is restored from the record; a conflicting one is refused with
`incompatible_handoff` and names the field.

## Identity

### req.worktrees.committed-base — Candidates start from committed history

The host SHALL create a candidate only from the primary worktree, on a new branch at the committed
`HEAD` of the primary's attached branch.

### req.worktrees.incarnation-bound — Status belongs to one worktree incarnation

The host SHALL admit a change status for a worktree only when the incarnation token in that
worktree's Git administrative directory equals the token recorded when the change was registered.

## Delivery input

### req.worktrees.local-state-not-delivered — Local control state never reaches a delivery

A deliverable snapshot SHALL exclude every Concorde control path under `.concorde/` that the host
keeps local, and the guidance block the host recorded for the change.
