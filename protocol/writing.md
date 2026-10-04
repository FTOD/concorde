# Spec writing guidelines

Use these guidelines to write and evaluate a Module's Specs. They have four separately maintained
parts, used together:

- **[Required format](format.md)** defines the machine-checkable structure and syntax: document
  pairs, declarations, metadata, identities, anchors and precise obligations.
- **[Writing guidance](module.md)** explains what the content must communicate to its intended
  reader, in a recommended reading order: purpose, core concepts, overview diagrams, then details
  of correct use, design and collaborations. Applying it requires reader and editor judgment.
- **[Sentence style](style.md)** states how each sentence is written: one fact in each sentence,
  short sentences, lists instead of long runs of clauses, the actor named and no semicolons. Its
  rules are inspired by the structural rules of ASD-STE100 Simplified Technical English.
- **[Evaluating a Spec](evaluation.md)** states how a Spec is judged good: the quality of one
  Module's Specs for its reader, the quality of the architecture between Modules, and when a
  problem is blocking or advisory. It is a judgment and not deterministic.

All four parts serve the Protocol's purposes of understanding and boundaries. Semantic writing
requirements still apply when structural checks pass. Mandatory terms retain their force in every
part: **MUST** and **MUST NOT** state requirements and prohibitions, **SHOULD** allows departure
for an explained reason, and **MAY** permits a choice. The chapter titles do not change these
meanings or introduce new conformance checks.

Start with the reader's problem and the Module's responsibility, use Required format to express
its declarations, and use Writing guidance to explain their meaning. The
[Module entry template](templates/module.md) and [Scenario fragment](templates/scenario.md) are
starting points. Keep diagrams next to the prose they clarify, choosing a workflow diagram for
any process, including one among several participants, or another view suited to the reader's
question; see [Writing guidance on diagrams](module.md#diagrams).

[Checks](checks.md) establish structural conformance only. Evaluate the content for semantic
sufficiency as well, as [Evaluating a Spec](evaluation.md) states; evidence from the implementation
establishes implementation conformance. None of these substitutes for another; see
[Conformance](principles.md#conformance).
