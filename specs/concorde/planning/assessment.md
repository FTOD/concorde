# Is the specification sufficient for this task?

Context assessment asks whether the selected specification provides enough information to plan a
particular task. It does not implement the task or claim that the Spec answers every possible future
question.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Task sufficiency | Whether the admitted Spec provides the meaning necessary to plan this particular task, not every possible task. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Blocker](../module.md#terminology) | Defined in Concorde Framework. |
| [Internal operation](../development/module.md#terminology) | Defined in Development operation host. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |

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

Assessment is an internal operation used by declared workflows, not a standalone developer Skill.
The result and admission details are in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#assessment-context-assessment).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
