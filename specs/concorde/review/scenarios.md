# Review scenarios

These precise specifications belong directly to the [Review Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Issue](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Review coverage](module.md#terminology) | Defined in Review. |

## Review

### scenario.development.standalone-review — Public review without a development change

- GIVEN an initialized project without a managed development change or preexisting Issue record
- AND a task with review_mode spec or code and optional target/focus routing hints
- WHEN the user invokes the public `concorde-review` Skill or its Studio entry
- THEN a Spec-only router selects one owning Module and a separate fresh reviewer receives its complete contract and, in code mode, only its admitted implementation files and scoped changes
- AND neither Agent receives write, network or credential authority
- AND the host returns typed review coverage, findings, gaps and completion status, persisting the review report without creating a development change or changing project Specs or implementation
- AND an unmanaged Git checkout uses HEAD as the scoped change baseline

The detailed contract is [Independent current review](execution-reference.md#review-independent-review-operation).
