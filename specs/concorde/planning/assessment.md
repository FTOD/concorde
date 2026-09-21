# Is the specification sufficient for this task?

Context assessment asks whether the selected specification provides enough information to plan a
particular task. It does not implement the task or claim that the Spec answers every possible future
question.

## Terminology

| Term                                                      | Meaning / definition                                                                                            |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Task sufficiency                                          | Whether the admitted Spec provides the meaning necessary to plan this particular task, not every possible task. |
| [Spec](../module.md#terminology)                          | Defined in Concorde Framework.                                                                                  |
| [Module](../module.md#terminology)                        | Defined in Concorde Framework.                                                                                  |
| [Host](../module.md#terminology)                          | Defined in Concorde Framework.                                                                                  |
| [Blocker](../module.md#terminology)                       | Defined in Concorde Framework.                                                                                  |
| [Internal operation](../operations/module.md#terminology) | Defined in Operations.                                                                                          |
| [Pi integration](../module.md#terminology)                | Defined in Concorde Framework.                                                                                  |

## Before planning

The composing workflow supplies the task and the complete allowed Module Spec. The host checks that
required collaborators are declared, then a fresh assessor considers whether the task can be carried
out without inventing software behavior. A sufficient result allows planning; a missing necessary
promise names the question and the step it blocks.

For example, adding automatic retries requires knowing which failures are retryable. If that policy
is absent, the assessor asks for it rather than reading existing code and assuming it is the intended
contract. Independent tasks that do not need that policy can continue.

## Distinguish missing information from failure

An explicit prohibition means the task is unsupported, not unspecified. Contradictory promises need
reconciliation. A malformed request or failed execution is another kind of problem. These distinctions
help the caller choose clarification, correction or recovery instead of treating every stop as a Spec
gap. Reassessment uses current inputs; an unchanged blocker is not cleared by repeating the call.
For an obsolete author prerequisite, select a fresh context assessment for the accepted task,
after any necessary direct contract edits. This supersedes only the removed step, including when
its original revision is unknown or its execution failed; it never claims the old author succeeded.
Its observation and Issue remain in history,
and required independent review still needs fresh evidence; assessment never stands in for review.

Assessment is available as the explicit-target `concorde-context-solve` Operation through
the Pi `concorde` tool. Its run prepares the selected context and returns an exact native
context-assessor call. Invoke that call without overrides, then inspect the Host acceptance
attached to its result. The native model proposal and staging gate do not themselves establish
accepted sufficiency. Known dependency gaps stop before a child is launched.

The native assessor has fresh context and terminal tools, with an explicitly prompt-level read
policy rather than OS confinement. Cancellation, failed execution or changed inputs prevent
unsettled acceptance. Native planning reuses this same assessor role as the first child of its authored workflow;
its deterministic acceptance must establish sufficiency before the planner starts.
The result and admission details are in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#assessment-context-assessment).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
