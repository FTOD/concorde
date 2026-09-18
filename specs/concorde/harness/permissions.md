# Information and permission

Having a document available is different from being allowed to change it. The [Harness Module](module.md) derives a concrete
permission grant for each job, so a Module relationship or a model's request cannot silently widen
access.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Tool gate](module.md#terminology) | Defined in Harness. |
| [Worker profile](module.md#terminology) | Defined in Harness. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |

## How access is selected

The worker's profile declares its maximum kinds of access. The host narrows those limits to the task's
specific files and operations. Both must permit an action. Spec authors and planners receive reading
access without source-code writes; programmers may write only the selected implementation scope;
reviewers remain read-only.

For example, referencing another Module's specification makes its selected documents readable,
but does not make its source files writable. A task that needs a different owner's code must obtain
a separately authorized invocation, not reinterpret a reference as permission.

## Why the boundary is rechecked

Permissions are bound to current inputs and the intended worktree. A mismatched workspace or changed
input invalidates the earlier preparation. A rejection stops the operation; retrying with broader
access is not an automatic recovery strategy.

## Know the enforcement limit

The worker's tool gate enforces its tool and path policy inside the agent process, and the worker
sandbox enforces the same grant on the process itself, so a shell command cannot write outside the
grant or read the developer's secrets. **The sandbox does not restrict the network and masks a
fixed list of secret locations.** Configured deterministic checks use a separate boundary of the
same kind. [Execution](execution.md) explains these limits and supported platforms. Exact policy
records and permission compilation interfaces are in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#permissions-permissions).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
