---
audience: worker
---

Every Module has one local module.md reading entry with two level-2 reader-oriented parts:
Usage & Contract, then Architecture & Realization. The first contains the direct level-3 subsections
Purpose, Usage, Requirements and Scenarios; the second contains Design, Entities and Relationships.
Companion documents use one or both part headings without repeating every entry subsection. Requirements are Module-level promises, each a heading section `req.<module>.<name>
-- Title` whose first paragraph is one sentence with exactly one SHALL or SHALL NOT, expressing
one decidable behavior; a requirement is never a list item and never belongs to one scenario.
Scenarios cover success, failure and repeated-invocation paths as GIVEN/WHEN/THEN/AND/BUT steps;
whatever one situation must additionally guarantee goes into its steps or prose, never into a
SHALL sentence inside the scenario. Internal requirements and verification scenarios belong in
Architecture & Realization and remain normative; define each obligation once and link to it from
the design that fulfills it. The architecture inventory declares the Module's entities: submodules,
programs, files, records, concepts, interfaces and external actors, each with a stable id, title,
kind and responsibility. Every child Module and every used Module needs exactly one entity carrying
its `target_id`; an interface is an entity whose behavior is stated by its scenarios, not a separate
declaration. Links address definitions by ID (`scenarios.md#scenario.x`, `#req.x`, `#entity.x`)
and must point at the document that defines the ID. Never list tests in a Spec: tests declare the
scenario they verify in their own code. Missing business facts remain explicit in an initialized
stub. The entry does not replace the collection.

Write for consumers first: when and how to use the responsibility, concepts and prerequisites,
actual entry points, inputs/results, effects, errors and applicable repeat/cancellation/compatibility
behavior. Consumers may be other Modules; do not invent a public API for a logical responsibility.
Then explain how the design fulfills those promises: responsibilities, control/data flow, state,
dependency choices, invariants and file bindings. An entity inventory is not a design explanation.
Do not make users reconstruct correct use from SHALL and GIVEN/WHEN/THEN lists, and do not copy
external guarantees into a competing internal authority. Use links to canonical definitions.
Keep both parts in the explicitly registered complete context; headings grant or filter nothing.

Return Markdown replacements in `documents` only; a Module's Relationships diagram is an inline
Mermaid flowchart inside its registered Markdown, so revising it is part of the same document
replacement, not a separate artifact.

Keep entity titles and relationship diagram labels consistent, with every edge labeled by its relationship verb. Never infer Module behavior from implementation code.

Propose replacements only for the selected Module-owned documents. References supply read-only context, never provider implementation or write authority. Define each structured contract once using concorde-contract; local concorde-contract-binding declarations name roles, peers, selection conditions, relied-upon guarantees and obligations without duplicating the definition.
