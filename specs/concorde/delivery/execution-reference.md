# Delivery execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Delivery Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Delivery](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Delivery receipt](module.md#terminology) | Defined in Delivery. |
| [Delivered branch](module.md#terminology) | Defined in Delivery. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |

## Delivery operation {#delivery-delivery-operation}

Delivery consumes host-recorded candidate identity, progress and current validation/review evidence.
The [common worktree metadata](../development/interfaces.md#worktree-awareness) supplies those
records; the producer graph owns its ordering and progress policy. A candidate's draft Spec bytes
are not visible in the primary worktree before delivery.

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

### Design {#delivery-design}

#### Integration verification {#delivery-integration-verification}

Delivery validates its actual integration result in a temporary detached worktree. When that tree
contains `concorde.json`, it is a Concorde package checkout: the host calls `write_build` on that
checkout's own merged sources before Spec/package validation and configured checks. Untracked
build outputs do not alter the deliverable tree. Build or validation failure preserves both
participants and prevents the primary update; no stale-output gate is disabled or bypassed.

The producer graph need not be dev-loop. A directly authored verified candidate is admitted under the same completion, current review, pending-entry confirmation and integration gates. Missing, stale or incomplete evidence rejects delivery; no plan is invented to make evidence appear valid.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary graph is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new graph requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.
