# Operations scenarios

These precise specifications belong directly to the [Operations Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Operation](../module.md#terminology) | Defined in Concorde Framework. |
| [Public operation](module.md#terminology) | Defined in Operations. |
| [Internal operation](module.md#terminology) | Defined in Operations. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |

## Operation catalog

### scenario.development.execute-unregistered — Unregistered or private operation refused

- GIVEN a `operation_id` that names no registered Skill, or a non-public operation invoked directly instead of through its composing operation
- WHEN the host admits the request
- THEN it refuses the request with `unknown_operation`
- AND no Agent is launched and no project file changes

See [non-public operations have no installed Skill](requirements.md#req.development.stage-no-skill) and
[non-public operations require declared composition](requirements.md#req.development.stage-in-process-only).
