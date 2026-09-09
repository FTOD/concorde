```concorde-document
{
  "id": "document.implementation.worktree-lifecycle",
  "targets": [
    "implementation.worktree-lifecycle"
  ],
  "main_visible": false
}
```
# Worktree Lifecycle implementation

`implementation.worktree-lifecycle` follows Spec Protocol 2.1.0 and binds the exact files below. It is reused by `module.harness`, `module.development`.

## Responsibility

Realize shared worktree identity, candidate state, session handoff and delivery mechanics for its two Module consumers.

## Bound files

- `src/concorde/host/change_worktree.py`
- `src/concorde/host/session_handoff.py`
- `src/concorde/host/worktree.py`
- `src/concorde/host/worktree_delivery.py`
- `tests/concorde/host/unit/test_change_worktree.py`
- `tests/concorde/host/unit/test_session_handoff.py`
- `tests/concorde/host/unit/test_worktree_boundary.py`
- `tests/concorde/specification/test_worktree_lifecycle.py`

## Internal responsibilities

The following paths identify responsibility groups; the exact authority remains the file list above.

| File or source family | Responsibility |
| --- | --- |
| `src/concorde/host/change_worktree.py` | Persists candidate identity, component progress, gaps and worktree inventory. |
| `src/concorde/host/worktree_delivery.py` | Checks actual integration and coordinates destination updates and cleanup. |
| `src/concorde/host/worktree.py` | Inspects the current Git worktree identity and applies the declared isolation requirement. |
| `src/concorde/host/session_handoff.py` | Builds complete localized handoff information for a required new session. |

## Implementation interfaces, dependencies and constraints

Worktree inspection uses verified Git identities. Candidate worktrees are created from the primary worktree's committed head and, for the self-hosted checkout, built before the handoff so the successor session finds its own Skills. Candidate state records one change and its component progress. Session handoff emits complete bounded continuation information without supplying private worker transcripts. Delivery admits only source/primary participation, creates a per-change delivery ref with compare-and-swap, and removes the source unless explicitly retained. Final merging requires a separate merge_primary request from the primary session, verifies the latest integration under the repository lock, and records publication, cleanup and primary merge evidence separately. Primary write ownership is a session policy in addition to host transaction locking. Dependencies are Git, exact lifecycle records and the callers’ explicit authorization/current evidence; task text cannot choose another worktree as a permission workaround.

The exact ownership list above agrees with the registered binding. Source-family labels in the responsibility table are explanatory groups and never own additional or future files. A Module reference does not duplicate this ownership or make these documents part of a Module collection.

## Verification and shared changes

Handoff cases must cover complete localized prompts without filesystem side effects; candidate creation cases cover the self-hosted build and the unrelated-project case that must not build. Delivery cases cover stale evidence, dirty destination preservation, source-session deletion, explicit retention, independent delivery branches, explicit primary-only merging, integration failure and cleanup/primary-merge retry without repeat merge. Exercise Workflows, Installation and Permissions separately when shared files change.

These are verification obligations for implementation work, not a claim that checks were run during this Spec revision. A changed file, binding or Implementation Spec invalidates evidence for every registered using Module. Assess each consumer contract separately; missing public promises must be resolved in its Module Spec.
