# Framework invocation contracts

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Skill](module.md#terminology) | Defined in Concorde Framework. |
| [Operation](module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](module.md#terminology) | Defined in Concorde Framework. |
| [Ready](module.md#terminology) | Defined in Concorde Framework. |
| [Grant](module.md#terminology) | Defined in Concorde Framework. |
| [Worker](module.md#terminology) | Defined in Concorde Framework. |

Installed Skills use a single schema-3 operation invocation with `operation_id`, execute or describe-policy mode, configuration and a version-1 typed request. Unsupported versions, malformed requests and configuration mismatch fail admission. The result reports succeeded, blocked, failed or described; domain output still distinguishes a ready candidate, gap, conflict or completed answer. Describe-policy reports the bound grant without launching an Agent. Standard execution can create candidate state and invoke separately bounded Agents; only the admitted action can change files.
