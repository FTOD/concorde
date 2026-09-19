# Preparing and coordinating work

Every operation request enters through Harness admission before any provider runs. Admission checks
the request, binds it to a workspace and hands it to the Operations dispatch; when an operation needs
a worker, this Module's invocation host assembles that worker's task, information and permissions
before execution. Its job is to make the boundary explicit, not to decide the software's intended
behavior.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Public operation](../operations/module.md#terminology) | Defined in Operations. |
| [Internal operation](../operations/module.md#terminology) | Defined in Operations. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |

## From request to result

<a id="entity.harness.admission"></a>

A developer invokes a public operation through its Skill, the Pi session tool or the common
launcher. Operation admission is the one boundary every such request crosses. It checks the
operation, the request and the configuration, binds the invocation to the worktree it was started
in, and only then hands the admitted request to the
[Operations dispatch](../operations/module.md), which selects the operation's entry or binds its
owning Module. Invalid requests stop before any worker runs. Internal operations are available only
to declared composing callers, not simply because someone knows their name.

For example, a standalone review and a development request use the same admission boundary, but
review returns findings while development may create a candidate. A successful host response must
still be read for the operation's result: answered, ready, blocked or another declared outcome.
Admission, the provider's own domain outcome and an execution failure stay distinct, so a caller
never mistakes a stopped task for a crashed one.

Mutating work requested from the primary worktree runs in an isolated candidate the host creates
from the committed base: admission relays the request to that candidate's own launcher and returns
its result, while the requesting session stays where it is. Uncommitted primary edits are not
silently carried into it. Resuming preserves the saved task and workspace identity; incompatible
input is rejected rather than applied to another change.

## Preparing a worker

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
Three Graph Specs define these shapes exactly. The
[admission Graph](admission.md#graphs-operation-admission-graph-operation-graph) runs every request
and ends it with one typed result envelope, the
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

See the Module-owned [operation admission contracts](admission.md) and
[execution and record contracts](execution-reference.md#host-invocation-host).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
