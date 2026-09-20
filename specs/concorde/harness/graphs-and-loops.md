# Graphs and feedback

A Graph describes which operations can run and what selects the next step. A loop describes how
feedback can lead to another attempt. Separating the two makes it possible to explain both the
normal sequence and why repetition eventually stops.

## Terminology

| Term                                  | Meaning / definition                                                                                                                                                                               |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Graph](../module.md#terminology)     | Defined in Concorde Framework.                                                                                                                                                                     |
| [Operation](../module.md#terminology) | Defined in Concorde Framework.                                                                                                                                                                     |
| [State](../module.md#terminology)     | Defined in Concorde Framework.                                                                                                                                                                     |
| Graph Spec                            | The section of a Module's Implementation Specs that specifies one executable Graph by its State, its Nodes and its Edges, with a flowchart the Graph Spec check keeps equal to the compiled Graph. |
| [Worker](../module.md#terminology)    | Defined in Concorde Framework.                                                                                                                                                                     |
| [Ready](../module.md#terminology)     | Defined in Concorde Framework.                                                                                                                                                                     |
| [Delivery](../module.md#terminology)  | Defined in Concorde Framework.                                                                                                                                                                     |

## Follow the normal path first

The caller chooses retained Operations and their order. For example, after directly editing a
contract the caller may request Spec review, planning, tasks, implementation, validation and code
review. This is an example of caller choices, not a built-in development sequence. Each invocation
receives only its own admitted inputs. A review finding cannot let the reviewer edit code itself.

The caller can select current blocking code-review evidence for task repair and then recheck the
changed implementation. No automatic authoring, child development or review-repair loop runs.

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
before choosing a next step. Completing an inner worker does not complete the enclosing
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

For example, the admission Graph checks a request, workspace and configuration before dispatch.
Its conditional edges send a failed check directly to finalization. A reader can inspect that
actual stopping behavior without mistaking the caller's broader task sequence for a built-in graph.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#graphs-and-loops-operation-graphs-loops-and-feedback).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
