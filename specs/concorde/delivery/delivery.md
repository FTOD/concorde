# Publishing a verified change

Delivery is separate from finishing development. It publishes a verified candidate as an independent
branch; merging that result into primary is a second, explicitly authorized operation.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Delivery receipt](module.md#terminology) | Defined in this Module’s entry Terminology. |
| [Delivered branch](module.md#terminology) | Defined in this Module’s entry Terminology. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Delivery](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worktree](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Normal delivery

Request delivery with the candidate's change ID from its source session or the primary session.
The host verifies current evidence and integration with the current primary revision, then creates
the delivered branch. Primary's checked-out branch and files are not advanced by this default action.
**Successful default delivery removes the source worktree.** Request retention explicitly if it must
remain. A session in a removed worktree must end; later retries use the primary session and saved ID.

For example, ready means a proposed change has passed its required gates. Delivering it makes a
separate verified branch available; neither state means it is already merged into the main development
line. This separation keeps publication and acceptance into primary distinct.

## Merging primary

An explicit merge-primary request must come from primary's owning session after delivery. Only one
agent may write primary at a time. The host checks integration again because primary may have advanced
since staging. Conflicts, local edits, failed checks or changed inputs stop the merge without discarding
unrelated work. A generic request to deliver does not authorize this update.

## Why retries are recorded

Publication, source cleanup and primary merge can fail at different moments. Separate receipts let
cleanup resume without republishing and prevent an accepted merge from being repeated. Recovery
verifies actual state rather than assuming that a missing acknowledgement means nothing happened.
Exact receipt versions, transactions and integration mechanics are in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#delivery-delivery-capability).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
