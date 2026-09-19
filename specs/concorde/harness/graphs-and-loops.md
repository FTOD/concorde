# Graphs and feedback

A Graph describes which operations can run and what selects the next step. A loop describes how
feedback can lead to another attempt. Separating the two makes it possible to explain both the
normal sequence and why repetition eventually stops.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [State](../module.md#terminology) | Defined in Concorde Framework. |
| Graph Spec | The section of a Module's Implementation Specs that specifies one executable Graph by its State, its Nodes and its Edges, with a flowchart the Graph Spec check keeps equal to the compiled Graph. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Delivery](../module.md#terminology) | Defined in Concorde Framework. |

## Follow the normal path first

For a change handled by [Development Graph](../dev-loop/module.md), the broad sequence is specification, planning, tasks, implementation,
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

## Why executable graphs are inspectable

Concorde declares control flow through LangGraph, so the runtime and Studio can inspect the same
nodes and transitions. The conceptual sequence above helps explain the design; the exact executable
node names, state channels, branching and limits are maintained once in Implementation Specs.
A matching diagram proves agreement with the compiled topology, not that every decision is correct.

A stopped graph retains its progress. Resuming checks that the task and inputs are still current
before choosing a next step. Completing an inner worker or helper does not complete the enclosing
change, and reaching ready does not authorize delivery.

## Reading a Graph Spec

Each Operation is explained where the Module that owns it is specified. When the Operation runs a
Graph, that Module's Implementation Specs hold the Graph's **Graph Spec**, and no other page draws
it again. A Graph Spec answers three questions in LangGraph's own terms:

- **State**: what the Graph carries between steps. These are named channels, such as the last
  stage's output or accumulated artifact references, plus the durable candidate records the steps
  read and write.
- **Nodes**: what runs at each step and what it reads and writes. A node is one Operation: a
  deterministic step, one model-backed worker, or another Graph used as a single step.
- **Edges**: what decides the next step. After a node finishes, either an edge function reads a
  State channel the node wrote, or the node itself names its successor. The diagram labels every
  branch with the condition that selects it.

For example, in the development Graph the `review_code` node reads the Spec, the changed files and
the tasks, and writes its review results. Its Edges say that it names its own successor: `ready`
when no finding blocks, `tasks` for a bounded repair, or `summarize` to stop. A reader can follow
one change through the Graph without reading the implementation, and the Graph Spec check keeps
that picture equal to the Graph that actually runs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#graphs-and-loops-operation-graphs-loops-and-feedback).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
