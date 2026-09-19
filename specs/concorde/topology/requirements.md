# Topology requirements

These precise specifications belong directly to the [Topology Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Ownership](../spec/registry.md#terminology) | Defined in Registry. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Context](../module.md#terminology) | Defined in Concorde Framework. |

## Topology

### req.topology.shared-document-agreement — Shared changes require owner authoring and consumer agreement

A referenced document change SHALL be applied only from its sole owner's proposal after compatibility
review in every affected consumer's resolved context.
