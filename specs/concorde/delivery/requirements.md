# Delivery requirements

These are the Module-wide obligations of [Delivery](module.md). The exact request, receipt and
transitions are in [Delivery records](records.md).

## Who may deliver

### req.delivery.participating-session — Only the two participating worktrees may deliver

Delivery SHALL accept a request only from a session whose worktree is the change's source worktree
or the primary worktree.

A session in a third worktree, a session served by a Concorde runtime from a third worktree of the
same repository, and a request nested more than one delegation level deep are refused with
`delivery_session_required`. A Task subagent working in one of the two worktrees may deliver.

### req.delivery.explicit-merge — Only an explicit request updates the primary branch

Delivery SHALL update the primary branch only for a `merge_primary: true` request from the primary
worktree's own session for a change whose delivery and cleanup are complete.

A request with `merge_primary` from another session is refused with `primary_session_required`,
and one for a change without a receipt with `delivery_required`.

## What delivery changes

### req.delivery.primary-unchanged — Delivery leaves the primary worktree alone

A delivery request without `merge_primary` SHALL NOT change the primary worktree's branch, index or
files.

### req.delivery.verified-integration — Only a verified integration is published

Delivery SHALL publish a delivered branch or update the primary branch only with an integration
commit that passed Spec validation and every configured check of the project in a temporary
detached worktree.

The verification runs on the integration with the latest primary head at that moment. When the
integrated tree is a Concorde package checkout, its own build runs first and must succeed.

### req.delivery.preserve-edits — Delivery never discards edits

Delivery SHALL NOT discard uncommitted edits in the primary worktree or in a candidate worktree.

A primary merge refuses a primary worktree with local or untracked changes, and cleanup keeps a
candidate worktree whose files changed after delivery.

## Recovery

### req.delivery.receipt-first — The receipt precedes every reference update

Delivery SHALL save the delivery receipt with the intended state before it updates the delivered
branch or the primary branch.

### req.delivery.no-repeat — Retries never publish or merge twice

A retried delivery SHALL NOT publish a delivered branch or merge into the primary branch a second
time.

A retry after publication only finishes cleanup, and a retry after an interrupted primary merge
only records the merge that already happened.

### req.delivery.primary-writes-serialized — The repository lock serializes transitions

The Host SHALL run every delivery transition and every shared lifecycle write under the repository
lock.
