# Delivery scenarios

These precise specifications belong directly to the [Delivery Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Delivery](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worktree](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Delivery receipt](module.md#terminology) | Defined in Delivery. |
| [Delivered branch](module.md#terminology) | Defined in Delivery. |

## Delivery

### scenario.development.deliver-branch — Publish an independent delivery branch

- GIVEN a ready change selected by `change_id`, requested from its source or the primary worktree
- WHEN `concorde-deliver` runs
- THEN the host verifies participation, candidate evidence and actual integration, then publishes an independent `concorde/delivered/<change_id>` branch and removes the source worktree unless `keep_worktree:true`
- AND default delivery leaves the primary branch, index and project files unchanged

### scenario.development.deliver-merge-primary — Explicit primary merge

- GIVEN an already delivered receipt and an explicit user-authorized `merge_primary:true` request from the primary worktree's owning session
- WHEN the host processes that request
- THEN it verifies current integration against the latest primary commit and merges the delivered branch, recording its own commit, tree and checks separately from staging evidence
- BUT a generic delivery request without `merge_primary:true` never merges into the primary branch

See [only one agent writes to primary](requirements.md#req.development.single-primary-writer) and
[repository lock serializes primary writes](requirements.md#req.development.primary-writes-serialized).

### scenario.development.deliver-session-rejected — Delivery refused from an unrelated worktree

- GIVEN a session whose worktree is neither the change's selected source nor the primary worktree
- WHEN it requests delivery or final merging for that change
- THEN the host refuses it with `delivery_session_required` or `primary_session_required`
- AND no branch is published or merged

### scenario.development.deliver-conflict — Integration conflict blocks final merge

- GIVEN the candidate's actual integration against the latest primary commit fails its configured checks or conflicts
- WHEN final merging runs
- THEN the host blocks the merge with `merge_conflict` or `failed_merge_checks`, preserves the delivered branch, and leaves the primary branch, index and project files unchanged

The detailed contract is [Participating-session delivery](delivery.md).
