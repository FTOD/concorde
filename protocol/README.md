# Spec Protocol

Concorde Spec Protocol **16.3** describes a project as a set of Modules connected by declared
relations. Each Module explains one responsibility. Concorde Spec Protocol serves two purposes:

1. **Understanding** — a human grasps these quickly from the project's specification, ultimately
   without reading the code:
   - The backbone of the project.
   - Its parts.
   - Its main flows.
2. **Boundaries** — a harness can derive, for each AI task, exactly what it may read and what it may
   write.

[Principles](principles.md) introduces the model: the specification is one graph of declared
nodes and relations. Read sets, write sets, views and checks are computed from this graph. Each
chapter says how its rules serve the two purposes.

## The shape of the model

- **Seven node types.** Module, document, concept, realization, requirement, scenario, contract.
- **Thirteen relation types**, each declared at one site fixed by its type. A relation's source
  determines its declaration site:
  - When its source is a Module, the relation is declared in that Module's entry and mirrored in
    the project registry.
  - When its source is a concept, the relation is declared in the concept's glossary entry.
  - For any other source, the relation is declared in the document that defines its source.
- **One glossary.** Every concept of the project is declared in one glossary file. Each entry
  names the Module that owns it.
- **One reconciliation rule.** Every relation declares what context it requires. A Module's own
  relations must grant it.

A registered Markdown file and its `.md.json` companion form one document with one identity and one
owner. Both enter context together. Dependencies and composition grant the Specs they depend
on. Every term has these properties:

- It is defined once, in the project glossary.
- It is owned by one Module.
- It is linked wherever a document uses it.

A reader receives the definitions its documents link. Architecture diagrams either assert only
declared relations or are marked illustrative.

## Read the standard

1. [Principles](principles.md) covers:
   - The two purposes.
   - The model at a glance.
   - Seven axioms.
2. [Node types](model.md) — every kind of thing a specification declares, and why each exists.
3. [Relations](relations.md) covers:
   - Every relation.
   - Its attributes.
   - Its checks.
4. [Context](context.md) covers the read side:
   - Four channels.
   - Selection.
   - The reconciliation.
5. [Boundaries](boundaries.md) covers:
   - The write side.
   - The impact of a write.
   - The task types that compose a task's boundary.
6. [Spec writing guidelines](writing.md) — the authoring entry. It has four separately maintained
   parts:
   - [Required format](format.md) for machine-checkable structure and syntax.
   - [Writing guidance](module.md) for content requiring reader and editor judgment.
   - [Sentence style](style.md) for how each sentence is written.
   - [Evaluating a Spec](evaluation.md) for how a Spec's quality and the architecture between
     Modules are judged.
7. [Checks](checks.md) — every decidable rule and its limits.
8. [Views](views.md) covers:
   - Derived views.
   - Checked D2 diagrams.
   - Illustrative blocks.
9. [Migration](migration.md) — what changed from version 10, in 11.1, in 13, 13.1, 13.2, 13.3, 14,
   15, 15.1, 16, 16.1, 16.2, 16.2.1 and 16.3.
10. [`model.yaml`](model.yaml) — the machine-readable vocabulary.
11. Templates: [Module](templates/module.md) and [Scenario fragment](templates/scenario.md).

These are chapters of one standard, not project Module Specs. To use the language, a project needs
none of these:

- The Concorde Framework.
- A particular publisher.
- A particular agent runtime.

Registry serialization, tool configuration, worker wire versions, context delivery and execution
permissions are separate agreements, not additional Protocol versions.

## Requirement language

In these chapters, **MUST** is required for conformance. **MUST NOT** is prohibited. **SHOULD**
is recommended and may be departed from for an explained reason. **MAY** permits a choice.
Examples prescribe neither project names nor business behavior.

## Compatibility

Version 11 is a breaking change. Version-10 registries, metadata and reading structures are invalid.
They MUST be migrated explicitly. No tool may silently reinterpret them. See
[Migration](migration.md).
