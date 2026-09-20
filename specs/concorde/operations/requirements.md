# Operations requirements

These precise specifications belong directly to the [Operations Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term                                        | Meaning / definition           |
| ------------------------------------------- | ------------------------------ |
| [Operation](../module.md#terminology)       | Defined in Concorde Framework. |
| [Public operation](module.md#terminology)   | Defined in Operations.         |
| [Internal operation](module.md#terminology) | Defined in Operations.         |
| [Pi integration](../module.md#terminology)  | Defined in Concorde Framework. |
| [Context](../module.md#terminology)         | Defined in Concorde Framework. |

## Operation catalog

### req.operations.stage-no-skill — Non-public operations have no public entry

A non-public Operation SHALL have no public Pi catalog or direct launcher entry.

### req.operations.stage-in-process-only — Non-public operations require declared composition

A non-public Operation SHALL be reachable only in-process from an operation that declares it in its
composition.

### req.operations.stage-no-reselect — Bound operations preserve their context

An Operation with bound context selection SHALL NOT reselect or expand the frozen context its composing operation gave it.
