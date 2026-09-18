# Turning intended behavior into a plan

Planning explains how to achieve an admitted task from its current specification. It starts only
after the task has enough specified meaning, and ends with a plan rather than tasks, code or a ready
candidate.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Task sufficiency](assessment.md#terminology) | Defined in Is the specification sufficient for this task? |

## Normal planning

The workflow selects a Module and asks [context assessment](assessment.md) whether its Spec supports
the request. A fresh planner then describes the work needed, including separately owned participants
when necessary. The host accepts a nonempty plan tied to that task and Spec revision. Task authoring
uses that plan in the next step.

For example, a change to checkout that relies on inventory identifies Inventory's required behavior
as separately owned work. It does not assume that a Checkout planner may inspect or modify Inventory's
implementation. Each participant needs its own bounded invocation.

## Why plans become stale

A plan depends on intended behavior. If the Spec or task changes, the old plan might solve the wrong
problem even if its text still looks plausible. The host rechecks its inputs before reuse. Empty,
invalid or stale output leaves the previous accepted plan intact but does not make it current.
The planner uses Spec information and admitted reference material, not implementation contents.

The exact planning Graph and artifact contract are maintained in Implementation Specs; the explanation
here is the normal reasoning path, not a second execution graph.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#plan-planning-operation).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
