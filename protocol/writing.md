# Spec writing guidelines

Use these guidelines to write and evaluate a Module's Specs. They have four separately maintained
parts, used together:

- **[Required format](format.md)** defines the machine-checkable structure and syntax:
  - Document pairs.
  - Declarations.
  - Metadata.
  - Identities.
  - Anchors.
  - Precise obligations.
- **[Writing guidance](module.md)** explains what the content must communicate to its intended
  reader. It recommends this reading order:
  - Purpose.
  - Core concepts.
  - Overview diagrams.
  - Details of correct use, design and collaborations.

  Applying it requires reader and editor judgment.
- **[Sentence style](style.md)** states how each sentence is written:
  - One fact in each sentence.
  - Short sentences.
  - Lists instead of long runs of clauses.
  - The actor named.
  - No semicolons.

  Its rules are inspired by the structural rules of ASD-STE100 Simplified Technical English.
- **[Evaluating a Spec](evaluation.md)** states how a Spec is judged good:
  - The quality of one Module's Specs for its reader.
  - The quality of the architecture between Modules.
  - When a problem is blocking or advisory.

  It is a judgment and not deterministic.

All four parts serve the Protocol's purposes of understanding and boundaries. When structural
checks pass, semantic writing requirements still apply. Mandatory terms retain their force in every
part. **MUST** states requirements. **MUST NOT** states prohibitions. **SHOULD** allows departure
for an explained reason. **MAY** permits a choice. The chapter titles do not change these
meanings or introduce new conformance checks.

Start with the reader's problem and the Module's responsibility, use Required format to express
its declarations, and use Writing guidance to explain their meaning.

The [Module entry template](templates/module.md) and [Scenario fragment](templates/scenario.md) are
starting points. Keep diagrams next to the prose they clarify. Choose a workflow diagram for any
process, including one among several participants, or another view suited to the reader's question.
See [Writing guidance on diagrams](module.md#diagrams).

[Checks](checks.md) establish structural conformance only. Evaluate the content for semantic
sufficiency as well, as [Evaluating a Spec](evaluation.md) states. Evidence from the implementation
establishes implementation conformance. None of these substitutes for another.
See [Conformance](principles.md#conformance).
