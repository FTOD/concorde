# Delivery records

This document gives the exact request, receipt, transitions and errors of [Delivery](module.md).

## Request

`concorde-deliver` takes `change_id` and optionally `target_id`, `task`, `focus_id`,
`constraints`, `keep_worktree` and `merge_primary`. A `target_id` that differs from the change's
Module is refused with `incompatible_handoff`. The response is the common capability response with
outcome `delivered`, the checks of the last verification and one artifact: the change's status
record holding the receipt. `completed_operations` lists `concorde-deliver` only once cleanup is
complete.

## Session check

Before admission binds the request, Delivery confirms that the Git repository has linked worktrees,
that exactly one live candidate worktree carries the `change_id` or a receipt exists for it, that
both the session's project root and its session root are the source or the primary worktree, that
the session is at most one delegation level deep, that the Concorde runtime serving the request is
not a third worktree of the same repository, and that the primary worktree is on a branch
(`detached_primary` otherwise). The request is then bound to the primary worktree.

## Receipt

The receipt is stored in the `delivery` field of the change's status record under
`.concorde/status/`. Its fields:

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

The status record also carries `cleanup.status`: `retained`, `removed` or `pending`, with the last
error. A receipt with another schema version or change identity is refused with `invalid_delivery`.

## Delivery transition

Under the repository lock:

1. If a receipt exists and its integration commit is on the delivered branch, record the retention
   choice and go to cleanup.
2. Find the one live candidate worktree of the change. Its status must be `ready` or `delivering`,
   or `blocked` in the delivery phase, with a validated tree; otherwise `incomplete_change`.
3. Refuse with `stale_delivery` when the delivered branch already exists, and with `stale_evidence`
   when the candidate's tree differs from the validated tree or the change has no evidence.
4. Run Validation's [completion check](../validation/requirements.md#req.validation.completion-gates) in
   the candidate.
5. Confirm pending entries whose files exist. When the candidate's tree differs from its `HEAD`
   tree, commit it on top of `HEAD`, with the message `Confirm created files for <change_id>` when
   entries were confirmed and the change's task otherwise.
6. Build the integration commit: the candidate itself when it already contains the primary head,
   otherwise a merge commit `Deliver <change_id> from <branch>`; a conflict stops with
   `merge_conflict`.
7. Mark the candidate `delivering`, verify the integration, and confirm that the candidate and the
   primary head did not move (`stale_evidence`, `stale_delivery`).
8. Save the receipt with status `merging`; move the candidate branch to the candidate commit and
   reset its index to it; refuse with `stale_delivery` when the delivered branch is checked out
   anywhere; create the delivered branch with a create-only update; save status `cleanup_pending`.
9. Clean up.

A failure before publication marks the candidate `blocked` in the delivery phase with the error
code as outcome. A failure after publication leaves the receipt at `cleanup_pending` with the error.

## Cleanup

Cleanup first confirms that the integration commit is still on the delivered branch
(`stale_delivery` otherwise). When the candidate worktree is still registered, its branch and head
must match the receipt and its files must equal the delivered tree; otherwise it is kept and cleanup
stops with `stale_delivery`. With `keep_worktree`, the candidate is marked delivered and kept.
Otherwise it is marked `cleanup_pending` and removed with `git worktree remove --force`; a failed
removal records the error and leaves the receipt at `cleanup_pending`. When the worktree's files are
already gone but Git still lists it, removal finishes the unregistration.

## Primary merge transition

Under the repository lock, for a `merge_primary` request from the primary session:

1. Require a receipt whose delivered branch is `concorde/delivered/<change_id>` and that names a
   primary branch (`invalid_delivery` otherwise), and a primary worktree still on that branch
   (`stale_delivery`).
2. When the receipt's merge commit is already in the primary history, record the merge as `merged`
   and answer without merging again.
3. Require receipt status `delivered` (`delivery_required`), an unchanged delivered branch
   (`stale_delivery`) and a clean primary worktree including untracked files (`dirty_primary`).
4. Build the merge: the primary head when it already contains the delivered branch, the delivered
   commit when it contains the primary head, otherwise a merge commit `Merge delivered <change_id>`;
   a conflict stops with `merge_conflict`.
5. Verify the merge, then confirm that the primary head, the delivered branch and the clean primary
   worktree are unchanged.
6. Save `primary_merge` with status `merging`, fast-forward the primary branch, and save status
   `merged`.

## Integration verification

The integration commit is checked out into a temporary detached worktree, which is always removed
afterwards. When its root contains `concorde.json`, the Host runs that tree's
`scripts/concorde.py build` in a fresh process, saves the build log and the build manifest under
`.concorde/runs/<invocation>/delivery/<phase>/`, and uses the built tree as the Concorde package;
a build failure stops with `invalid_merge`. Spec validation of the tree must succeed
(`invalid_merge`), and every configured check of every Module must pass (`failed_merge_checks`).
The tree snapshot must be unchanged after verification (`stale_evidence`).

## Describe policy

A `describe-policy` request needs one live candidate worktree or a receipt for the change, and
answers `described` with an explanation of the delivered branch, the default cleanup and the
separate primary merge. It changes nothing.
