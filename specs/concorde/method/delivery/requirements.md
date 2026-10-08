# Delivery requirements

The Module-wide obligations of [Delivery](module.md). The commit and the output are defined in the
[contracts](contracts.md). The [scenarios](scenarios.md) show the obligations at work.

## Preconditions

### req.delivery.own-readiness — Delivery validates the whole workspace itself

Delivery SHALL commit only when all of these conditions hold:

- The readiness is ready.
- Delivery decided that readiness itself in the same run with Validation's steps.
- That readiness covers every commit on the bound branch since the base commit and every
  uncommitted change.

### req.delivery.committed-steps — Committed steps are deliverable

When all of these conditions hold, Delivery SHALL treat the workspace as new work to validate,
never as nothing to deliver:

- The workspace has no uncommitted changes.
- Its branch head is past the base commit.
- Its branch head is no [delivery commit](../../glossary.json#concept.delivery-commit) of the
  workspace.

Such a workspace is still delivered only under the other requirements, first
[its own readiness](#req.delivery.own-readiness).

### req.delivery.scenarios-verified — A code change ships only with tests for its scenarios

Except in a run given `--adoption`, Delivery SHALL refuse a workspace when both of these
conditions hold:

- The workspace changed code.
- A scenario it added or changed since its base commit has no test declaring that it verifies it.

Changed code is a changed path outside `specs/` and `.concorde/` that a
[Module](../../glossary.json#concept.module)'s realization binds, tests included. A test declares
what it verifies by its
[verification declaration](../../glossary.json#concept.verification-declaration).

The rule holds for every scenario a [Spec](../../glossary.json#concept.spec) document defines, at
every heading level Spec core accepts, and whichever Module owns it. A Module that binds no file
still owns scenarios a code change may add, as
[scenario.delivery.unrealized-scenarios](scenarios.md#scenario.delivery.unrealized-scenarios)
shows. A scenario changed when its section, from its heading to the next heading, differs from its
section at the base commit.

### req.delivery.blocked-reason — A refusal says its own reason

A delivery run that ends `blocked` SHALL explain in its error link the reason of its own code as
follows:

- For `nothing_to_deliver`, it says that the head is the base commit and no change waits.
- For `not_ready`, it names every blocking finding.
- For `unverified_scenarios`, it names every unverified scenario with its document.

### req.delivery.blocked-inert — A blocked delivery changes nothing

A delivery run that ends `blocked` SHALL leave the workspace, its index and its branch unchanged.

## The commit

### req.delivery.exact-content — The commit holds what was validated

A delivery commit SHALL contain exactly the uncommitted changes the readiness examined.

Its parent is fixed by [req.delivery.bound-branch](#req.delivery.bound-branch).

### req.delivery.staged-validated — Staging is proven to keep what was validated

Delivery SHALL commit only when a checkout of the staged index gives back each path the readiness
examined with the mode and content it examined, and each other path as the base commit holds it,
and otherwise fail with `staged_unvalidated`, naming every path that differs, and give the index
back as [req.delivery.atomic](#req.delivery.atomic) requires.

Git stages a file through the repository's clean filters and line-ending conversion. A clean filter
may rewrite a validated file while Git still sees the worktree as clean, as
[scenario.delivery.staged-unvalidated](scenarios.md#scenario.delivery.staged-unvalidated) shows.
A checkout passes the staged content through the smudge filters. So a filter that a checkout
reverses, such as Git LFS or line-ending conversion, changes nothing, as
[scenario.delivery.staged-filtered](scenarios.md#scenario.delivery.staged-filtered) shows. When
`core.fileMode` is false, Git ignores the executable bit, and so does this comparison.

### req.delivery.bound-branch — Commits go on the bound branch

Delivery SHALL create its commit only on the branch the
[workspace binding](../../glossary.json#concept.workspace-binding) names, with the validated head
as its only parent.

### req.delivery.marked — Every delivery commit is marked by its subject

Delivery SHALL give every delivery commit the subject `concorde: deliver <workspace>` and give no
other commit it creates that subject, making the commit even when it changes nothing.

### req.delivery.commit-verified — The commit is proven to hold what was staged

Delivery SHALL end a run that created a delivery commit `ok` only when all of these conditions hold,
and otherwise fail with `commit_unverified`, naming every difference, and take the commit off the
branch as [req.delivery.rejected-removed](#req.delivery.rejected-removed) requires:

- The commit's tree is the tree `git write-tree` recorded from the index after staging.
- Its subject is exactly the subject of the delivery message Delivery gave Git.
- Its only parent is the validated head.
- It is the head of the bound branch.
- The worktree is clean.

The repository's commit hooks run normally. A hook may change what is committed or the message it is
committed with. The recorded tree shows each path it changed. The subject shows whether it still
marks a delivery. Thus, the commit is exactly what was validated, marked as a delivery, or the run
says it is not. A hook that only adds to the body, such as a `Change-Id` trailer, changes no mark
and is accepted. The commit verified is the one `git commit` names as the one it created, never a
commit a post-commit hook made on top of it.

### req.delivery.rejected-removed — A rejected commit does not stay on the branch

When a delivery commit Delivery created in the run does not verify, Delivery SHALL move the bound
branch back to the validated head, only while that head is the commit's only parent and the branch
still points at the commit, leave the index and the worktree as they are, and say in the run's error
that it took the commit off the branch, or otherwise that the commit stays and why: that the branch
no longer points at it, naming the commit it points at, or that Git refused to move a branch that
still points at it, with Git's account.

A rejected commit left at the head would carry the subject that alone marks a delivery. Whoever
reads the branch could therefore take it for one, as
[scenario.delivery.hook-changed-commit](scenarios.md#scenario.delivery.hook-changed-commit) shows.
The index and the worktree keep what the commit held, so that what a hook changed can be inspected.

### req.delivery.history-kept — History is never rewritten

Delivery SHALL NOT amend, rebase, merge or push any commit, nor move its branch to a commit other
than the delivery commit it creates or, when it rejects that commit, back to the head it validated.

Restoring the index while undoing an uncommitted delivery, as
[req.delivery.atomic](#req.delivery.atomic) requires, changes no commit. Taking a rejected commit
off the branch, as [req.delivery.rejected-removed](#req.delivery.rejected-removed) requires, removes
only the commit the same run created.

### req.delivery.atomic — A failed commit gives the validated index back

When staging, its comparison or the commit fails, Delivery SHALL restore the index to the state the readiness
examined, leave the worktree as it is, and name in the run's summary and error every worktree path
whose mode or content is no longer what the readiness examined.

A failing commit hook, such as a formatter that rewrites files and then rejects the commit, may
leave edits in the worktree that the developer wants. Delivery therefore keeps them and names them
rather than undoing them, as
[scenario.delivery.hook-edits-kept](scenarios.md#scenario.delivery.hook-edits-kept) shows. Nothing
unvalidated is delivered, since the next delivery validates the worktree as it then is.

## Records

### req.delivery.commit-is-record — The commit is the only record

Delivery SHALL record a delivery only in its delivery commit, writing no
[task record](../../glossary.json#concept.task-record) and no other record of it.

Whoever needs to know whether and how often a workspace was delivered reads the delivery commits on
its branch, as the [contract](contracts.md#delivery-commit) defines them.

### req.delivery.already-delivered — A delivered head is reported, not repeated

When the branch head already is a delivery commit of the workspace and no uncommitted change
waits, Delivery SHALL NOT create a commit.

Once the existing commit verifies and its workspace validates again, such a run reports that
commit instead, as [scenario.delivery.recover](scenarios.md#scenario.delivery.recover) shows.

### req.delivery.recovered-referenced — A delivered head is referenced as found

The [trace node](../../glossary.json#concept.trace-node) of a delivery run that reports an
existing delivery commit SHALL reference that commit with the relation `found_commit`, and not with
`commit`.

`commit` names only what a node created, as
[Tracing requires](../../kernel/tracing/requirements.md#req.tracing.created-or-found). A recovered
delivery created none. Its trace still leads to the delivery it reported.

### req.delivery.recovered-verified — A delivered head is verified before it is reported

Delivery SHALL report an existing delivery commit at the branch head as delivered only when it has
exactly one parent, and otherwise fail with `commit_unverified`, naming the mismatch and committing
nothing.

A delivery commit is recognised by its subject alone. Any commit can carry that subject. A commit
with another number of parents, such as a merge given the subject, cannot be one Delivery created,
as [scenario.delivery.recover-unverified](scenarios.md#scenario.delivery.recover-unverified) shows.

### req.delivery.recovered-revalidated — A delivered head is validated again before it is reported

Delivery SHALL report an existing delivery commit at the branch head as delivered only when a
readiness it decided in the same run over every commit since the base commit is ready and, unless
the run was given `--adoption`, every scenario the workspace added or changed with code has a
verifying test, and otherwise end `blocked` as a new delivery would, with `not_ready` or
`unverified_scenarios`, committing nothing.

The subject and the one parent show only that Delivery may have created the commit. They never show
that what it holds is ready, as
[scenario.delivery.recover-not-ready](scenarios.md#scenario.delivery.recover-not-ready) shows.
