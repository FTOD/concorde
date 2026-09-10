---
audience: worker
---

Every Module has one local module.md reading entry with its four mandatory parts in order:
Purpose, Requirements, Scenarios and Ontology, the last holding the Entities and Relationships
subsections. Requirements are Module-level promises, each a heading section `req.<module>.<name>
-- Title` whose first paragraph is one sentence with exactly one SHALL or SHALL NOT, expressing
one decidable behavior; a requirement is never a list item and never belongs to one scenario.
Scenarios cover success, failure and repeated-invocation paths as GIVEN/WHEN/THEN/AND/BUT steps;
whatever one situation must additionally guarantee goes into its steps or prose, never into a
SHALL sentence inside the scenario. The Ontology declares the Module's entities: submodules,
programs, files, records, concepts, interfaces and external actors, each with a stable id, title,
kind and responsibility. Every child Module and every used Module needs exactly one entity carrying
its `target_id`; an interface is an entity whose behavior is stated by its scenarios, not a separate
declaration. Links address definitions by ID (`scenarios.md#scenario.x`, `#req.x`, `#entity.x`)
and must point at the document that defines the ID. Never list tests in a Spec: tests declare the
scenario they verify in their own code. Missing business facts remain explicit in an initialized
stub. The entry does not replace the collection.

Prefer an overview that builds overall understanding and points to detailed submodule or topic
Specs. Internal structure can be useful on the main page; no fixed abstraction level or black-box
presentation is required. Treat these as writing recommendations, not gates. Use local explanations
and references where they help readers, while retaining required promises in the target's
explicitly registered context.

Return Markdown replacements in `documents` only; a Module's Relationships diagram is an inline
Mermaid flowchart inside its registered Markdown, so revising it is part of the same document
replacement, not a separate artifact.

Keep entity titles and relationship diagram labels consistent, with every edge labeled by its relationship verb. Never infer Module behavior from implementation code.
