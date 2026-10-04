# Kernel scenarios

Concrete situations that show the Kernel's [requirements](requirements.md) at work on its library.
The formats are the [contracts](contracts.md).

## Workspace binding

### scenario.kernel.binding-read — A binding is read whole from its own worktree

- GIVEN a worktree whose [workspace binding](../glossary.json#concept.workspace-binding) satisfies its contract
- AND the binding names that worktree's real path as its root
- AND the binding names an existing workspace folder
- AND another worktree has no binding file
- WHEN the Kernel's binding reader reads each worktree
- THEN it returns the first binding exactly as written
- AND for the second it returns none, without refusing

### scenario.kernel.binding-refused — A broken binding is refused whole

- GIVEN a worktree whose binding file is no JSON
- AND a worktree whose binding names the workspace `Not A Name`
- AND a worktree whose binding names a relative workspace folder
- AND a worktree whose binding names a workspace folder that does not exist
- WHEN the binding reader reads each
- THEN it refuses the first with `binding_unreadable`
- AND it refuses the three others with `binding_invalid`
- AND each refusal names the file
- AND the refusal of the invalid name names the field `/workspace`
- AND it returns no part of any of them

### scenario.kernel.binding-copied — A copied binding is refused

- GIVEN a worktree holding a binding copied from another worktree
- AND the binding names that other worktree as its root
- WHEN the binding reader reads it
- THEN it refuses it with `binding_misplaced`
- AND the refusal names both the root the binding names and the worktree it lies in

## Delivery commits

### scenario.kernel.deliveries-listed — Deliveries are recognized by their subject since the base

- GIVEN a branch whose base commit has the subject `concorde: deliver retry`
- AND after the base, a commit with that subject
- AND then a commit with the subject `concorde: deliver other`
- AND then an ordinary commit
- AND then a second commit with the subject `concorde: deliver retry`
- WHEN the Kernel lists the deliveries of workspace `retry` on the branch since the base
- THEN it lists exactly the two commits after the base with the subject `concorde: deliver retry`, oldest first
- AND because each has exactly one parent, each verifies

### scenario.kernel.delivery-message — A delivery message carries the subject and the goal

- GIVEN the workspace `retry` with the goal `Limit HTTP retries to three attempts.` followed by a newline
- WHEN the Kernel makes its delivery message
- AND a [delivery commit](../glossary.json#concept.delivery-commit) is made with it
- THEN the commit's subject is `concorde: deliver retry`
- AND its body is the goal without the trailing newline

### scenario.kernel.delivery-merge-unverified — A merge commit with the subject does not verify

- GIVEN a branch whose head is a merge commit given the subject `concorde: deliver retry`
- WHEN the Kernel lists the deliveries of workspace `retry`
- THEN it lists the merge commit
- AND it says that the merge commit has two parents instead of one
- AND for that reason, the merge commit does not verify

### scenario.kernel.deliveries-unresolvable — A branch Git cannot resolve is refused

- GIVEN a repository with no branch `missing`
- WHEN the Kernel lists the deliveries of workspace `retry` on the branch `missing`
- THEN it refuses with `git_failed`
- AND the refusal names the Git command and its output

## Typed values

### scenario.kernel.registration-repeated — Registering a type again changes nothing or is refused

- GIVEN a type `example-note` registered at version 1 with a schema
- WHEN it is registered again at version 1 with an equal schema
- AND then at version 2
- AND then at version 1 with another schema
- THEN the first repetition changes nothing
- AND each of the two others is refused with `duplicate_type`
- AND a value of version 1 that satisfies the first schema is still accepted afterwards

### scenario.kernel.registration-dialect — A schema outside the registered dialect is refused

- GIVEN a schema using `oneOf`
- AND a schema using local `$defs`
- AND a schema using a `$ref` to `#/$defs/note`
- AND a schema using a list of types
- AND a schema using the format `email`
- AND a schema using `minLength` greater than `maxLength`
- WHEN each is registered as a type
- THEN each is refused with `invalid_input`
- AND none of the types is registered

### scenario.kernel.contract-schema-defs — A contract schema describes a recursive record through its `$defs`

- GIVEN a contract schema for objects whose `child` is a `node`
- AND its top-level `$defs` defines `node` as `null` or such an object again through `{"$ref": "#/$defs/node"}`
- AND the records `{"child": {"child": {"child": null}}}` and `{"child": 1}`
- WHEN each record is checked against the schema
- THEN the first is accepted
- AND the second is refused with `invalid_field`
- AND the refusal names `/child`

### scenario.kernel.contract-schema-refused — A contract schema outside its dialect is refused

- GIVEN a contract schema whose local reference names no entry of its `$defs`
- AND another contract schema keeps a `$defs` inside one of its properties
- WHEN a record is checked against each
- THEN each schema is refused with `invalid_input`
- AND the refusal of the second names the JSON pointer of its misplaced `$defs`

### scenario.kernel.typed-embedded — A typed value is checked with every value it embeds

- GIVEN a type `example-batch` whose schema embeds whole values of a type `example-run` as the items of its `runs`
- AND `example-run` is not registered
- WHEN a value of `example-batch` holding one run is checked
- AND after `example-run` is registered, the value is checked again
- THEN the first check fails with `unknown_type` at `/data/runs/0`
- AND the second accepts the value
- AND the second returns a copy that is not the value given

### scenario.kernel.typed-embedded-refused — A broken embedded value refuses its container

- GIVEN the types `example-batch` and `example-run` above, both registered
- AND three values of `example-batch`, each holding one run
- AND the first value's one run has another `schema_version`
- AND the second value's one run is of another type
- AND the third value's one run holds data that breaks the schema of `example-run`
- WHEN each value is checked
- THEN the first check fails with `unsupported_version`
- AND the second check fails with `incompatible_handoff`
- AND the third check fails with `invalid_field`
- AND each refusal names the JSON pointer of the offending field inside the run

## File transactions

### scenario.kernel.transaction-stale — A stale change writes nothing

- GIVEN two files
- AND a transaction changes both
- AND the second's `before_digest` was computed before that file was changed again
- WHEN the transaction is applied
- THEN it is refused with `stale_proposal`
- AND the refusal names the second file
- AND neither file was written

### scenario.kernel.transaction-not-allowed — A change outside the allowed paths writes nothing

- GIVEN two files
- AND a transaction changes both
- AND the transaction allows only the first
- WHEN the transaction is applied
- THEN it is refused with `permission_denied`
- AND neither file was written

### scenario.kernel.transaction-malformed — A malformed list of changes writes nothing

- GIVEN an empty list of changes
- AND a change without its `before_digest` and `content`
- AND a list that names one path twice
- AND a change of the path `../a.txt`
- WHEN each is applied as a transaction
- THEN each is refused with `invalid_proposal`
- AND no file was written

### scenario.kernel.transaction-restored — A failed final check restores every file

- GIVEN a transaction that changes an existing file
- AND the transaction creates a new file
- AND the transaction's final check fails
- WHEN the transaction is applied
- THEN the existing file holds its original bytes again
- AND the new file does not exist
- AND the caller receives the final check's failure exactly as the check raised it

### scenario.kernel.transaction-unrestored — A refused restoration is named

- GIVEN a transaction whose final check fails
- AND an operating system refuses to restore one of the files the transaction wrote
- WHEN the transaction is applied
- THEN it fails with `system_error`
- AND the failure names that file
- AND the failure says that the file still holds the transaction's new content
- AND the failure's first cause is the final check's failure
- AND the failure's next cause is the refused restoration
- AND every other written file was restored

## Locks

### scenario.kernel.busy-lock-refused — A busy lock is refused naming its holder

- GIVEN a process holding the [merge lock](../glossary.json#concept.merge-lock) for `concorde task merge` of task `t1`
- AND another process holds the [workspace lock](../glossary.json#concept.workspace-lock) of workspace `t2`
- WHEN a third process takes each without waiting
- THEN for the merge lock, the third process is refused with `merge_busy`
- AND for the workspace lock, the third process is refused with `workspace_busy`
- AND each refusal names the holder its lock's holder line names

### scenario.kernel.workspace-lock-retired — A workspace retired while its lock was awaited is refused

- GIVEN a process holding the workspace lock of `t2` for `concorde task close`
- AND as the process releases the lock, it removes the lock file
- AND another process waits for that lock
- AND the waiting process asked not to take a new file
- WHEN the holder releases the lock
- THEN the waiting process is refused with `workspace_retired`
- AND it does not hold the lock

### scenario.kernel.lock-taken — A free lock is taken and its holder read back

- GIVEN the merge lock and the workspace lock of `t2`, which their earlier holders released
- WHEN a process takes each
- THEN it holds both
- AND reading each lock's holder gives the holder line the process wrote
- AND once the process releases them, reading either holder gives none
