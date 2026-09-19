# Review requirements

These precise specifications belong directly to the [Review Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Review coverage](module.md#terminology) | Defined in Review. |

## Review

### req.review.admitted-contract — Bind independent findings to current review inputs

Review SHALL return independent findings bound to its exact admitted task and current input revision.

### req.review.terminology-consistency — Check meaning rather than wording

Spec review SHALL assess every imported terminology restatement in its complete admitted reading collection for semantic consistency with its direct canonical definition.

Different wording is permitted; changes in scope, conditions, constraints, exceptions or obligation
strength are semantic differences. Source-only rows have no restatement to compare. Report coverage
and local/canonical locations, including missing or ambiguous definitions and unfinished comparisons;
never use text equality as a requirement or claim consistency for unassessed pairs.
