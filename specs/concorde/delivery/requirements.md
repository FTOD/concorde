# Delivery requirements

These precise specifications belong directly to the [Delivery Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Worktree](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |

## Delivery

### req.development.single-primary-writer — Only one agent writes to primary

At most one agent SHALL own writes in the primary worktree at a time.

### req.development.primary-writes-serialized — Repository lock serializes primary writes

The host SHALL serialize shared lifecycle writes and final primary merges with the repository lock.
