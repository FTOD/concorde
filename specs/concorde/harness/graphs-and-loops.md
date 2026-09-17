# Flows and feedback

A Flow describes which operations can run and what selects the next step. A loop describes how
feedback can lead to another attempt. Separating the two makes it possible to explain both the
normal sequence and why repetition eventually stops.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Harness](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Snapshot](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Follow the normal path first

For a development change, the broad sequence is specification, planning, tasks, implementation,
checks and review. Each operation receives only its own admitted inputs. A review finding may
select an allowed repair path; it does not let the reviewer edit code itself.

A useful example is a failed acceptance case: the review identifies the violated promise, new tasks
address it, and the changed result is checked again. Repeating identical blocking feedback is not
progress. Limits and stopping rules prevent an indefinite cycle.

## Who makes a decision

Some decisions follow fixed program rules, such as rejecting missing input. Others use model
judgment, such as assessing whether a promise is missing. A human decision supplies intent or
accepts a proposed effect when the workflow requires it. These sources remain distinct so that a
model recommendation cannot stand in for required human approval.

## Why executable flows are inspectable

Concorde declares control flow through LangGraph, so the runtime and Studio can inspect the same
nodes and transitions. The conceptual sequence above helps explain the design; the exact executable
node names, state channels, branching and limits are maintained once in Implementation Specs.
A matching diagram proves agreement with the compiled topology, not that every decision is correct.

A stopped flow retains its progress. Resuming checks that the task and inputs are still current
before choosing a next step. Completing an inner worker or helper does not complete the enclosing
change, and reaching ready does not authorize delivery.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#graphs-and-loops-capability-flows-loops-and-feedback).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
