# Issue solving requirements

The Module-wide obligations of [Issue solving](module.md). The exact state, journal and step table
are in [Solve workflow](workflow.md); the [scenarios](scenarios.md) show the obligations in concrete
situations.

## Selection

### req.issue-solving.owner-bound — A selection never redirects work

Issue solving SHALL bind every request that selects an Issue to that Issue's owning Module.

A different `target_id` is refused, so selecting an Issue never widens a task's boundary.

### req.issue-solving.committed-issue — Only committed Issues are solved

Issue solving SHALL refuse to solve an Issue whose record file is not committed, unchanged, at
`HEAD` of the worktree the request starts in.

The refusal happens before any candidate exists. It keeps a solved Issue from being delivered while
an uncommitted copy of the same file remains in the primary worktree, where it would block the
primary merge.

### req.issue-solving.bookkeeping-in-place — Bookkeeping never creates a candidate

The `list`, `show`, `report` and `reopen` actions SHALL NOT create a candidate or launch a model.

## Solving

### req.issue-solving.no-edits — Solving edits no Spec or code

A solve SHALL NOT change any file other than the selected Issue's record and the change status.

A decision that needs a code or Spec change is handed back to the user session.

### req.issue-solving.host-closes — Only a Host step writes a solver disposition

Issue solving SHALL write a solver disposition only from a Host step that admitted a solve decision
correlated with an actual finished native child.

### req.issue-solving.verified-resolution — Resolution needs current verification

The solve workflow SHALL write a `resolved` disposition only after Issue-specific and ordinary
reviews completed without blocking findings on the Module's current Specs and implementation files.

### req.issue-solving.bounded-decisions — Solving is bounded

One solve SHALL launch the Issue solver at most six times for an unchanged set of inputs and
clarification.

### req.issue-solving.journal-first — The journal precedes the close

The Host SHALL save the closing journal in the change status before it writes a solver disposition
to the Issue.

### req.issue-solving.validated-close — A close survives only with a ready candidate

Issue solving SHALL restore the Issue's open bytes whenever the final validation after a close does
not answer ready.

### req.issue-solving.ready-boundary — Solving stops before delivery

A successful solve SHALL end at a ready candidate without delivering it or changing the primary
branch.
