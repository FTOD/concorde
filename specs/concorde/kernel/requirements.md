# Kernel requirements

The precise obligations of the [Kernel](module.md) and of its library. The formats they refer to are
the [contracts](contracts.md). The [scenarios](scenarios.md) show them at work. Tracing states its
own obligations.

## Independence

### req.kernel.no-part-imports — The Kernel imports no part

The Kernel SHALL import no part's code.

So every part may depend on the Kernel without bringing in any other part.

### req.kernel.no-part-types — The Kernel registers no part's types

The Kernel SHALL register no part's [typed value](../glossary.json#concept.typed-value) type.

When a part loads, that part's own code registers its types. Before checking a value of a type,
whoever checks it must load its owner, as [Typed values](contracts.md#typed-values) says.

## Workspace binding

### req.kernel.binding-whole — A broken binding is refused whole

The Kernel's binding reader SHALL refuse a [workspace binding](../glossary.json#concept.workspace-binding) with `binding_unreadable` or `binding_invalid` when any of these conditions holds:

- The binding cannot be read.
- The binding breaks the [binding contract](contracts.md#contract.kernel.workspace-binding).
- The binding names a workspace folder that does not exist.

On such a refusal, the binding reader SHALL never return part of the binding.

### req.kernel.binding-own-root — A copied binding is refused

When a binding's `root` is not the real path of the worktree it lies in, the Kernel's binding reader SHALL refuse it with `binding_misplaced`.

## Delivery commits

### req.kernel.delivery-recognized — Deliveries are recognized by their subject

The Kernel SHALL count exactly the commits that meet all these conditions as the [delivery commits](../glossary.json#concept.delivery-commit) of a workspace:

- The commit is on the first-parent history of the workspace's branch.
- The commit occurs since the binding's base commit.
- The commit's subject is `concorde: deliver <workspace>`.

### req.kernel.delivery-verifies — A delivery commit verifies only with one parent

The Kernel SHALL report a delivery commit as verifying only when it has exactly one parent.

A merge commit given the subject is thereby never taken for a delivery, whatever made it.

## Typed values

### req.kernel.registration-stable — A registration never changes

When a type identity is already registered with another version or schema, the Kernel SHALL refuse its registration with `duplicate_type` while keeping the existing registration in force.

Registering it again with the same version and an equal schema changes nothing, so that a part's code
may be loaded twice.

### req.kernel.registered-dialect — A registered schema promises only what is checked

When a schema uses anything outside the [registered dialect](contracts.md#registered-schemas), the Kernel SHALL refuse to register it with `invalid_input`.

### req.kernel.typed-checked — A typed value is checked against its registration

The Kernel SHALL accept a typed value only when all these conditions hold:

- Its type is registered.
- Its `schema_version` is the registered version.
- Its `data`, with every embedded typed value, satisfies the registered schema.

## File transactions

### req.kernel.transaction-fresh — A stale change writes nothing

When any file's current bytes or existence do not match its change's `before_digest` before the first write, a [file transaction](../glossary.json#concept.file-transaction) SHALL write no file.

### req.kernel.transaction-restored — A failed transaction restores what it wrote

When a write or the final check of a file transaction fails while its process runs, the transaction SHALL attempt the following before it reports the failure:

- Restore every file it wrote, or remove every file it created.

When the operating system refuses a restoration, that refusal does not stop the other restorations.
The failure then names the files not restored, as
[req.kernel.transaction-unrestored-named](#req.kernel.transaction-unrestored-named) says. Otherwise,
when the failure is reported, every file holds its original bytes again. An interruption the
process receives, such as `KeyboardInterrupt`, is such a failure. The guarantee covers only what
the transaction's own process observes. As [File transactions](contracts.md#file-transactions) says,
the guarantee assumes that its caller excludes every other writer of the target files.
A killed process restores nothing. A killed process may leave its `.concorde-write-` temporary
files beside the target files. During the transaction, another writer's change may be overwritten.

### req.kernel.transaction-unrestored-named — A refused restoration is named

When the operating system refuses a file transaction's restoration, the transaction SHALL fail with these details:

- The code is `system_error`.
- The failure names every file not restored.
- The first cause is the first failure.

## Locks

### req.kernel.busy-lock-named — A busy lock is refused naming its holder

When a [workspace lock](../glossary.json#concept.workspace-lock) or [merge lock](../glossary.json#concept.merge-lock) taker gives up waiting, the Kernel SHALL refuse the taker with these details:

- The code is `workspace_busy` or `merge_busy`.
- The refusal names the holder that the lock's holder line names.

When both these conditions hold, the Kernel refuses a taker with `workspace_retired` instead:

- The taker waited for a workspace lock whose holder removed its file meanwhile.
- The taker asked not to take a new file.

The reason is that the taker never holds the lock of a workspace that was retired while the taker waited.

## Refusals

### req.kernel.refusals-coded — Every refusal carries a stable code

Every refusal of the Kernel's library SHALL carry these details:

- A stable code.
- The JSON pointer of the offending value or the path of the offending file. It is empty when the
  refusal concerns the whole input.
- A message that describes the refusal completely.

The level that called the library builds its own error link from the refusal, as the
[Library](contracts.md#library) says. The Kernel writes no link itself.
