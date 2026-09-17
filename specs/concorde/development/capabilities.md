# Choosing and composing operations

A Capability is the common executable unit for ordinary code, model work and composed workflows.
This lets the host check how operations fit together without inventing a separate ownership model
for every worker or library function.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Public capability](module.md#terminology) | Defined in Development capability host. |
| [Internal capability](module.md#terminology) | Defined in Development capability host. |
| [Capability](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Skill](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Public entry or internal operation

Developers invoke public capabilities through Skills or the common launcher. Some operations, such
as planning one already selected Module, are internal building blocks used by declared workflows.
Knowing an internal operation's name is not permission to invoke it directly.

For example, [Development Flow](../dev-loop/module.md) uses planning and implementation as separate steps. [Planning Module](../planning/module.md) returns
a plan; the [Implementation Module](../implementation/module.md) fulfills accepted tasks. The Flow chooses their order, while each provider
owns what its result means. A caller does not acquire the provider's responsibilities by composing it.

## Why data and authority are separate

Operations exchange declared inputs and results. Trusted host objects and permissions are not
caller-writable task data: otherwise a forged result could select more powerful tools or a different
workspace. The host checks declared composition as well as each invocation's actual permission grant.

Some operations make no model calls; others do, directly or through composition. This distinction
helps explain execution, but does not imply that filesystem or external effects are pure or repeatable.
The exact inventory, State channels, adapters and compatibility rules are in Implementation Specs;
the associated metadata remains the single machine-checked capability inventory.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#capabilities-capability-registry).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
