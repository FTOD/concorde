# Delivery interface

This document gives the exact request, session check, receipt, transitions, manual merge record and
errors of [Delivery](module.md).

## Request

The request and response are the typed values `concorde-deliver-request@1` and
`concorde-deliver-response@3`. `concorde-deliver` takes `change_id` and optionally `target_id`, `task`, `focus_id`,
`constraints`, `keep_worktree` and `merge_primary`. A `target_id` that differs from the change's
Module is refused with `incompatible_handoff`. The response is the common capability response with
outcome `delivered`, the checks of the last verification and one artifact: the change status holding
the receipt. `completed_operations` lists `concorde-deliver` only once cleanup is complete.

The capability declaration binds the request to the primary worktree, never relays it into a
candidate and never creates one.

## Session check

Delivery's first step, before any state is read for writing:

1. The Git repository has linked worktrees (`delivery_session_required` otherwise).
2. Exactly one live candidate worktree carries the `change_id`, or a receipt exists for it
   (`unknown_change` otherwise). The participating worktrees are that candidate, or the receipt's
   `source_worktree`, and the primary worktree.
3. The request's starting worktree and its session root are both participating worktrees, the
   request is not a nested capability invocation, and the Concorde runtime serving it is not a
   checkout of a third worktree of the same repository (`delivery_session_required` otherwise).
4. The primary worktree is on a branch (`detached_primary` otherwise).
5. For `merge_primary`, the starting worktree and the session root are both the primary worktree
   (`primary_session_required` otherwise).

A nested capability invocation is a request issued by another capability's run; a request issued
directly by the user session or by a Task subagent is not nested, and the two are indistinguishable
to the Host.

## Receipt

Delivery keeps its records in its provider section `delivery` of the change status, a typed value
`concorde-delivery-records@1` whose `data` is `{receipt, manual_merge}`, each null until written.
The receipt is stored as `receipt`. Its fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | `1` |
| `change_id`, `target_id`, `focus_id`, `task`, `constraints`, `targets` | the change's identity, intent and recorded Module work |
| `status` | `merging` while publishing, `cleanup_pending` after publication, `delivered` once cleanup is done |
| `source_worktree`, `source_branch` | the candidate's worktree path and branch |
| `candidate_commit`, `candidate_tree` | the delivered candidate commit and its tree |
| `target_branch` | the delivered branch, `concorde/delivered/<change_id>` |
| `target_before`, `primary_branch` | the primary head and branch the integration was built on |
| `merged_commit`, `merged_tree` | the integration commit and its tree |
| `checks` | the check results of the integration's verification |
| `confirmed_files`, `still_pending` | pending entries confirmed at delivery and those still pending |
| `retained_worktree` | whether the candidate's worktree is kept |
| `cleanup_error` | the last cleanup failure, or null |
| `primary_merge` | null, or `{status, branch, before, commit, tree, checks}` with status `merging` or `merged` |

The change status also carries `cleanup.status`: `pending`, `retained` or `removed`, with the last
error. Once a receipt reaches `cleanup_pending` or `delivered`, the change's status and outcome are
`delivered` and its phase `complete`. A receipt with another schema version or change identity is
refused with `invalid_delivery`.

## Delivery transition

Under the repository lock:

1. If a receipt exists and its integration commit is on the delivered branch, record the retention
   choice and go to cleanup.
2. Find the one live candidate worktree of the change. Its status must be `ready` or `delivering`,
   or `blocked` in phase `deliver`, with a validated tree; otherwise `incomplete_change`.
3. Refuse with `stale_delivery` when the delivered branch already exists, and with `stale_evidence`
   when the candidate's deliverable tree differs from the validated tree or the change has no
   completion or validation evidence.
4. Run the [completion check](../validation/records.md#contract.validation.completion) in the
   candidate with the change's recorded Module, focus, task and constraints.
5. Confirm pending entries whose files exist. When the candidate's deliverable tree differs from
   its `HEAD` tree, commit it on top of `HEAD`, with the message `Confirm created files for
   <change_id>` when entries were confirmed and the change's task otherwise.
6. Build the integration commit: the candidate commit itself when it already contains the primary
   head, otherwise a merge commit `Deliver <change_id> from <branch>`; a conflict stops with
   `merge_conflict`.
7. Mark the change `delivering`, verify the integration, and confirm that the candidate and the
   primary head did not move (`stale_evidence`, `stale_delivery`).
8. Save the receipt with status `merging`; move the candidate branch to the candidate commit and
   reset its index to it; refuse with `stale_delivery` when the delivered branch is checked out
   anywhere; create the delivered branch with a create-only update; save status `cleanup_pending`.
9. Clean up.

A failure before publication marks the change `blocked` in phase `deliver` with the error code as
outcome. A failure after publication leaves the receipt at `cleanup_pending` with the error.

## Cleanup

Cleanup first confirms that the integration commit is still on the delivered branch
(`stale_delivery` otherwise). When the candidate worktree is still registered, its branch and head
must match the receipt and its deliverable tree must equal the delivered tree; otherwise it is kept
and cleanup stops with `stale_delivery`. With `keep_worktree`, the candidate is marked delivered
and kept. Otherwise it is marked `cleanup_pending` and removed with `git worktree remove --force`;
a failed removal records the error and leaves the receipt at `cleanup_pending`. When the worktree's
files are already gone but Git still lists it, removal finishes the unregistration.

## Primary merge transition

Under the repository lock, for a `merge_primary` request that passed the session check:

1. Require a receipt whose delivered branch is `concorde/delivered/<change_id>` and that names a
   primary branch (`delivery_required` without a receipt, `invalid_delivery` otherwise), and a
   primary worktree still on that branch (`stale_delivery`).
2. When the receipt's recorded merge commit is already in the primary history, record the merge as
   `merged` and answer without merging again.
3. Require receipt status `delivered` (`delivery_required`), an unchanged delivered branch
   (`stale_delivery`) and a clean primary worktree including untracked files (`dirty_primary`).
4. Build the merge: the primary head when it already contains the delivered branch, the delivered
   commit when it contains the primary head, otherwise a merge commit `Merge delivered <change_id>`;
   a conflict stops with `merge_conflict`.
5. Verify the merge, then confirm that the primary head, the delivered branch and the clean primary
   worktree are unchanged (`stale_delivery`, `dirty_primary`).
6. Save `primary_merge` with status `merging`, fast-forward the primary branch, and save status
   `merged`.

A failed primary merge changes neither the receipt's delivery state nor the change status.

## Integration verification

The commit to verify is checked out into a temporary detached worktree, which is always removed
afterwards. Spec validation of that tree with the Host's own package must succeed (`invalid_merge`),
and every configured check of every Module must pass (`failed_merge_checks`); check logs are kept in
the primary worktree's run records under `.concorde/runs/<invocation>/delivery/<phase>/`, where
`<phase>` is `staging` or `primary`. The tree snapshot must be unchanged after verification
(`stale_evidence`). No build and no other program of the integrated tree runs outside the check
boundary.

## Manual merge record

`record_manual_merge(root, change_id, commit, cleanup)` runs under the repository lock in the
primary worktree and is reached through the project CLI's `status --change-id <id>
--manual-merge <commit> --cleanup <outcome>`. It:

1. requires the primary worktree (`primary_session_required`) and a recorded change
   (`unknown_change`);
2. without `commit`, reuses the recorded manual merge's commit, and refuses with `stale_evidence`
   when none is recorded;
3. requires the commit to be in the primary branch's history (`stale_evidence`);
4. when the candidate worktree still exists, requires it to be this change's incarnation
   (`workspace_mismatch`), its `HEAD` to be contained in the commit and its deliverable tree to equal
   its `HEAD` tree (`stale_evidence`); when it no longer exists, requires a previously recorded
   candidate commit contained in the commit (`stale_evidence`);
5. accepts the cleanup outcome `pending`, `retained` or `removed` (`invalid_input` otherwise), and
   `removed` only when the candidate's worktree is gone (`stale_evidence`);
6. writes the section's `manual_merge: {commit, candidate_commit, method: "ordinary-git"}`, `cleanup.status`
   (`not_needed` for a change registered in the primary worktree itself), status and outcome
   `merged` and phase `complete`.

Recording the same merge again leaves the record unchanged apart from the cleanup outcome.

## Describe policy

A `describe-policy` request needs one live candidate worktree or a receipt for the change, and
answers `described` with an explanation of the delivered branch, the default cleanup and the
separate primary merge. It changes nothing.

## Errors

| Code | Meaning |
| --- | --- |
| `delivery_session_required` | the request does not come from a participating worktree, is nested, or is served from a third worktree |
| `primary_session_required` | a primary merge or manual merge record not requested from the primary worktree |
| `detached_primary` | the primary worktree is not on a branch |
| `unknown_change` | no live candidate and no receipt for the change |
| `incompatible_handoff` | `target_id` differs from the change's Module |
| `incomplete_change` | the change is not ready, or its completion check found unfinished tasks |
| `stale_evidence` | the candidate or its evidence changed after validation or during verification |
| `merge_conflict` | the candidate or delivered branch conflicts with the primary head |
| `invalid_merge` | the integration fails Spec validation |
| `failed_merge_checks` | a configured check of the integration did not pass |
| `stale_delivery` | a branch, worktree or head moved, or the delivered branch already exists without a receipt |
| `invalid_delivery` | a receipt with another schema version or identity |
| `delivery_required` | a primary merge before delivery and cleanup are complete |
| `dirty_primary` | a primary merge with local or untracked changes in the primary worktree |
| `state_persistence_failed` | the failure could not be recorded in the change status |
