# Preparing and coordinating work

The invocation host assembles a worker's task, information and permissions before execution.
Its job is to make the boundary explicit, not to decide the software's intended behavior.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Harness](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Snapshot](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

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
The exact batch and capability-node Flows are in the execution reference.

## Observing a run

Studio shows the same executable Flows used by local invocations, along with stage and worker events.
It is optional: normal CLI and Skill calls do not require the server. Policy preview shows the
intended access without launching a worker. Replaying a run may execute effects again and does not
waive current permission or lifecycle checks. Setup is described in the project Studio guide.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#host-invocation-host).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
