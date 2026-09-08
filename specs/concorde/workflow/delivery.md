```concorde-document
{
  "id": "document.workflow.delivery",
  "targets": [
    "domain.workflow"
  ],
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
worktrees. Primary main cognition sees that inventory; secondary main cognition also sees its own
candidate identity and status. These are declared lifecycle inputs, not hidden reads of another
worktree's Specs or code. Secondary AGENTS.md/CLAUDE.md blocks remind newly opened agents of this scope.

Standard and fast loops end at ready. Request concorde-deliver with the selected change_id from
either its source worktree or the destination primary worktree. A third-worktree or nested session
cannot initiate delivery for that pair. The host verifies the exact candidate and actual integration
result, then merges into the primary worktree's checked-out branch, whose name need not be main.
It retains the source when that worktree owns the active session or keep_worktree:true is requested;
otherwise it removes the source and its local state. Local prompt injection and control files never
enter the merged tree. A primary delivery receipt distinguishes an accepted merge from pending cleanup,
allowing retries without another merge. Destination local edits block delivery and remain untouched.
