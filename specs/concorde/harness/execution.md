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

The worker tool gate checks tools and paths inside the agent process; the worker sandbox around
that process bounds everything else it does, including a shell command it was granted. Inside the
sandbox the host filesystem is read-only, the developer's credential locations, agent-client state
and every other worktree of the repository are masked, only the grant and the run directory are
writable, and the temporary directory and process namespace are private. **The network is shared,
because the process contacts its model provider with the developer's credentials, which it can read
inside its run directory; the masks are a fixed list.** Both boundaries require Linux with a working
system bubblewrap/namespace setup; an unavailable sandbox refuses the launch rather than running the
worker unconfined. Treat these limits as deployment constraints, not as implementation details a
user can safely ignore.

Configured checks use the same kind of boundary as a read-only project mount with separate temporary
storage. A check that needs to write a project cache must use the issued temporary area instead; an
unavailable boundary blocks the check rather than falling back to unrestricted execution.

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
