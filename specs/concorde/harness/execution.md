# Running a worker safely

The [Harness Module](module.md) turns a checked task into one fresh worker execution and accepts only a result for that
same task. It also runs configured deterministic checks through a separate, stronger filesystem
boundary. These are related services, but their security guarantees are not interchangeable.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Tool gate](module.md#terminology) | Defined in Harness. |
| [Capsule](module.md#terminology) | Defined in Harness. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Snapshot](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Issue](../module.md#terminology) | Defined in Concorde Framework. |

## A normal worker execution

Before launch, the host checks the worker definition, fixes the available information and narrows
tool and file access for the job. A Spec-only worker runs in a temporary workspace containing its
allowed documents; a code worker runs against the candidate with separately allowed code access.
After execution, the host checks the submitted result and verifies that the relevant inputs have
not changed. A process exiting successfully is not enough to establish task completion.

For example, a code reviewer can inspect its selected code but cannot repair it. A programmer can
change its allowed implementation files but cannot change the Spec to make an incorrect result look
correct. A stale input, invalid result, cancellation or timeout remains a distinct stopping outcome.
Authorized edits already made by a failed programmer can remain and need inspection before retry.

## Important security limits

Native Agents run through pi-subagents with fresh context and enforced terminal tool/delegation
ceilings. Their intended file, network and credential restrictions are prompt-level policy, not
OS confinement or proof of exclusive reads. In particular, the native programmer's shell is not
confined to its intended write paths by Concorde. Read-only reviewers have no shell/write/edit tools;
that tool ceiling does not prove which files their read tools examined.

The retained low-level Pi-RPC diagnostic/test utilities have a different boundary: their worker
extension checks tool/path policy and their Linux bubblewrap sandbox restricts process writes and
masks a fixed list of secret locations and other worktrees. Those utilities refuse unavailable
isolation and are not a selectable fallback for native capability failures. Their network remains
shared and provider credentials inside their run directory remain readable.

Configured checks and the tester command tool have an actual OS read-only governing-filesystem
boundary with separate temporary storage and process-tree cleanup. They refuse unavailable isolation;
they define no finer read, network or credential policy. A check needing a writable cache uses its
issued scratch, not the project. These guarantees must not be transferred to the native Agent itself.

## Why inputs and results are checked twice

Preparing a job and starting it are different moments. Rechecking prevents intervening file or
configuration changes from turning an earlier approval into permission for different work. Fresh
workers avoid hidden conversational assumptions; explicit results make the handoff inspectable.

Workers can report Issues through the [Issues Module](../issues/module.md) while continuing useful work. Accepted observations survive a later
failure, but neither an Issue receipt nor usage statistics means the task succeeded. The Module's
execution reference defines process, transport, environment, accounting and cleanup details.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#execution-agent-execution).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
