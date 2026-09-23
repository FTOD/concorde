# Delivery requirements

These are the Module-wide obligations of [Delivery](module.md). The exact request, receipt and
transitions are in [Delivery interface](records.md).

## Who may deliver

### req.delivery.participating-session — Only the two participating worktrees may deliver

Delivery SHALL accept a request only when it starts in the change's candidate worktree or the
primary worktree and is not a nested capability invocation.

A session in a third worktree, a request served by a Concorde runtime from a third worktree of the
same repository, and a request issued by another capability's run are refused with
`delivery_session_required`. A Task subagent working directly in one of the two worktrees may
deliver.

### req.delivery.explicit-merge — Only an explicit request updates the primary branch

Delivery SHALL update the primary branch only for a `merge_primary: true` request that starts in
the primary worktree, is not a nested capability invocation, and names a change whose delivery and
cleanup are complete.

The developer's authorization of the merge is not something the Host can verify; the Host verifies
only where the request starts and that it is not nested.

## What delivery changes

### req.delivery.primary-unchanged — Delivery leaves the primary worktree alone

A delivery request without `merge_primary` SHALL NOT change the primary worktree's branch, index or
files.

### req.delivery.verified-integration — Only a verified integration is published

Delivery SHALL publish a delivered branch or update the primary branch only with a commit that
passed Spec validation and every configured check of the project in a temporary detached worktree.

The verification runs on the integration with the latest primary head at that moment, using the
Host's own package.

### req.delivery.no-foreign-code — Delivery runs no code of the integrated tree as the Host

Delivery SHALL NOT run a build or any other program of the integrated tree outside Check
execution's read-only check boundary.

### req.delivery.preserve-edits — Delivery never discards edits

Delivery SHALL NOT discard uncommitted edits in the primary worktree or in a candidate worktree.

A primary merge refuses a primary worktree with local or untracked changes, and cleanup keeps a
candidate worktree whose files changed after delivery.

### req.delivery.deterministic — Delivery runs no model

Delivery SHALL NOT start any worker or model.

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

The Host SHALL run every delivery transition and every manual merge record under the repository
lock.

## Manual merges

### req.delivery.manual-merge-observed — Recording a merge performs nothing

Recording a manual merge SHALL NOT perform, authorize or undo any merge.

### req.delivery.manual-merge-integrated — Only an integrated candidate is recorded as merged

Delivery SHALL record a manual merge only for a commit in the primary branch's history that
contains the change's candidate commit.
