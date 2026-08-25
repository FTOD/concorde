---
title: What Concorde Is
sidebar_position: 3
---

# What Concorde Is

Concorde is a spec-driven workflow for projects where coding agents produce much of the code but
people still need confidence in the system's intent and structure. It combines two ideas:

- **Spec-driven development** keeps required behavior and reasons explicit before implementation.
- **Architecture as Code** keeps module ownership, boundaries, contracts, and component interaction
  in versioned, machine-checkable sources.

Spec Kit already gives a feature a specification, plan, tasks, and implementation workflow. Concorde
retains that lifecycle and adds a hierarchical architectural view plus a permanent record of the
accepted feature realization.

## The problem it addresses

Feature-only specifications answer what users need, but they do not always let a reviewer answer:

- Which module owns this behavior?
- Which immediate submodules collaborate to provide it?
- What information crosses each boundary?
- Which parts of a large system can be ignored at the current level?
- After a coding agent finishes, which implementation decisions were accepted and should survive the
  temporary plan?

Reading generated source code is not a scalable substitute for those answers. Concorde makes them
reviewable before, during, and after implementation.

## One recursive model

A module provides a cohesive set of features through documented contracts. A feature is primarily
defined by text; scenarios are representative examples that show how the feature behaves and how
visible components collaborate. A module may contain child modules, and a feature may be refined by
lower-level features.

At any one level, a reader sees only:

- the current module's responsibility, features, and provided or required I/O contracts;
- its immediate child modules and their boundary I/O;
- the organization and permitted interactions among those visible participants; and
- external actors or systems that cross the current boundary.

Zooming into a child repeats the same model. This bounded view provides useful abstraction without
pretending that the deeper structure does not exist.

## Human intent and agent execution

Concorde assigns different roles to different artifacts:

| Concern | Human-reviewable authority |
|---|---|
| Required behavior and purpose | Feature `spec.md` |
| Accepted feature realization | Feature `design.md` |
| Module responsibility and ownership | `module.md` |
| Boundary obligations and representations | Contract documentation, schemas, and examples |
| Current-level component organization | Maintained Archify JSON |
| One implementation attempt | Files beneath `implementation/` |
| Executable reality and evidence | Source code and tests |

The coding agent can choose low-level code details within these boundaries. The maintainer controls
behavior, structure, contracts, accepted design, and approval gates.

## What Concorde does not replace

Concorde is not a second package manager, coding agent, diagram renderer, documentation generator,
or feature lifecycle. Spec Kit owns component installation and normal feature phases. The active
coding-agent integration presents commands as skills or slash commands. Archify renders maintained
diagram sources. Docusaurus publishes a read-only site.

Concorde connects those systems through a starter bundle, preset, extension, workspace conventions,
and deterministic validation. See the [command reference](commands.md) for the exact responsibility
of each layer and the [root architecture](../specs/concorde/module.md) for the normative module
boundary.
