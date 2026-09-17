# Taking a change to a ready candidate

Development Flow coordinates the work needed for one intended change. The developer supplies the
behavior and constraints; the workflow stops at a verified candidate rather than delivering it.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Follow the normal path

The workflow selects an owner, prepares and reviews its specification, checks whether planning has
enough information, produces a plan and tasks, implements them, runs checks and obtains independent
code review. It reports ready only when the relevant completion evidence is current.
Specification Flow can run first on its own; the same task can then continue into development without
repeating accepted work whose inputs remain unchanged.

For example, adding retries first needs a clear rule for retryable failures. A missing rule pauses
the dependent work. Once specified, planning describes the change, implementation fulfills its tasks,
and checks and review assess the result. A stopped attempt retains the candidate and its progress.

## Reading completion and stops

Ready is not delivery or a merge. A Spec gap needs clarification; a failed check needs inspection;
an incompatible task or changed input needs fresh admission. These different stops are not all
"the Spec is incomplete." Explicit review skips remain recorded and cannot cancel a review already
required for this change. Skipping authoring also cannot waive a missing necessary contract.

## Repair and resume

Blocking code review has a bounded repair path: create repair tasks, implement, check and review
again. Repeated unchanged feedback or an exhausted limit stops rather than retrying forever. Other
non-successful outcomes wait for a decision or explicit correction. Resume rechecks saved intent and
inputs and reuses only work that remains valid; workers still start fresh conversations.

For a multi-Module change, each owner works within its own contract and permissions. Final checks
wait for all writers, because one repair of shared code can invalidate another consumer's evidence.
The exact executable Flow, advanced task-scope recovery and saved state are in Implementation Specs.

## Why these stages are separate

Authoring decides intended meaning, implementation fulfills it, and independent review challenges
that result. Keeping their authority and conversations separate helps prevent a worker from silently
weakening the contract to fit its own code. An explicit delivery decision follows readiness.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#development-development-agent-flow-and-revision-loops).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
