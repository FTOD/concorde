# Spec writing guidelines

Use these guidelines to write and review a Module's Specs. They have two separately maintained
parts, used together:

- **[Required format](format.md)** defines the machine-checkable structure and syntax: document
  pairs, declarations, metadata, identities, anchors, reading sections and precise obligations.
- **[Writing guidance](module.md)** explains what the content must communicate to its intended
  reader: responsibility, terminology, correct use, design, collaborations and meaningful diagrams.
  Applying it requires reader and editor judgment.

Both parts serve the Protocol's purposes of understanding and boundaries. Semantic writing
requirements still apply when structural checks pass. Mandatory terms retain their force in both
parts: **MUST** and **MUST NOT** state requirements and prohibitions, **SHOULD** allows departure
for an explained reason, and **MAY** permits a choice. The chapter titles do not change these
meanings or introduce new conformance checks.

Start with the reader's problem and the Module's responsibility, use Required format to express
its declarations, and use Writing guidance to explain their meaning. The
[Module entry template](templates/module.md) and [Scenario fragment](templates/scenario.md) are
starting points. Keep diagrams next to the prose they clarify, choosing a lightweight workflow
for process progression or another view suited to the reader's question; see
[Writing guidance on diagrams](module.md#diagrams).

[Checks](checks.md) establish structural conformance only. Review the content for semantic
sufficiency as well; evidence from the implementation establishes implementation conformance.
None of these substitutes for another; see [Conformance](principles.md#conformance).
