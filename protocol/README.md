# Spec Protocol

Concorde Spec Protocol **11.0.0** describes a project as a set of Modules, each explaining one
responsibility, connected by declared relations. It serves two purposes:

1. **Understanding** — a human grasps the backbone of the project, its parts and main flows,
   quickly from its specification; ultimately, without reading the code.
2. **Boundaries** — a harness can derive, for each AI task, exactly what it may read and what it may
   write.

[Principles](principles.md) introduces the model: the specification is one graph of declared
nodes and relations, from which read sets, write sets, views and checks are computed. Each chapter
says how its rules serve the two purposes.

## The shape of the model

- **Seven node types.** Module, document, concept, realization, requirement, scenario, contract.
- **Thirteen relation types**, each declared at one site fixed by its type. A relation whose source
  is a Module is declared in that Module's entry and mirrored in the project registry; any other
  relation is declared in the document that defines its source.
- **One reconciliation rule.** Every relation declares what context it requires; a Module's own
  relations must grant it.

A registered Markdown file and its `.md.json` companion form one document with one identity and one
owner, and both enter context together. Dependencies and composition grant the Specs they depend
on. Each term is defined once, in its owner's Terminology table, and imported elsewhere by link.
Architecture diagrams either assert only declared relations or are marked illustrative.

## Read the standard

1. [Principles](principles.md) — the two purposes, the model at a glance, and seven axioms.
2. [Node types](model.md) — every kind of thing a specification declares, and why each exists.
3. [Relations](relations.md) — every relation, its attributes and its checks.
4. [Context](context.md) — the read side: three channels, selection and the reconciliation.
5. [Boundaries](boundaries.md) — the write side, the impact of a write, and composing a task's
   boundary.
6. [Module specifications](module.md) — what the reading content must explain.
7. [Required format](format.md) — Module declaration, registry, metadata schema 3, identities, anchors, reading
   structure and definition syntax.
8. [Checks](checks.md) — every decidable rule and its limits.
9. [Views](views.md) — derived views, checked flowcharts and illustrative blocks.
10. [Migration](migration.md) — what changed from version 10.
11. [`model.yaml`](model.yaml) — the machine-readable vocabulary.
12. Templates: [Module](templates/module.md) and [Scenario fragment](templates/scenario.md).

These are chapters of one standard, not project Module Specs. A project needs neither the Concorde
Framework, nor a particular publisher, nor a particular agent runtime to use the language.
Registry serialization, tool configuration, worker wire versions, context delivery and execution
permissions are separate agreements, not additional Protocol versions.

## Requirement language

In these chapters, **MUST** is required for conformance and **MUST NOT** is prohibited. **SHOULD**
is recommended and may be departed from for an explained reason. **MAY** permits a choice.
Examples prescribe neither project names nor business behavior.

## Compatibility

Version 11 is a breaking change. Version-10 registries, metadata and reading structures are invalid
and MUST be migrated explicitly; no tool may silently reinterpret them. See
[Migration](migration.md).
