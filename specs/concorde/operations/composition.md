# Choosing capabilities and composing Operations

The typed inventory distinguishes native Agents, native Workflows, finite Host tools and optional
StateGraph Operations. The compatibility `operations/` path and `operation_id` spellings are not
claims that every entry runs a Graph.
This lets the host check how admitted collaborators fit together without inventing a separate ownership model
for every worker or library function.

## Terminology

| Term                                        | Meaning / definition           |
| ------------------------------------------- | ------------------------------ |
| [Public operation](module.md#terminology)   | Defined in Operations.         |
| [Internal operation](module.md#terminology) | Defined in Operations.         |
| [Operation](../module.md#terminology)       | Defined in Concorde Framework. |
| [Host](../module.md#terminology)            | Defined in Concorde Framework. |
| [Graph](../module.md#terminology)           | Defined in Concorde Framework. |
| [Pi integration](../module.md#terminology)  | Defined in Concorde Framework. |
| [Worker](../module.md#terminology)          | Defined in Concorde Framework. |
| [Module](../module.md#terminology)          | Defined in Concorde Framework. |
| [Grant](../module.md#terminology)           | Defined in Concorde Framework. |

## Public entry or internal composition

Developers invoke public capabilities through the Pi tool; finite Host adapters use the common launcher. The outer
agent selects the target and orders calls; prepared native Agents/workflows remain bound to their exact Host-issued invocation. Knowing an internal name is not permission to invoke it directly.

For example, Planning returns a current plan and tasks, while Implementation fulfills accepted
tasks under its bounded grant. The caller chooses their order without acquiring either provider's
authority or bypassing current-input checks. Spec and registry edits are direct agent work, not
an authoring Operation or an implicit step in a development graph.

## Why data and authority are separate

Operations exchange declared inputs and results. Trusted host objects and permissions are not
caller-writable task data: otherwise a forged result could select more powerful tools or a different
workspace. The host checks declared composition as well as each invocation's actual permission grant.

Host services make no model calls; Agent entries and Workflows use native roles. Explicit
StateGraph Operations may call a trusted native service supplied by their embedding. This distinction
helps explain execution, but does not imply that filesystem or external effects are pure or repeatable.
The exact inventory, State channels, adapters and compatibility rules are in Implementation Specs;
the associated metadata checks the compatibility adapter inventory; [Agents](../agents/roles.md)
owns the separate role inventory.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#operations-operation-registry).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
