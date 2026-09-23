# Task context requirements

The Module-wide obligations of [Task context](module.md). The [scenarios](scenarios.md) show them
in concrete situations; the records are in [records](records.md).

## Freezing

### req.context.boundary-sets — A snapshot records Spec tooling's boundary sets

A context snapshot SHALL record the `SpecContext` of every bound Module and the selected Module's
`ImplementationContext` and `ExternalContext` exactly as Spec tooling computes them for the
checkout the snapshot is frozen in.

`SpecContext` is recorded as one source record per selected document member, with its identity,
owner, path, role, byte digest and every relation that selected it. `ExternalContext` is recorded
as one tree digest per external inclusion. `ImplementationContext` is recorded as the declared
realization entries and the file names they currently bind.

### req.context.shared-file-binding — A code-writing call is bound to every Module sharing its files

A snapshot for an Agent whose definition writes implementation SHALL also be bound to each other
Module that binds a file in the selected Module's `ImplementationScope`, recording that Module's
`SpecContext` and the files it shares.

The additional Modules add reading only: the intended write paths stay the selected Module's
`ImplementationScope`. Their documents are part of the snapshot's identity, so a change to one of
them makes the snapshot stale.

### req.context.focus-no-trim — A scenario focus never trims context

A snapshot focused on a scenario SHALL contain the same boundary sets as a snapshot of the
scenario's owning Module without a focus.

### req.context.names-every-phase — Implementation names reach every phase

Every snapshot SHALL list the names of the files bound by the selected Module's realizations,
including pending entries.

### req.context.contents-when-read — Implementation contents only for Agents that read them

A snapshot SHALL include the selected Module's `ImplementationScope` files, by path and digest,
only when the bound Agent definition reads implementation.

### req.context.no-embedded-bodies — Bodies travel as files

The Host SHALL NOT embed Spec document, Protocol, external reference or implementation file bodies
in an Agent's input.

The Agent reads them as files: copies in its capsule, or files in place in the project worktree
for the programmer. The snapshot itself, the task, stage inputs and a review's typed changes do
travel inline.

### req.context.identity — A snapshot is identified by all its inputs

A snapshot's identity SHALL be the SHA-256 digest of its complete canonical content apart from the
identity field itself.

## Delivery

### req.context.capsule-exact — A capsule holds exactly the delivered copies

A capsule SHALL contain byte-identical copies of exactly the files its snapshot delivers to the
bound Agent, and the context file.

Which files are delivered is fixed by the snapshot and the Agent definition, as the
[capsule layout](records.md#capsule) states. Agent execution may add its own launch files beside
them; those are not context.

## Rechecking

### req.context.recheck — Recheck rejects changed inputs

A recheck of a snapshot SHALL fail with `stale_context` when any rechecked input differs from the
snapshot.

The rechecked inputs are the snapshot's identity digest, the current worktree's workspace facts
other than the list of other worktrees, the Protocol binding, the Spec context record of every
bound Module, the selected Module's realization entries, its bound file names, the implementation
file bytes the snapshot holds, the external reference digests and the Agent binding. For an Agent
whose definition writes implementation, bound file names and implementation bytes are not
rechecked, because changing them is the purpose of the call.

## Binding

### req.context.definition-consistent — Only a consistent, built definition is bound

The Host SHALL refuse with `invalid_agent_binding` to bind an Agent definition whose tools,
workspace kind, effects, stage inputs or result fields are inconsistent with each other, or whose
instruction source is not recorded in the build manifest.
