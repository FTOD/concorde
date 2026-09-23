# Candidate worktrees scenarios

Concrete situations of [Candidate worktrees](module.md). Module-wide obligations are stated once
in [requirements](requirements.md).

## Creating and owning a change

### scenario.worktrees.create-candidate — Create a candidate from the primary's committed HEAD

- GIVEN the primary worktree of a consumer project on an attached branch, with uncommitted edits
- WHEN the host creates a candidate for an admitted request
- THEN a new branch `concorde/<uuid>` and a linked worktree are created at the primary's committed `HEAD`
- AND the primary's vendored reference checkouts are copied into the candidate without network access
- AND a change status with the request's task, target and constraints is registered in the primary
- BUT the uncommitted primary edits are not present in the candidate

Creating a candidate from a linked worktree, or from a primary on a detached `HEAD`, is refused
with `workspace_mismatch`. See [committed base](requirements.md#req.worktrees.committed-base).

### scenario.harness.change-owner — Preserve and validate a change's owner

- GIVEN a change status bound to the current worktree
- WHEN the host reads it, restores its owner for a new request or binds its first target
- THEN omitted task, target, focus and constraints are restored from the record
- AND a conflicting task, target, focus or constraints is refused with `incompatible_handoff` naming the field, before any progress is written
- AND a recorded owner that names no registered Module is refused with `invalid_worktree_state`
- AND a binding request without a task or target is refused with `invalid_input`
- AND a request naming an existing change cannot create a second status for it in another worktree
- BUT reading status never grants access to the change's files or waives a readiness check

See [owner preserved](requirements.md#req.worktrees.owner-preserved).

### scenario.harness.worktree-guidance — Guidance is appended to AGENTS.md and never delivered

- GIVEN a consumer candidate, possibly with existing `AGENTS.md` or `CLAUDE.md` files
- WHEN the host registers a new change there
- THEN it appends its marked guidance block only to `AGENTS.md`, creating the file when it is absent and keeping existing bytes and file mode
- AND if registering the status fails, the guidance bytes and mode are rolled back
- AND a deliverable snapshot strips exactly the recorded block, omitting a file the host created only if nothing else remains in it
- AND edited or duplicated markers block the snapshot instead of discarding content
- BUT `CLAUDE.md` is never written, and the snapshot changes neither the working files, the caller's index nor the status record

See [local state not delivered](requirements.md#req.worktrees.local-state-not-delivered).

## Where a request is

### scenario.harness.workspace-inventory — The inventory joins primary status to live worktrees

- GIVEN a primary worktree and several live linked worktrees, some with a change status and some without
- WHEN the host computes the workspace facts of a request started in the primary
- THEN every live linked worktree is listed with its path, branch, head and lock state
- AND a managed worktree adds its change ID, target, a task summary, phase, status and outcome from its change status
- AND an unmanaged worktree is reported with status `unmanaged`
- BUT no file of another worktree is read, so a candidate's draft edits stay invisible from the primary

A request started in a linked worktree instead reports kind `change` with its own change.

### scenario.harness.worktree-boundary — Require an isolated worktree before a mutation

- GIVEN a directory and an explicit flag that allows the primary worktree
- WHEN the worktree boundary check is required for it
- THEN it returns the directory's Git identity for a committed linked worktree
- AND it accepts a committed primary worktree only when the flag allows it
- AND with the flag set it also accepts a directory outside any Git repository
- BUT a symlinked or missing directory, or a failing Git probe inside a repository, is refused with `WorktreeBoundaryError`

## Persistence

### scenario.harness.primary-status — Stable primary status and run records

- GIVEN a primary worktree and a candidate with a registered change
- WHEN work in the candidate records progress and run evidence
- THEN only the primary's status and runs directories receive durable records, each naming its source worktree
- AND renaming the candidate's branch or removing the candidate keeps the change and its terminal outcome
- AND two registrations of the same change ID from different worktrees produce at most one record
- AND a worktree recreated at the same path, branch and commit does not inherit the old change
- AND a status write carrying an old revision is refused with `stale_status` without erasing newer blockers or progress
- AND a per-Module progress record whose owner does not match the change is refused with `workspace_mismatch`
- AND recording an ordinary Git merge verifies Git ancestry and the candidate's owner before using its `HEAD`, and a cleanup-only update requires an already recorded merge
- BUT when the primary cannot be found the write stops with `primary_unavailable` instead of writing into the candidate

See [primary authority](requirements.md#req.worktrees.primary-authority),
[revision-checked writes](requirements.md#req.worktrees.revision-checked-write) and
[incarnation-bound status](requirements.md#req.worktrees.incarnation-bound).
