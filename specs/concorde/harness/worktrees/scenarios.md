# Candidate worktrees scenarios

Concrete situations of [Candidate worktrees](module.md). Module-wide obligations are stated once
in [requirements](requirements.md).

## Creating a candidate

### scenario.worktrees.create-candidate — Create a candidate from the primary's committed HEAD

- GIVEN the primary worktree of a consumer project on an attached branch, with uncommitted edits
- WHEN the Host creates a candidate for an admitted request
- THEN a new branch `concorde/<uuid>` and a linked worktree are created at the primary's committed `HEAD`
- AND the primary's vendored reference checkouts are copied into the candidate without network access
- AND a change status with the request's task, target and constraints is registered in the primary
- BUT the uncommitted primary edits are not present in the candidate

See [committed base](requirements.md#req.worktrees.committed-base).

### scenario.worktrees.create-candidate-refused — No candidate from a linked or detached worktree

- GIVEN a linked worktree, or a primary worktree on a detached `HEAD`
- WHEN the Host is asked to create a candidate from it
- THEN the request is refused with `workspace_mismatch`
- AND no branch, worktree or change status is created

### scenario.worktrees.guidance-appended — Guidance is appended only to AGENTS.md

- GIVEN a consumer candidate, possibly with existing `AGENTS.md` or `CLAUDE.md` files
- WHEN the Host registers a new change there
- THEN it appends its marked guidance block to `AGENTS.md`, creating the file when it is absent and keeping its existing bytes and file mode
- AND it records which file holds the block and whether it created the file
- BUT `CLAUDE.md` is never written

### scenario.worktrees.guidance-rollback — A failed registration removes the guidance

- GIVEN a consumer candidate whose change registration fails after the guidance block was appended
- WHEN the registration is abandoned
- THEN `AGENTS.md` has its original bytes and mode again, or is absent again if the Host created it
- AND no change status exists for the candidate

## Owning a change

### scenario.worktrees.owner-restored — A later request inherits the recorded owner

- GIVEN a change status bound to the current worktree with a task, target, focus and constraints
- WHEN a new request for that change omits some of these fields
- THEN the omitted fields are restored from the record before the request continues

See [owner preserved](requirements.md#req.worktrees.owner-preserved).

### scenario.worktrees.owner-conflict — A conflicting owner is refused

- GIVEN a change status bound to the current worktree
- WHEN a new request for that change names a different task, target, focus or constraints
- THEN it is refused with `incompatible_handoff` naming the conflicting field
- AND the change status is unchanged

See [owner preserved](requirements.md#req.worktrees.owner-preserved).

### scenario.worktrees.change-id-unique — A change identity belongs to one worktree

- GIVEN a change status registered for one worktree
- WHEN another worktree tries to register a change with the same identity, or two processes register it concurrently
- THEN at most one change status exists for that identity
- AND the second registration is refused with `workspace_mismatch`

### scenario.worktrees.incarnation — A recreated worktree does not inherit an old change

- GIVEN a candidate with a registered change that was removed
- WHEN a new worktree is created at the same path, on the same branch and commit
- THEN no change is bound to the new worktree
- BUT renaming the branch of a live candidate keeps its change bound

See [incarnation-bound status](requirements.md#req.worktrees.incarnation-bound).

### scenario.worktrees.child-owner — Record which Task subagent owns a change

- GIVEN a registered change and the user session in the primary worktree
- WHEN the user session records a Task subagent as the change's writer or tester
- THEN the change status names that Task subagent, its phase and that it runs in a fresh context
- AND releasing it clears the owner and sets the phase to `handoff`
- BUT no session is started

### scenario.worktrees.child-owner-conflict — A second Task subagent cannot take an owned worktree

- GIVEN a change whose worktree a Task subagent already owns
- WHEN the user session records a different Task subagent for it, or for another change on the same worktree
- THEN the request is refused with `workspace_mismatch`
- AND the recorded owner is unchanged

Recording ownership from a linked worktree is refused with `primary_session_required`, and naming
an unknown change with `unknown_change`.

## Persistence

### scenario.worktrees.primary-status — Status and run records live in the primary

- GIVEN a primary worktree and a candidate with a registered change
- WHEN work in the candidate records lifecycle progress and runs
- THEN only the primary's status and runs directories receive durable records, each naming its source worktree
- AND removing the candidate keeps the change status and its terminal outcome

See [primary authority](requirements.md#req.worktrees.primary-authority).

### scenario.worktrees.primary-unavailable — No record without the primary

- GIVEN a candidate whose primary worktree cannot be found
- WHEN the Host writes a change status or a run record
- THEN the write stops with `primary_unavailable`
- BUT nothing is written into the candidate instead

### scenario.worktrees.stale-status — A stale writer cannot overwrite newer status

- GIVEN two writers that read the same revision of a change status
- WHEN the first writes successfully and the second then writes
- THEN the second write is refused with `stale_status`
- AND the stored record keeps the first writer's content, including its provider sections

See [revision-checked writes](requirements.md#req.worktrees.revision-checked-write).

### scenario.worktrees.provider-section — A provider's section is stored as declared

- GIVEN a provider that declared a section name and its typed-value type
- WHEN it writes a change status carrying a valid value in that section
- THEN the value is stored unchanged under the section name with the next revision
- AND every other section of the record is unchanged

### scenario.worktrees.provider-section-refused — An undeclared or mistyped section is refused

- GIVEN a change status write that carries a section no provider declared, or a value that does not satisfy its section's declared type
- WHEN the Host writes it
- THEN the write fails with `invalid_worktree_state`
- AND the stored record is unchanged

See [declared sections](requirements.md#req.worktrees.section-declared).

### scenario.worktrees.run-record — A run record keeps its provenance and artifacts

- GIVEN an admitted request executing in a worktree with a build manifest
- WHEN its run record is opened and later finished with its result envelope
- THEN the record names the source worktree, branch, commit, exact input tree, runtime and build manifest digest, and the final status and envelope
- AND a copy of the build manifest and of every accepted artifact the envelope references is kept in the run directory
- AND an artifact whose bytes no longer match its recorded digest is marked unavailable instead of being copied

## Where a request is

### scenario.worktrees.workspace-inventory — Workspace facts summarize live worktrees from primary records

- GIVEN a primary worktree and several live linked worktrees, some with a change status and some without
- WHEN the Host computes the workspace facts of a request started in the primary
- THEN every live linked worktree is listed with its path, branch, head and lock state
- AND a managed worktree adds its change identity, target, a task summary and lifecycle position from its change status
- AND an unmanaged worktree is reported with status `unmanaged`
- BUT no file inside another worktree is read, so a candidate's draft edits stay invisible

See [inventory from the primary only](requirements.md#req.worktrees.inventory-primary-only).

### scenario.worktrees.boundary-check — Accept an isolated worktree for a mutation

- GIVEN a committed linked worktree, or with the explicit primary flag a committed primary worktree or a directory outside any Git repository
- WHEN the worktree boundary check is required for it
- THEN it returns the directory's Git identity and whether it is isolated
- AND nothing is changed and no file content is read

### scenario.worktrees.boundary-refused — Refuse the primary or an unusable directory

- GIVEN the primary worktree without the explicit flag, a symlinked or missing directory, or a directory inside a repository where a Git probe fails
- WHEN the worktree boundary check is required for it
- THEN it fails with a worktree boundary error that says how to obtain an isolated worktree
- AND nothing is changed

## Delivery input

### scenario.worktrees.deliverable-snapshot — A deliverable snapshot drops local state

- GIVEN a candidate with changes, local control files under `.concorde/` and a recorded guidance block in `AGENTS.md`
- WHEN the Host computes its deliverable snapshot
- THEN the snapshot tree holds the candidate's changes without the control paths and with exactly the recorded guidance block stripped
- AND a guidance file the Host created is omitted when nothing else remains in it
- BUT the working files, the caller's Git index and the change status are unchanged

See [local state not delivered](requirements.md#req.worktrees.local-state-not-delivered).

### scenario.worktrees.guidance-markers-edited — Edited guidance markers block the snapshot

- GIVEN a candidate whose guidance block markers were edited, removed or duplicated
- WHEN the Host computes its deliverable snapshot
- THEN it fails with `invalid_worktree_state`
- BUT no content around the markers is discarded
