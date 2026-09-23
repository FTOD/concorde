# Task context requirements

These are the Module-wide obligations of [Task context](module.md). The [scenarios](scenarios.md)
show them in concrete situations; the records are in [contracts](contracts.md).

## Freezing

### req.context.boundary-sets — A snapshot records the Spec Module's boundary sets

A context snapshot SHALL record the selected Module's `SpecContext`, `ImplementationContext` and
`ExternalContext` exactly as the Spec Module computes them for the checkout the snapshot is frozen
in.

`SpecContext` is recorded as one source record per selected document member, with its identity,
owner, path, role, byte digest and every relation that selected it (`owns`, `contains`, `uses` or
`includes`, with its target). `ExternalContext` is recorded
as one tree digest per external inclusion. `ImplementationContext` is recorded as the declared
realization entries and the file names they currently bind.

### req.context.shared-file-readers — A code-writing step reads every Module that binds its files

A snapshot for the `implementation` phase SHALL add, read-only, both members of every document
owned by each other Module that binds a file in the selected Module's `ImplementationScope`, each
recorded with the relation `shares`, that Module and the shared files.

A task that writes a shared file can otherwise break a promise it cannot see (Protocol Boundaries,
shared files). The additional documents are part of the snapshot's identity, so a change to one of
them makes the snapshot stale. They widen no write set and no other phase receives them.

### req.context.focus-no-trim — A scenario focus never trims context

A snapshot focused on a scenario SHALL contain the same boundary sets as a snapshot of the
scenario's owning Module without a focus.

### req.context.names-every-phase — Implementation names reach every phase

Every snapshot SHALL list the names of the files bound by the selected Module's realizations,
including pending entries.

### req.context.contents-code-phases — Implementation contents only for code phases

A snapshot SHALL include the selected Module's `ImplementationScope` files, by path and digest,
only for the `implementation` and `code-review` phases.

### req.context.no-embedded-bodies — Bodies travel as files

The host SHALL NOT embed Spec document, Protocol, external reference or implementation file bodies
in a worker's input.

The worker reads them as files: copies in its capsule, or files in place in the project worktree.
The snapshot itself, the task, stage inputs and a review's typed changes do travel inline.

### req.context.identity — A snapshot is identified by all its inputs

A snapshot's identity SHALL be the SHA-256 digest of its complete canonical content apart from the
identity field itself.

## Rechecking

### req.context.recheck — Recheck rejects changed inputs

A recheck of a snapshot SHALL fail with `stale_context` when any selected document byte, selecting
declaration, realization entry, bound file name, code-phase file byte, external reference digest,
Protocol binding or the current worktree's own status differs from the snapshot.

## Profiles

### req.context.profile-consistent — A worker profile is consistent with its contract

The host SHALL refuse with `invalid_agent_binding` a worker profile whose tools, workspace kind,
path roles, stage inputs or result fields are inconsistent with its contract.
