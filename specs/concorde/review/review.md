# Reviewing a task independently

Review asks whether a current specification or implementation supports the requested work. A fresh
reviewer examines the allowed evidence and reports findings; it cannot repair files while reviewing.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Review coverage](module.md#terminology) | Defined in Review. |
| [Advisory finding](module.md#terminology) | Defined in Review. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Choose the question and mode

Use Spec review to examine intended behavior and design. Use code review to compare the allowed
implementation with that contract. Supply the task and constraints so the reviewer can select useful
representative cases rather than claim to prove everything. A standalone request selects its owning
Module and returns a report without creating a development candidate.

For example, reviewing a retry change includes its promised failure behavior and affected consumers.
An unrelated pre-existing limitation may be reported as advisory rather than automatically becoming
work required by this change. A missing contract necessary for the retry decision can block it.

## Read the result correctly

No findings means the bounded review completed without finding a problem in the work it covered.
It is not universal proof. Findings identify a concrete problem, evidence and its effect on the task.
An incomplete or failed review is not a clean review. A skipped review is also distinct from success.
The caller decides whether an admitted repair is appropriate; the reviewer itself does not execute it.

## Why freshness and independence matter

A review of yesterday's code cannot establish today's changed revision. The host binds the result
to current inputs and rejects stale evidence. Each reviewer gets a fresh conversation and read-only
access so an author's assumptions or edits cannot silently become review evidence.

When a changed file serves several Modules, each affected owner is reviewed against its own contract.
Only their results are aggregated; one reviewer does not acquire another Module's code. Exact input
identities, type fields, scope calculations and status mappings are in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#review-independent-review-capability).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
