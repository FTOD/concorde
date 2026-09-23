# Delivery design

This topic explains the choices the [Delivery](module.md) entry summarizes: why each step is
recorded before it happens, what is verified, why nothing of the integrated tree runs as the Host,
and what the session check and the repository lock can and cannot guarantee. The exact transitions
are in [Delivery interface](records.md).

## Three recorded transitions

Publication, cleanup and primary merge are separate transitions, each recorded in the delivery
receipt before the Git reference it changes. If the process stops after publishing the branch, the
receipt shows the publication happened and a retry goes straight to cleanup; if it stops after the
primary merge, a retry sees the merge commit on the primary branch and only records it. Recovery
always looks at the actual Git state rather than assuming that a missing acknowledgement means
nothing happened.

## Verifying the actual integration

The primary branch may have moved since the candidate was validated, so verification runs on the
integration, not on the candidate alone. The integration commit is built with `git merge-tree`
without touching any worktree, checked out into a temporary detached worktree for verification, and
published with a create-only reference update. Before and after each verification the Host confirms
that neither the candidate nor the primary head moved.

## No build step

Delivery verifies with the Host's own Concorde package and never runs a build or any other program
of the integrated tree outside Check execution's boundary. Running the integrated tree's own code
as the Host would execute unverified code with the Host's authority. A project that needs build
freshness verified configures a check for it, which then runs in the check boundary like any other.

## No sandbox, deliberately

Delivery's own Git work (merging trees, creating commits, moving references, adding and removing
worktrees) runs with the Host's full authority; only the configured checks it runs are confined, by
Check execution. Nothing enforces that the Host's Git operations stay within the change's branches:
containment rests on the fixed sequence of steps and the refusals. This is deliberate, because
every step is Host code, not model output.

## The session check

Delivery's capability declaration asks admission to bind the request to the primary worktree
without a candidate; Delivery then checks the requesting session itself, from the starting worktree,
session root and nesting that admission records. Keeping the check inside Delivery keeps admission
free of provider rules. What is checked is the request's origin: a participating worktree and not a
nested capability invocation. A user session and a Task subagent working directly in the same
worktree are indistinguishable to the Host.

## One cooperative lock

All transitions and manual merge records run under the repository lock, which also serializes the
status writes of other Host requests. The lock orders Concorde's own writers but cannot stop someone
running Git directly, which is why one writer owns the primary worktree at a time by convention.

## Never discarding edits

A primary merge refuses a primary worktree with local or untracked changes, and cleanup refuses to
remove a candidate worktree whose files changed after delivery; that worktree is kept for
inspection.

## Observed, not performed

A manual merge record states facts the Host can verify from Git: the merge commit is in the primary
branch's history and contains the candidate's commit, and the candidate has no uncommitted
deliverable files. The Host cannot know how the merge was made or whether it was authorized; that
stays the developer's responsibility. A later cleanup-only update reuses the recorded merge, and a
merge cannot be recorded once the candidate was removed without one.

## Where the code lives

The delivery transitions live in `src/concorde/delivery/deliver.py`, the manual merge record in
`src/concorde/delivery/manual_merge.py`, and the declaration of Delivery's section of the change
status in `src/concorde/delivery/records.py`.
