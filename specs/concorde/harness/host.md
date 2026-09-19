# Preparing and coordinating work

The [Development Module](../development/module.md) dispatches operation requests; when an operation
needs a worker, this Module's invocation host assembles that worker's task, information and permissions before execution.
Its job is to make the boundary explicit, not to decide the software's intended behavior.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |

## From request to result

The host selects the worker for the requested stage, obtains current instructions, fixes the
available Spec and task information, and narrows the allowed tools and files. It then selects runtime
settings and starts the checked worker. The executor independently checks the preparation before
launch and validates the returned result afterward.

For example, the same review operation can run for two Modules, but each reviewer receives its own
contract and code scope. The coordinator collects their results rather than merging their private
conversations or giving either reviewer the other's permissions.

## Why orchestration is separate from workers

The host controls ordering and admission; a worker reasons within one job. This prevents a useful
answer from becoming an unchecked command to run another stage. Sequential batches stop when an item
cannot proceed, so a later operation does not accidentally consume incomplete earlier work.
Two Graph Specs in the execution reference define these shapes exactly. The
[Operation node](execution-reference.md#host-operation-node-operation-node) runs one worker as a
single step of any Graph, and the
[Sequential work items Graph](execution-reference.md#host-sequential-work-items-graph-batch-graph)
runs independently admitted items one at a time and stops at the first that returns a result.

## Observing a run

Studio shows the same executable Graphs used by local invocations, along with stage and worker events.
It is optional: normal CLI and Skill calls do not require the server. Policy preview shows the
intended access without launching a worker. Replaying a run may execute effects again and does not
waive current permission or lifecycle checks. Setup is described in the project Studio guide.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#host-invocation-host).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
