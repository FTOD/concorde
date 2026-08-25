---
title: Specifications, Design, and Architecture
sidebar_position: 4
---

# Specifications, Design, and Architecture

Concorde keeps all durable behavioral and architectural intent in one recursive `specs/` hierarchy.
The name means more than feature requirements: architecture is also part of the maintained system
specification.

## Module packages

Every module package follows the same conceptual shape:

```text
<module>/
├── module.md
├── architecture.json
├── contracts/
├── features/
└── modules/
```

`module.md` describes responsibility, boundaries, current-level features, and immediate children.
`architecture.json` is the machine-readable one-level component view. `contracts/` defines the
module's external I/O. `features/` owns behavior at this level, while `modules/` recursively contains
the next level.

An architecture view must respect the abstraction boundary: it can show the current module,
immediate children, their I/O, permitted external actors, and their organization. It should not
expose grandchildren or low-level classes merely because those details exist.

## Feature packages

A feature root separates permanent knowledge from one delivery attempt:

```text
<feature>/
├── spec.md
├── design.md
├── contracts/
├── diagrams/
└── implementation/
    ├── checklists/
    ├── plan.md
    ├── tasks.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── validation.md
```

The distinction is deliberate:

| Artifact | Lifetime | Question answered |
|---|---|---|
| `spec.md` | Durable | What behavior is required, and why? |
| `design.md` | Durable | How does the accepted implementation compose related modules, features, contracts, and flows to realize the feature? |
| Feature contracts | Durable | What exact representation or obligation is normative for this feature? |
| Feature diagrams | Durable | Which components collaborate, or how does a representative scenario move through them? |
| `implementation/` | Temporary | How will the current implementation attempt be planned, executed, and verified? |

`design.md` is not a second module architecture. It explains the feature's accepted realization and
references the modules that own structural boundaries. Plans and tasks are not permanent design
records: they include rejected options, sequencing, and delivery state that cease to be useful after
the milestone is accepted.

## Hardening a milestone

When all current tasks and checklist items are complete, the maintainer may harden the attempt. The
agent proposes a concise update to `design.md`, and Concorde binds that proposal to the current
source digest. After explicit approval, the durable design is updated and `implementation/` is
removed atomically.

Hardening is optional and review-driven. It cannot run on incomplete work, and it does not change
`spec.md`. A later change starts a fresh implementation attempt using both durable documents as its
baseline.

## Contracts and serialized information

Every module boundary contract must be documented. A feature is functional only when the relevant
provided and required contracts are respected.

A contract representation should either use a commonly adopted format or define a custom format in
an observable serialization language such as JSON, YAML, or TOML. For a common format, explain
briefly what information crosses the boundary. For a custom format, maintain a schema or grammar,
representative examples, field meaning, failure behavior, and compatibility rules so a programmer
can inspect exactly what is being passed.

## Diagrams as explanations

Concorde encourages Archify diagrams when component involvement is easier to understand visually.
A cross-component feature normally has one core architecture diagram showing stable participants,
responsibilities, interactions, and contract crossings. Sequence, workflow, data-flow, or lifecycle
views may supplement it when order or state matters; a sequence diagram is not the core feature
view.

The text remains authoritative. A diagram may make a scenario concrete, but it cannot introduce
behavior or a boundary obligation absent from the specification and contracts.

Read the canonical [core workflow specification](../specs/concorde/features/001-concorde-starter-workflow/spec.md)
for the complete rules and the [project structure guide](project-structure.md) for their locations in
a working repository.
