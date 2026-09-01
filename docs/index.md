# Concorde documentation

Concorde is a module-centered architecture and feature workflow for Spec Kit.

Start here:

- [Framework overview](framework-overview.md) — what Concorde adds and where authority lives.
- [Ontology](ontology.md) — modules, architecture entities, relationships, features, interfaces,
  attempts, evidence, and projections.
- [Specification model](specification-model.md) — canonical files and validation rules.
- [Project structure](project-structure.md) — the recursive directory profile.
- [Workflow](concorde-workflow.md) — specify through cleanup-only delivery.
- [Command reference](commands.md) — normal and Concorde-specific commands.
- [Quick start](quick-start.md) — install and use the framework.
- [Self-hosting](self-hosting.md) and [Releasing](releasing.md) — distribution workflows.

The shortest useful mental model is:

1. `architecture.md` explains one module's typed entities and how they relate.
2. `features/<NNN-name>.md` explains one level-local capability and how to use it.
3. Code implements it; tests/checks provide evidence.
4. `.concorde/attempts/<stable-feature-id>/` holds temporary planning/work evidence and disappears
   after successful delivery.
5. `.concorde/reflections/log.md` retains project-wide process memory.
6. Generated documentation and diagrams are reproducible views of durable sources.
