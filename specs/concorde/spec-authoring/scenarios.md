# Spec Authoring scenarios

These precise specifications belong directly to the [Spec Authoring Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ownership](../spec/registry.md#terminology) | Defined in Registry. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |

## Spec Authoring

### scenario.spec-authoring.admitted-work — Apply valid owner-bound replacements

- GIVEN a selected Module's complete current Spec and an explicit authoring task
- WHEN a fresh Spec author returns complete owned replacements whose identity, metadata and before-state remain valid
- THEN the host applies the accepted replacements after the required affected-consumer compatibility checks
- AND the author has no direct project write authority and the response retains artifact references to accepted output

The detailed contract is [Owner-only Spec replacements](execution-reference.md#authoring-spec-authoring-operation).

## Spec authoring operation

### scenario.spec-authoring.gap — Missing meaning prevents replacements

- GIVEN the selected Module's complete Spec lacks meaning necessary for the authoring task
- WHEN the fresh author cannot complete its owned replacements without inventing that meaning
- THEN it returns attributed gaps with no document replacements
- AND existing document bytes and unresolved blockers remain available for explicit repair

### scenario.spec-authoring.foreign-output — A consumer cannot replace its provider's document

- GIVEN a selected Module references a document owned by another Module
- WHEN its author proposes a replacement for that foreign document
- THEN the host rejects the replacement rather than treating reference inclusion as ownership
- AND project document bytes and prior blockers remain unchanged

### scenario.spec-authoring.stale-output — Changed inputs reject author output

- GIVEN an author prepared owned replacements from a frozen current context
- AND admitted source bytes, context or configuration change before acceptance
- WHEN the host rechecks those replacements
- THEN it rejects the stale or incompatible output without applying replacements
- AND previous document bytes and blockers remain available for a fresh authoring invocation

### scenario.spec-authoring.invalid-output — Invalid metadata prevents application

- GIVEN a selected Module and its currently registered document identities and metadata
- WHEN ordinary authoring returns replacements with invalid identity or metadata
- THEN the host rejects the replacements without applying them
- AND successful assessment alone does not clear the previous authoring blockers
