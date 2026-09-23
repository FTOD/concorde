# Delivery scenarios

These situations show how [Delivery](module.md) behaves. The obligations they demonstrate are
defined once in [Delivery requirements](requirements.md).

## Delivering a change

### scenario.delivery.branch — Deliver a ready change to its own branch

- GIVEN a ready change selected by its `change_id`
- AND a request from its candidate worktree or from the primary worktree
- WHEN `concorde-deliver` runs
- THEN the Host reruns the completion check, builds the integration commit with the current primary head and verifies it
- AND saves the delivery receipt and creates `concorde/delivered/<change_id>` without checking it out
- AND removes the candidate's worktree
- BUT the primary branch, its index and its files stay unchanged

### scenario.delivery.keep-worktree — Keep the candidate's worktree on request

- GIVEN a ready change
- WHEN `concorde-deliver` runs with `keep_worktree: true`
- THEN the delivered branch is created as usual
- AND the candidate's worktree is kept and marked delivered
- AND later cleanup retries keep it unless a retry states `keep_worktree: false`

### scenario.delivery.pending-confirmed — Delivery reports pending entries and confirms any left

- GIVEN a ready change whose Specs declare some realization entries as pending
- WHEN `concorde-deliver` runs
- THEN the pending marker is removed for any remaining entry whose file now exists, as part of the delivered candidate
- AND the response and the receipt list the files confirmed at delivery and the entries that are still pending
- BUT an entry whose file does not exist stays pending in the delivered Specs

Because a candidate's files must equal its validated tree at delivery, and validation confirms
created files before recording that tree, delivery normally finds nothing left to confirm.

### scenario.delivery.not-ready — A change that is not ready is refused

- GIVEN a change whose status is not `ready`, or whose completion check no longer passes
- WHEN `concorde-deliver` runs
- THEN the Host stops with `incomplete_change` or the completion check's code
- BUT no branch is published

### scenario.delivery.stale-candidate — A candidate edited after validation is refused

- GIVEN a ready change whose candidate files changed after validation
- WHEN `concorde-deliver` runs
- THEN the Host stops with `stale_evidence`
- AND the change is marked `blocked` in phase `deliver`
- BUT the candidate's files are kept and no branch is published

### scenario.delivery.conflict — A conflicting candidate blocks delivery

- GIVEN a ready candidate that conflicts with the latest primary head
- WHEN `concorde-deliver` runs
- THEN the Host stops with `merge_conflict`
- AND the change is marked `blocked` in phase `deliver`
- BUT the candidate's files, the primary branch, its index and its files stay unchanged

### scenario.delivery.failed-checks — An integration that fails its checks is not published

- GIVEN a ready candidate whose integration with the latest primary head fails a configured check
- WHEN `concorde-deliver` runs
- THEN the Host stops with `failed_merge_checks`
- AND the change is marked `blocked` in phase `deliver`
- BUT no delivered branch is created and the primary branch stays unchanged

### scenario.delivery.cleanup-kept — Cleanup keeps a candidate that changed after delivery

- GIVEN a published delivery whose candidate worktree received new edits before cleanup
- WHEN cleanup runs
- THEN the Host stops with `stale_delivery`
- AND the worktree and its edits are kept for inspection
- BUT the delivered branch stays published

### scenario.delivery.retry — A retry after publication only finishes cleanup

- GIVEN a change whose delivered branch was published but whose cleanup failed or was interrupted
- WHEN a participating session requests delivery of the same change again
- THEN the Host only finishes cleanup, keeping the recorded `keep_worktree` choice unless the retry states another
- BUT no branch is published twice

### scenario.delivery.preview — A policy preview changes nothing

- GIVEN a change with a live candidate or a receipt
- WHEN `concorde-deliver` runs in `describe-policy` mode
- THEN the answer `described` explains the delivered branch, the default cleanup and the separate primary merge
- BUT no check runs and no branch, worktree or status changes

## Who may deliver

### scenario.delivery.session-rejected — A third worktree cannot deliver

- GIVEN a session whose worktree is neither the change's candidate nor the primary worktree
- WHEN it requests delivery of that change
- THEN the Host refuses with `delivery_session_required`
- BUT no branch is published

### scenario.delivery.nested-rejected — A nested capability invocation cannot deliver

- GIVEN a capability run that issues a `concorde-deliver` request of its own
- WHEN the nested request reaches the Host
- THEN the Host refuses with `delivery_session_required`
- BUT no branch is published

## Merging into the primary branch

### scenario.delivery.merge-primary — An explicit primary merge

- GIVEN a delivered change whose cleanup is complete
- AND the developer has authorized merging it
- WHEN a session in the primary worktree requests `concorde-deliver` with `merge_primary: true`
- THEN the Host verifies the merge of the delivered branch with the latest primary head and fast-forwards the primary branch to it
- AND records the merge commit, its tree and its checks in the receipt apart from the delivery's own evidence
- BUT a delivery request without `merge_primary: true` never merges into the primary branch

### scenario.delivery.merge-session-rejected — A primary merge from the candidate is refused

- GIVEN a delivered change whose candidate worktree was kept
- WHEN a session in the candidate worktree requests `merge_primary: true`
- THEN the Host refuses with `primary_session_required`
- BUT the primary branch stays unchanged

### scenario.delivery.merge-retry — A retried primary merge is only recorded

- GIVEN a primary merge that fast-forwarded the primary branch but was interrupted before the receipt recorded `merged`
- WHEN the primary merge is requested again
- THEN the Host records the merge as `merged`
- BUT it does not merge a second time

### scenario.delivery.dirty-primary — Local edits block the primary merge

- GIVEN a delivered change and a primary worktree with local or untracked changes
- WHEN the primary merge is requested
- THEN the Host refuses with `dirty_primary`
- BUT the local changes and the primary branch stay as they were

### scenario.delivery.merge-conflict — A conflicting delivered branch is kept

- GIVEN a delivered branch that conflicts with the latest primary head
- WHEN the primary merge is requested
- THEN the Host stops with `merge_conflict`
- AND the delivered branch and the receipt are kept
- BUT the primary branch, its index and its files stay unchanged

## Manual merges

### scenario.delivery.manual-merge — Record an ordinary-Git merge

- GIVEN a change whose candidate commit the developer merged into the primary branch with ordinary Git
- WHEN the user session records the merge commit from the primary worktree with cleanup outcome `pending`
- THEN the change status records the manual merge with the commit and the candidate commit
- AND the change is marked `merged` in phase `complete`
- BUT no merge is performed

### scenario.delivery.manual-merge-not-integrated — An unintegrated commit is not recorded

- GIVEN a change whose candidate commit is not contained in the named commit, or a commit not in the primary branch's history
- WHEN the user session records it as a manual merge
- THEN the Host refuses with `stale_evidence`
- BUT the change status stays unchanged

### scenario.delivery.manual-merge-cleanup — Update only the cleanup outcome of a recorded merge

- GIVEN a change with a recorded manual merge whose candidate worktree has since been removed
- WHEN the user session records cleanup outcome `removed` without naming a commit
- THEN the Host rechecks the recorded merge and updates only the cleanup outcome

### scenario.delivery.manual-merge-after-removal — A merge cannot be recorded after unrecorded cleanup

- GIVEN a change whose candidate worktree was removed before any manual merge was recorded
- WHEN the user session records a manual merge for it
- THEN the Host refuses with `stale_evidence`
- BUT no manual merge is recorded
