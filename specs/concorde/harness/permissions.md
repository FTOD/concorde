# Information and permission

Having a document available is different from being allowed to change it. The [Harness Module](module.md) derives a concrete
permission grant for each job, so a Module relationship or a model's request cannot silently widen
access.

## Terminology

| Term                                         | Meaning / definition           |
| -------------------------------------------- | ------------------------------ |
| [Tool gate](module.md#terminology)           | Defined in Harness.            |
| [Worker profile](module.md#terminology)      | Defined in Harness.            |
| [Worker](../module.md#terminology)           | Defined in Concorde Framework. |
| [Grant](../module.md#terminology)            | Defined in Concorde Framework. |
| [Host](../module.md#terminology)             | Defined in Concorde Framework. |
| [Module](../module.md#terminology)           | Defined in Concorde Framework. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry.           |
| [Worktree](../module.md#terminology)         | Defined in Concorde Framework. |

## How access is selected

The worker's profile declares its maximum kinds of access. The host narrows those limits to the task's
specific files and operations. Both must permit an action. Assessors and planners receive reading
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

Native tool/delegation ceilings are enforced, but native file/network/credential exclusions are
prompt-level policy. A native programmer's shell is not OS-confined to the declared file grant;
a native reviewer's lack of write/edit/shell tools does not establish exclusive reads.

The retained low-level RPC diagnostic/test utilities separately enforce a tool/path gate and a
Linux worker sandbox. Their fixed secret masks and shared network are not a universal secrets or
network boundary, and they are never a fallback for native execution. Configured checks and tester
commands use an actual OS read-only governing-filesystem boundary and issued writable scratch,
without a finer read/network/credential policy. [Execution](execution.md) explains these separate
surfaces and their failure behavior.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#permissions-permissions).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
