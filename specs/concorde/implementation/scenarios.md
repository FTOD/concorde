# Implementation scenarios

These precise specifications belong directly to the [Implementation Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Acceptance task](../planning/tasks.md#terminology) | Defined in Making work verifiable. |

## Implementation

### scenario.implementation.admitted-work — Return complete fulfillment of the admitted tasks

- GIVEN a current accepted plan and nonempty task list bound to a selected Module
- WHEN the worker fulfills every task's acceptance within that Module's implementation grant and returns the complete task list
- THEN the host accepts completion only for those same tasks with their IDs and acceptance preserved and all complete flags true
- AND the host records accepted progress without declaring ready or changing Specs

The detailed contract is [Exact tasks and bounded code effects](execution-reference.md#implementation-implementation-operation).

## Implementation operation

### scenario.implementation.missing-tasks — Implementation has no authored tasks

- GIVEN an admitted selected target with no authored task list
- WHEN its declared composing caller requests implementation
- THEN the host rejects the request with missing_tasks before launching the programmer
- AND it does not invent tasks or grant implementation writes for that request

### scenario.implementation.incomplete-output — The result does not complete every task

- GIVEN a programmer invocation with a current accepted plan and nonempty task list
- WHEN its result omits an admitted task or leaves an admitted task incomplete
- THEN the host reports incomplete_tasks instead of accepting full implementation completion
- AND authorized code changes remain inspectable in the candidate without establishing readiness

### scenario.implementation.failed-execution — Recover after partial authorized edits

- GIVEN an implementation invocation has made authorized code edits in its selected Module's grant
- WHEN execution fails before a matching successful completion is accepted
- THEN the failure neither establishes task completion nor implies rollback of those code edits
- AND the host preserves the candidate and progress for inspection and recovery
- AND a subsequent attempt re-admits current task artifacts and context in a fresh invocation without wider permissions
