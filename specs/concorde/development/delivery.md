```concorde-document
{
  "id": "document.development.delivery",
  "owner": "module.development",
  "main_visible": true
}
```
# Delivery capability


One linked worktree contains the entire in-progress revision for one top-level change. Its
`.concorde/worktree.json` records ownership, phase/status, target plans and task progress, per-component
Spec reconciliation and implementation outcomes, gaps and the exact validated tree. Already authored
component Specs may remain as draft bytes if another component blocks. Recovery resumes this explicit
state, and global consumer/provider agreement is checked only after the affected authors finish.

The primary worktree retains `.concorde/worktrees.json` with basic information about all live linked
worktrees, built from Git's worktree list and each linked worktree's own `.concorde/worktree.json`;
no other file of a linked worktree is read. Primary main cognition sees that inventory; secondary
main cognition also sees its own candidate identity and status. These are declared lifecycle inputs,
not hidden reads of another worktree's Specs or code: a candidate's draft Spec edits stay invisible
to an invocation in the primary worktree until they are delivered. Secondary AGENTS.md/CLAUDE.md
blocks remind newly opened agents of this scope.

Standard and fast loops end at ready. Request concorde-deliver with the selected change_id from
either its source worktree or the primary worktree. A third-worktree or nested session cannot
initiate delivery for that pair. The host verifies the exact candidate and its actual integration
with the current primary commit, then creates `concorde/delivered/<change_id>` in the shared Git
repository without checking it out. The branch is unique to this change; an existing unreceipted
branch or a checked-out destination is rejected. Publication uses an atomic create-only ref update.
Default delivery leaves the primary branch, index and project files unchanged, even if the primary
has local edits. It removes the source worktree and its local state after verification, including
when the source owns the invoking session. Only explicit keep_worktree:true retains it. The source
session ends after removal; further work requires a fresh session in an existing intended worktree.
Local prompt injection and control files never enter the delivered tree.

A separate request with merge_primary:true requires an already delivered receipt, explicit user
authorization to merge into the primary branch, and the primary worktree's owning outer session.
A generic delivery request does not authorize final merging. At most one agent may own writes in
the primary worktree, including maintenance; all other development agents use linked worktrees.
The host serializes shared lifecycle writes and complete primary merge transactions using the
repository lock. This is cooperative host enforcement; agents must respect the single-writer rule
for direct maintenance and Git commands as well.

Final merging verifies that the staged branch is unchanged and the primary branch is the recorded
destination, then computes and checks integration against the latest primary commit. Conflicts,
failed checks, local primary edits or concurrent input changes block the update and preserve the
delivered branch. Conflict repair after source deletion uses a new candidate worktree. The primary
branch need not be named main. Successful final merging retains the delivered branch and records its
own commit, tree and checks separately from staging evidence.

The primary delivery receipt distinguishes branch publication, cleanup and final primary merging.
Cleanup retries never republish a branch. Final merge retries never repeat an accepted merge; a
receipt written before the update permits recovery after interruption. After source removal, retries
use the primary session and recorded change_id. Explicit retention remains sticky on cleanup retry
unless keep_worktree:false is supplied. The receipt records that choice before branch publication
or a cleanup retry, so an interruption cannot silently turn explicit retention into removal.
No operation discards unrelated local edits.

Historical schema-1 receipts for the former direct-primary delivery retain their recorded target
and may finish cleanup without another merge. Their responses must not claim that the primary
branch was left unchanged. They are not staged-branch receipts and cannot authorize merge_primary.

Readiness and delivery also recheck the owner and every old/candidate context consumer of changed
Spec documents. Reference-only changes and provider inventory changes invalidate dependent review
identities even when the implementation reverse index is unchanged. Each consumer retains its
own context and code grant; no delivery check transfers provider ownership or authority. The
evidence collector binds complete resolutions and separately retained consumer review artifacts.
