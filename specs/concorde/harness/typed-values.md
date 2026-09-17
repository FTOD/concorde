# Checking values across boundaries

A task result needs an agreed meaning and a checkable shape. Typed values let the host recognize which
kind of result it received and reject incompatible or malformed data before another stage uses it.
They do not prove that the underlying claim is true.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Contract](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Review coverage](../review/module.md#terminology) | Defined in Review. |
| [Structural validation](../spec/structure.md#terminology) | Defined in What structural validation tells you. |
| [Semantic completeness](../spec/structure.md#terminology) | Defined in What structural validation tells you. |

## A normal handoff

A planner returns a plan, not arbitrary text that can also act as permissions or executable commands.
The host checks the expected result type and version, then checks its relationship to the current job.
Only an accepted result becomes input to task authoring. A value that has the right fields but names
an old task is still unsuitable.

For example, a review record saying there are no findings needs actual review coverage of current
inputs. Shape checking can reject missing coverage fields; it cannot establish that the reviewer
thought carefully enough. Structural and semantic checks answer different questions.

## Why identities depend on exact inputs

Results and saved artifacts carry identities derived from the information they describe. This allows
later stages to detect changed inputs rather than trusting a familiar path or title. Canonical
serialization makes a given value's identity reproducible; its exact byte rules are part of the
technical contract, not a prerequisite for understanding the handoff.

## Offline and bounded

Contract validation does not fetch remote schemas or silently include more project documents.
Unknown versions and invalid paths reject the handoff. A valid path identifies a location but grants
no access to it. The Module's interface and execution references define the supported schema
vocabulary, envelope layouts, validation errors and serialization algorithms.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#typed-values-typed-values).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
