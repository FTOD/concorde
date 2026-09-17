# Validation requirements

These precise specifications belong directly to the [Validation Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Validation

### req.development.check-isolation — Configured checks use enforced read-only execution

Validation SHALL execute configured checks through Harness's OS-enforced project-read-only executor.
