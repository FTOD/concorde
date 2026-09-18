# What structural validation tells you

Structural validation checks that a project's declared specification can be interpreted consistently.
It catches missing, ambiguous or contradictory records without deciding whether the intended software
behavior is correct or fully implemented.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Structural validation | Deterministic checks of document shape, identity, ownership, references and other declared consistency rules. |
| Semantic completeness | Whether the specification supplies the meaning needed for a task; valid syntax alone cannot establish it. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Registry](../module.md#terminology) | Defined in Concorde Framework. |
| [Reference](registry.md#terminology) | Defined in Registry. |
| [Document role](values.md#terminology) | Defined in Identities and versions. |
| [Document unit](values.md#terminology) | Defined in Identities and versions. |
| [Entity](../module.md#terminology) | Defined in Concorde Framework. |
| [Context](../module.md#terminology) | Defined in Concorde Framework. |
| [Evidence](../module.md#terminology) | Defined in Concorde Framework. |

## Registry shape

Each Module names the documents it owns, the responsibilities it contains or uses, the knowledge it
references and the files that realize it. These declarations are explicit so the validator can detect
a missing document, duplicate identity or conflicting owner rather than guess from directory names.
Both members of each document pair must be available and agree on identity and ownership.

For example, two Modules may rely on the same interface, but only one owns its canonical definition.
Registering two copies as if they were one agreement is an error. Two Modules listing the same code
file is different: both contracts can concern that realization and each needs affected-change checks.

## Reference and interface validation

A necessary definition must actually be in the selected context. A Markdown link to an excluded
provider does not satisfy that requirement. Complementary participants must select the same interface
version, and a diagram cannot invent undeclared entities. Scoped diagrams can omit irrelevant entities;
they need not become a second inventory.

Terminology follows the same rule: an imported term links directly to its defining table, and that
unit must be explicitly included. A table of unexplained names or forwarding links is not a substitute
for readable meaning. Structural checks verify placement and links; review still asks whether the
terms and explanations help the intended reader.

## Interpreting the result

Success means these mechanical checks passed for the assessed sources. It does not mean a retry rule
is sufficient for every failure, an implementation is correct, or a review is unnecessary. A missing
promise can remain a real gap even when every registered file exists. Code checks and independent
review provide different evidence rather than another spelling of structural validation.

## Precise specifications

The Module-owned [admission details](contracts.md#structure-registry-admission-details),
[requirements](requirements.md) and [scenarios](scenarios.md) define exact errors and checks.
