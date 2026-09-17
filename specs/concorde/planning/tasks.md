# Making work verifiable

Task authoring turns an accepted plan into concrete implementation work with acceptance conditions.
A useful task tells the programmer what must work and what evidence it can produce, without claiming
that later independent checks or delivery have already happened.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Acceptance task | One item of implementation work with a stated condition for judging whether it has been fulfilled. |
| Reserved task ID | An identity retained by task history that a new task must not reuse. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## From plan to tasks

A fresh task author reads the current plan and Module Spec. It returns a nonempty list whose tasks
start incomplete. The host preserves task identities and history, rejects collisions and accepts the
new list only when it belongs to the current change. The author does not complete tasks or edit code.

For example, a task may require implementing a specified retry policy and exercising it with tests
available in the programmer's grant. It must not require an independent reviewer to have approved the
change before the programmer can finish its own step. That would reverse the workflow's dependencies.

## Repair without losing history

After blocking code review, an admitted repair can produce new tasks addressing the findings. The
old list remains history rather than being rewritten to look as if it always described the repair.
Task-scope recovery similarly corrects a phase-boundary mistake without weakening software acceptance.
If the intended behavior has changed enough to need a new plan, the author reports that instead.

Only the composing workflow may admit repair feedback. Exact fields, reserved-ID rules and failure
outcomes are defined in the Module's execution reference and interface contracts.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#tasks-task-authoring-capability).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
