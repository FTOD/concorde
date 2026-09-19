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

### scenario.review.standalone — Public review without a development change

- GIVEN an initialized project without a managed development change or preexisting Issue record
- AND a task with optional target/focus routing hints and no review-mode selector
- WHEN the user invokes `concorde-spec-review` or `concorde-code-review` through its public Skill or Studio entry
- THEN a Spec-only router selects one owning Module and a separate fresh reviewer receives its complete contract and, for `concorde-code-review`, only its admitted implementation files and scoped changes
- AND neither Agent receives write, network or credential authority
- AND the host returns typed review coverage, findings, gaps and completion status, persisting the review report without creating a development change or changing project Specs or implementation
- AND an unmanaged Git checkout uses HEAD as the scoped change baseline

The detailed contract is [Independent current review](execution-reference.md#review-independent-review-operation).

### scenario.review.terminology-consistency — Compare local restatements with canonical meaning

- GIVEN an admitted Spec collection with imported terminology rows and their complete canonical defining units
- WHEN `concorde-spec-review` assesses that collection
- THEN every local restatement is checked for semantic consistency with its direct canonical definition, including unchanged and referenced reading documents
- AND different wording is allowed without requiring text equality
- AND additions, omissions, contradictions or consumer-specific behavior that change shared meaning are reported with local and canonical locations
- AND coverage identifies checked term/source pairs or explicitly states that no imported restatements exist
- AND missing, ambiguous or unassessed comparisons are reported as gaps or incomplete coverage, never silently counted as consistent

### scenario.review.separate-entries — Review authority follows the selected Operation

- GIVEN an initialized project and a standalone review task
- WHEN a caller selects a public review Operation
- THEN `concorde-spec-review` selects only the Spec reviewer and `concorde-code-review` selects only the code reviewer
- AND a request containing review_mode is rejected rather than changing that Operation's authority
- AND the retired `concorde-review` entry is rejected without an alias or implicit migration
