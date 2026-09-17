# Managed runtime

A caller supplies package/project roots and a reviewed runtime plan; this Module does not select
business requirements or agent context.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Installation](installation.md#terminology) | Defined in Installing and updating Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Planning before provisioning

Plan against the actual target and its current receipt before creating or replacing a managed
runtime. The plan distinguishes creation, verified reuse, rebuild and ownership conflict. Inspect it
before provisioning: an apparently compatible environment still needs identity and health checks,
and a conflict is not permission to adopt or delete another environment.

Provisioning is separate from launching a worker or opening a graph. It prepares the locked Python
dependencies, viewer and worker extensions that those operations rely on, then records observed
identity only after verification succeeds. Changed package or lock inputs require replanning rather
than treating an old receipt as permanent evidence. The calling installation transaction owns its
rollback boundary; no provisioning request supplies business behavior or wider agent authority.

### Effects, failures and retries

Provisioning may create the environment, acquire the locked dependencies, viewer and Pi worker extensions, run verification
processes and write the owned receipt. Malformed requirements, ownership conflicts, unsupported
actions, failed processes or mismatched installed identity raise `ManagedRuntimeError(ValueError)`;
filesystem/process exceptions may also propagate.

The required replacement design preserves the previous valid runtime until the replacement is
verified and restores it after a failed rebuild; this Module's Unresolved information names the gap
between that design and the current provisioning implementation. Replan from actual state before
retrying; package/lock changes require a new plan.

## Precise specifications

The Distribution Module owns the exact obligations and interface details in [contracts](contracts.md), [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.
