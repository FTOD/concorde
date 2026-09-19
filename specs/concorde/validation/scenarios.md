# Validation scenarios

These precise specifications belong directly to the [Validation Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Semantic completeness](../spec/structure.md#terminology) | Defined in What structural validation tells you. |

## Validation

### scenario.validation.ready — Deterministic checks record readiness

- GIVEN the current candidate
- WHEN `concorde-validate` runs
- THEN the host runs deterministic Spec validation and every configured implementation check of every affected Module, and records readiness evidence bound to the exact candidate bytes
- AND validation never claims semantic completeness

### scenario.validation.blocked — A failed or stale check blocks readiness

- GIVEN a configured implementation check fails, is missing, or its previously recorded evidence no longer matches the current candidate bytes
- WHEN readiness is evaluated
- THEN the candidate is not recorded ready and the failing or stale check is reported

### scenario.validation.check-isolation — Checks cannot write their inputs or host logs

- GIVEN a configured implementation check and the current candidate
- WHEN validation runs the check
- THEN project writes, including writes to lifecycle records and logs, are denied by [Harness Module](../harness/module.md)
- AND the outside host saves private stdout/stderr and records passed, failed or timeout evidence with exit and digest identities
- AND unavailable enforcement blocks readiness with check_sandbox_unavailable while raw diagnostics stay in the host log
- AND check input, candidate tree and affected Module freshness checks still reject external changes

The detailed contract is [Current deterministic evidence](execution-reference.md#validation-validation-operation).
