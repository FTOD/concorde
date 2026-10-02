# Kernel scenarios

Concrete situations that show the Kernel's [requirements](requirements.md) at work on its library.
The formats are the [contracts](contracts.md).

## Workspace binding

### scenario.kernel.binding-read — A binding is read whole from its own worktree

- GIVEN a worktree whose [workspace binding](../glossary.json#concept.workspace-binding) satisfies its contract, names that worktree's real path as its root and an existing workspace folder, and another worktree with no binding file
- WHEN the Kernel's binding reader reads each worktree
- THEN it returns the first binding exactly as written
- AND for the second it returns none, without refusing

### scenario.kernel.binding-refused — A broken binding is refused whole

- GIVEN a worktree whose binding file is no JSON, one whose binding names the workspace `Not A Name`, one whose binding names a relative workspace folder and one whose binding names a workspace folder that does not exist
- WHEN the binding reader reads each
- THEN it refuses the first with `binding_unreadable` and the three others with `binding_invalid`, naming the file
- AND the refusal of the invalid name names the field `/workspace`
- AND it returns no part of any of them

### scenario.kernel.binding-copied — A copied binding is refused

- GIVEN a worktree holding a binding copied from another worktree, which names that other worktree as its root
- WHEN the binding reader reads it
- THEN it refuses it with `binding_misplaced`, naming both the root the binding names and the worktree it lies in

## Delivery commits

### scenario.kernel.deliveries-listed — Deliveries are recognized by their subject since the base

- GIVEN a branch whose base commit has the subject `concorde: deliver retry`, followed by a commit with that subject, a commit with the subject `concorde: deliver other`, an ordinary commit and a second commit with the subject `concorde: deliver retry`
- WHEN the Kernel lists the deliveries of workspace `retry` on the branch since the base
- THEN it lists exactly the two commits after the base with the subject `concorde: deliver retry`, oldest first
- AND each verifies, having exactly one parent
- AND a [delivery commit](../glossary.json#concept.delivery-commit) made with the Kernel's message carries the workspace's goal as its body

### scenario.kernel.delivery-merge-unverified — A merge commit with the subject does not verify

- GIVEN a branch whose head is a merge commit given the subject `concorde: deliver retry`
- WHEN the Kernel lists the deliveries of workspace `retry`
- THEN it lists the merge commit, saying that it has two parents instead of one, so it does not verify
- AND a revision Git cannot resolve is refused with `git_failed`, naming the Git command and its output

## Typed values

### scenario.kernel.registration-repeated — Registering a type again changes nothing or is refused

- GIVEN a type `example-note` registered at version 1 with a schema
- WHEN it is registered again at version 1 with an equal schema, and then at version 2, and then at version 1 with another schema
- THEN the first repetition changes nothing
- AND each of the two others is refused with `duplicate_type`
- AND a value of version 1 that satisfies the first schema is still accepted afterwards

### scenario.kernel.registration-dialect — A schema outside the registered dialect is refused

- GIVEN schemas using `oneOf`, local `$defs`, a `$ref` to `#/$defs/note`, a list of types, the format `email` and `minLength` greater than `maxLength`
- WHEN each is registered as a type
- THEN each is refused with `invalid_input`, and none of the types is registered
- AND a record checked against a contract schema may use local `$defs` with `{"$ref": "#/$defs/<name>"}`, while a local reference that names no entry of its `$defs` is refused with `invalid_input`

### scenario.kernel.typed-embedded — A typed value is checked with every value it embeds

- GIVEN a type `example-batch` whose schema embeds whole values of a type `example-run` as the items of its `runs`, while `example-run` is not registered
- WHEN a value of `example-batch` holding one run is checked, and again after `example-run` is registered
- THEN the first check fails with `unknown_type` at `/data/runs/0`
- AND the second accepts the value and returns a copy that is not the value given
- AND a run with another `schema_version` fails with `unsupported_version`, a run of another type with `incompatible_handoff` and a run whose data breaks its schema with `invalid_field`, each naming the JSON pointer of the offending field

## File transactions

### scenario.kernel.transaction-stale — A stale change writes nothing

- GIVEN two files, and a transaction that changes both, the second's `before_digest` computed before that file was changed again
- WHEN the transaction is applied
- THEN it is refused with `stale_proposal`, naming the second file
- AND neither file was written
- AND a change of a path outside the allowed ones is refused with `permission_denied` and a malformed list with `invalid_proposal`, before any write

### scenario.kernel.transaction-restored — A failed final check restores every file

- GIVEN a transaction that changes an existing file and creates a new one, with a final check that fails
- WHEN the transaction is applied
- THEN the existing file holds its original bytes again and the new file does not exist
- AND the caller receives the final check's failure exactly as the check raised it

### scenario.kernel.transaction-unrestored — A refused restoration is named

- GIVEN a transaction whose final check fails, and an operating system that refuses to restore one of the files it wrote
- WHEN the transaction is applied
- THEN it fails with `system_error`, naming that file and saying that it still holds the transaction's new content
- AND its first cause is the final check's failure and its next the refused restoration
- AND every other written file was restored

## Locks

### scenario.kernel.busy-lock-refused — A busy lock is refused naming its holder

- GIVEN a process holding the [merge lock](../glossary.json#concept.merge-lock) for `concorde task merge` of task `t1`, and another holding the [workspace lock](../glossary.json#concept.workspace-lock) of workspace `t2`
- WHEN a third process takes each without waiting
- THEN it is refused with `merge_busy` and `workspace_busy`, each naming the holder its holder line names
- AND a process that waited for the workspace lock of `t2` while its holder removed the lock file, without asking to take a new file, is refused with `workspace_retired`
- AND once the holders released them, both locks are taken and their holders read back
