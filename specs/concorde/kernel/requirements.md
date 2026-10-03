# Kernel requirements

The precise obligations of the [Kernel](module.md) and of its library. The formats they refer to are
the [contracts](contracts.md), and the [scenarios](scenarios.md) show them at work; Tracing states its
own.

## Independence

### req.kernel.no-part-imports — The Kernel imports no part

The Kernel SHALL import no part's code.

So every part may depend on the Kernel without bringing in any other part.

### req.kernel.no-part-types — The Kernel registers no part's types

The Kernel SHALL register no part's [typed value](../glossary.json#concept.typed-value) type.

A part's types are registered by that part's own code when it loads; whoever checks a value of a
type must have loaded its owner, as [Typed values](contracts.md#typed-values) says.

## Workspace binding

### req.kernel.binding-whole — A broken binding is refused whole

The Kernel's binding reader SHALL refuse a [workspace binding](../glossary.json#concept.workspace-binding) that cannot be read, breaks the [binding contract](contracts.md#contract.kernel.workspace-binding) or names a workspace folder that does not exist, with `binding_unreadable` or `binding_invalid`, never returning part of it.

### req.kernel.binding-own-root — A copied binding is refused

The Kernel's binding reader SHALL refuse with `binding_misplaced` a binding whose `root` is not the real path of the worktree it lies in.

## Delivery commits

### req.kernel.delivery-recognized — Deliveries are recognized by their subject

The Kernel SHALL count as the [delivery commits](../glossary.json#concept.delivery-commit) of a workspace exactly the commits on the first-parent history of its branch since the binding's base commit whose subject is `concorde: deliver <workspace>`.

### req.kernel.delivery-verifies — A delivery commit verifies only with one parent

The Kernel SHALL report a delivery commit as verifying only when it has exactly one parent.

A merge commit given the subject is thereby never taken for a delivery, whatever made it.

## Typed values

### req.kernel.registration-stable — A registration never changes

Registering a type identity already registered with another version or schema SHALL be refused with `duplicate_type`, the existing registration staying in force.

Registering it again with the same version and an equal schema changes nothing, so that a part's code may be loaded twice.

### req.kernel.registered-dialect — A registered schema promises only what is checked

The Kernel SHALL refuse with `invalid_input` to register a schema that uses anything outside the [registered dialect](contracts.md#registered-schemas).

### req.kernel.typed-checked — A typed value is checked against its registration

The Kernel SHALL accept a typed value only when its type is registered, its `schema_version` is the registered version and its `data`, with every embedded typed value, satisfies the registered schema.

## File transactions

### req.kernel.transaction-fresh — A stale change writes nothing

A [file transaction](../glossary.json#concept.file-transaction) SHALL write no file when any file's current bytes, or its existence, do not match its change's `before_digest` before the first write.

### req.kernel.transaction-restored — A failed transaction restores what it wrote

When a write or the final check of a file transaction fails while its process runs, the transaction SHALL restore every file it wrote, or remove every file it created, before it reports the failure.

The guarantee covers only what the transaction's own process observes and assumes that its caller
excludes every other writer of the target files, as [File transactions](contracts.md#file-transactions)
says: a killed process restores nothing and may leave its `.concorde-write-` temporary files beside
the target files, and another writer's change during the transaction may be overwritten.

### req.kernel.transaction-unrestored-named — A refused restoration is named

A file transaction whose restoration the operating system refuses SHALL fail with `system_error`, naming every file not restored, with the first failure as its first cause.

## Locks

### req.kernel.busy-lock-named — A busy lock is refused naming its holder

A taker of the [workspace lock](../glossary.json#concept.workspace-lock) or the [merge lock](../glossary.json#concept.merge-lock) that gives up waiting SHALL be refused with `workspace_busy` or `merge_busy`, naming the holder its holder line names.

A taker that waited for a workspace lock whose holder removed its file meanwhile, and that asked not
to take a new file, is refused with `workspace_retired` instead, so that it never holds the lock of a
workspace that was retired while it waited.

## Refusals

### req.kernel.refusals-coded — Every refusal carries a stable code

Every refusal of the Kernel's library SHALL carry a stable code, the JSON pointer of the offending value or the path of the offending file, empty when the refusal concerns the whole input, and a message that describes it completely.

The level that called the library builds its own error link from it, as the
[Library](contracts.md#library) says; the Kernel writes no link itself.
