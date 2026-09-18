# Query and Routing requirements

These precise specifications belong directly to the [Query and Routing Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Context](../module.md#terminology) | Defined in Concorde Framework. |

## Query and Routing

### req.development.global-discovery — Discovery workers discover complete Module contexts

An Operation with discover context selection SHALL use a discovery-phase worker to discover complete Module Spec contexts.

### req.development.routing-hint-not-context — Routing hints only steer selection

A target or focus hint SHALL only steer selection.

### req.development.routing-hint-no-grant — Routing hints never grant context

A target or focus hint SHALL NOT itself grant context or replace explicit resolution.
