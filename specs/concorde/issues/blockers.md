# Problems that block a task

A recorded Issue and a task's Blocker have different lifecycles. Keeping them separate lets work
continue where it is safe without pretending that every recorded problem has been solved.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Issue](../module.md#terminology) | Defined in Concorde Framework. |
| [Blocker](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Disposition](lifecycle.md#terminology) | Defined in Solving a recorded problem. |

## A concrete example

Suppose a task needs a rule for retrying a failed payment, but the Spec does not define that rule.
The missing promise is recorded as an Issue and blocks planning that behavior. Another independent
task can still proceed. Finding a harmless documentation typo during the same run can produce an
advisory Issue without blocking either task.

## Repair and reassessment

The [Issues Module](module.md) manages problem reports and their dispositions;
the host retains the task's dependency, and the phase's reassessment decides when it is released.

After a necessary promise is supplied, the dependent phase reassesses its task against the current
Spec. Its old blocker is released only when the new accepted result supports proceeding. A failed
or unrelated assessment cannot clear it. A workaround may release a task's dependency while leaving
the underlying Issue open; closure needs its own evidence-grounded decision.

## Why history remains

Tasks may be reworded or replanned. Problem identity and saved observations must survive those edits,
otherwise a renamed task could silently lose its unresolved dependency. Reports accepted during a
worker run also survive a later cancellation or invalid result. That persistence records an
observation, not successful completion of the worker's job.

Results from the [Review Module](../review/module.md) apply to the inputs they examined. Changed code or relevant Spec invalidates that
evidence; closing an Issue does not rewrite a review as passed. Exact blocker records and release
rules are defined in the execution reference.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#review-and-gaps-attributed-issue-blockers-and-host-history).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
