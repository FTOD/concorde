# Delivery scenarios

These situations show how [Delivery](module.md) behaves. The obligations they demonstrate are
defined once in [Delivery requirements](requirements.md).

## Staging a change

### scenario.delivery.branch — Deliver a ready change to its own branch

- GIVEN a ready change selected by its `change_id`
- AND a request from its source worktree or from the primary worktree
- WHEN `concorde-deliver` runs
- THEN the Host rechecks the candidate's readiness, builds the integration commit with the current primary head and verifies it
- AND saves the delivery receipt and creates `concorde/delivered/<change_id>` without checking it out
- AND removes the candidate's worktree, unless the request set `keep_worktree: true`
- BUT the primary branch, its index and its files stay unchanged

### scenario.delivery.pending-confirmed — Delivery reports pending entries and confirms any left

- GIVEN a ready change whose Specs declare some realization entries as pending
- AND validation already confirmed the entries whose files the change created
- WHEN `concorde-deliver` runs
- THEN the pending marker is removed for any remaining entry whose file now exists, as part of the delivered candidate
- AND the response and the receipt list the files confirmed at delivery and the entries that are still pending
- BUT an entry whose file does not exist stays pending in the delivered Specs

Because a candidate's files must equal its validated tree at delivery, and validation confirms
created files before recording that tree, delivery normally finds nothing left to confirm.

### scenario.delivery.session-rejected — A third worktree cannot deliver

- GIVEN a session whose worktree is neither the change's source worktree nor the primary worktree
- WHEN it requests delivery or a primary merge for that change
- THEN the Host refuses with `delivery_session_required` or `primary_session_required`
- BUT no branch is published or merged

### scenario.delivery.retry — Retries finish the interrupted step only

- GIVEN a change whose delivered branch was published but whose cleanup failed or was interrupted
- WHEN a participating session requests delivery of the same change again
- THEN the Host only finishes cleanup, keeping the recorded `keep_worktree` choice unless the retry states another
- AND a retried primary merge whose merge commit is already on the primary branch is only recorded
- BUT no branch is published twice and no merge is repeated

## Merging into the primary branch

### scenario.delivery.merge-primary — An explicit primary merge

- GIVEN a delivered change whose cleanup is complete
- AND the developer has authorized merging it
- WHEN the primary worktree's own session requests `concorde-deliver` with `merge_primary: true`
- THEN the Host verifies the merge of the delivered branch with the latest primary head and fast-forwards the primary branch to it
- AND records the merge commit, its tree and its checks in the receipt apart from the delivery's own evidence
- BUT a delivery request without `merge_primary: true` never merges into the primary branch

### scenario.delivery.conflict — A conflict or failed check blocks the integration

- GIVEN a candidate or a delivered branch that conflicts with the latest primary head, or whose integration with it fails its configured checks
- WHEN delivery or the primary merge runs
- THEN the Host stops with `merge_conflict` or `failed_merge_checks`
- AND the candidate's files and any delivered branch are kept, and a candidate is marked blocked with that outcome
- BUT the primary branch, its index and its files stay unchanged

The conflict is resolved in a new or the existing candidate worktree, which is then validated
again before another delivery.
