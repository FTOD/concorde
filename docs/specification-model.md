---
title: Specifications, Design, and Architecture
sidebar_position: 4
---

# Specifications, Design, and Architecture

In Concorde, `specs/` means the maintained specification of the system, not merely a collection of
feature requests. Behavioral specifications, module architecture, boundary contracts, accepted
feature design, and explanatory diagrams share one recursive hierarchy because they constrain the
same system from different viewpoints.

The complete source profile is governed by
[Feature 001](../specs/concorde/features/001-concorde-starter-workflow/spec.md). This guide explains
how to use it.

## Module packages define architectural levels

Each module package repeats the same shape:

```text
<module>/
├── module.md
├── architecture.json
├── contracts/
├── features/
└── modules/
```

`module.md` owns the module's responsibility, boundary, current-level features, parent, and immediate
children. Its contract documents own the obligations and information crossing the boundary.
`architecture.json` owns the machine-readable organization visible at that level.

For a non-leaf module, the architecture view contains only the current module, its immediate
children, permitted externals, and connections among those participants. It must not expose
grandchildren or internal code structures. A leaf may omit the view when there is no lower
architectural level worth showing.

This rule is what makes the hierarchy useful. A root-level reviewer can reason about major system
parts; a maintainer can then zoom into one child and see its next level without loading the entire
system at once.

## Features belong to a providing module

Every feature has one stable identity and one providing module at its current abstraction level. Its
workspace sits under that module's `features/` directory.

If behavior uses multiple immediate child modules, it normally belongs to their nearest common
parent. The parent-level feature describes the observable outcome and current-level collaboration.
Features owned by the children may refine it, but refinement links move only between adjacent levels
and must remain acyclic.

This means the feature hierarchy and module hierarchy reinforce one another:

```text
parent module feature
├── refined by child-module feature A
└── refined by child-module feature B
```

The parent feature does not need the children's implementation details. It needs their visible
contracts and enough scenario information to explain their collaboration.

## A feature has two durable documents

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

The files at the feature root and those below `implementation/` have deliberately different
lifetimes.

### `spec.md`: required behavior

`spec.md` answers what the feature must make observable and why it matters. It includes actors,
requirements, constraints, failures, success criteria, and representative scenarios without
prescribing source layout or implementation mechanics.

The prose is the definition. A scenario is an example used to make the behavior testable and show
which visible components participate; it cannot silently narrow or expand the textual requirements.

### `design.md`: accepted realization

`design.md` answers how the currently accepted implementation realizes that feature. It should
explain:

- collaborating modules and lower-level features;
- the contracts and data or control flow between them;
- realization of representative scenarios;
- durable implementation decisions;
- useful code and evidence references; and
- limitations or compatibility constraints that remain true after the delivery attempt ends.

It is not a second `architecture.json`. Module responsibilities, boundaries, and organization remain
owned by module architecture; `design.md` references those authorities while explaining their use for
this particular feature.

Before the first accepted milestone, `design.md` explicitly says that no realization has been
hardened. Planning must not invent an accepted design merely because work is proposed.

### `implementation/`: one temporary attempt

`implementation/` contains the current delivery proposal and its review state: checklists, research,
plan, tasks, technical models, acceptance guidance, and evidence. It represents at most one active
attempt.

These files may contain alternatives, sequencing decisions, incomplete work, and transient notes.
Their presence beneath `specs/` does not make them durable intent. There must be no compatibility
copy of `plan.md`, `tasks.md`, or `checklists/` beside `spec.md` and `design.md`.

## Hardening changes the lifetime, not the behavior

Once every recognizable task and every existing checklist item is complete, the maintainer may ask
Concorde to harden the attempt. The coding agent synthesizes a candidate durable design; the runtime
binds that candidate and the exact `implementation/` removal target to the current source digest.

Nothing changes until the maintainer explicitly approves that exact proposal. On success,
`design.md` is updated and the whole `implementation/` directory is removed as one failure-safe
operation. `spec.md`, architecture sources, code, and tests are not changed by hardening.

A later change begins a fresh attempt. Planning reads both durable documents: `spec.md` as required
behavior and `design.md` as the accepted realization baseline.

## Contracts make boundaries observable

A module feature is functional only when its provided and required contracts are respected. Every
contract identifies its owner, role, flow direction, counterparties, obligations, failures,
compatibility expectations, and evidence.

The transferred representation must also be reviewable:

- For a commonly adopted format, name the relevant standard and version, link its authoritative
  definition, and briefly explain the information passed.
- For a custom format, use a programmer-observable serialization such as JSON, YAML, or TOML and
  provide a schema or grammar, complete field meanings, compatibility rules, examples, and
  conformance evidence.

Contract documents can exist at module and feature levels. The module contract owns architectural
identity and boundary obligations; a feature-local schema may own the detailed representation used
by that feature. References must make this split explicit.

## Diagrams explain; text governs

Concorde encourages maintained Archify diagrams when they materially improve understanding.

A cross-component feature normally declares at most one **core** diagram. It must be an architecture
view that shows stable components, responsibilities, interactions, and governing contracts. A
sequence, workflow, data-flow, or lifecycle diagram is **supplemental** and answers a narrower dynamic
question such as call order or state change; it cannot serve as the core feature view.

Feature diagrams live under `diagrams/`, are declared by the feature specification, and have an
equivalent textual explanation. Their generated HTML is a reproducible projection. Neither source
JSON nor generated HTML may introduce requirements or boundaries absent from the owning text and
contracts.

Use [Project structure and source authority](project-structure.md) next when you need to identify the
correct file for a change.
