---
title: Specifications, Design, and Architecture
sidebar_position: 4
---

# Specifications, Design, and Architecture

In Concorde, `specs/` means the maintained specification of the system, not merely a collection of
feature requests. Behavioral specifications, module architecture, boundary contracts, accepted
feature realization, and explanatory diagrams share one recursive hierarchy because they constrain
the same system from different viewpoints.

Every level of that hierarchy separates a **summary that is read** from a **reference that is
consulted**. The summary is the primary interface for humans and coding agents; the reference keeps
the specification complete beneath that surface without making anyone read it first.

The complete source profile is governed by
[Feature 001](../specs/concorde/features/001-concorde-workflow/spec.md). This guide explains
how to use it.

## Module packages define architectural levels

Each module package repeats the same shape:

```text
<module>/
├── module.md          summary: read first and, usually, only
├── design.md          design reference: consulted for one specific question
├── architecture.json  level view: the required structure diagram (non-leaf)
├── diagrams/          optional supplemental module-owned Archify views
├── contracts/
├── features/
└── modules/
```

`module.md`, the contract documents, and `architecture.json` are the only authorities for
responsibility, boundary, boundary obligations, and current-level organization. `design.md`
explains and justifies them; it never redefines them.

### `module.md`: the module summary

`module.md` is the primary interface to a level for humans and coding agents, and the first project
source every Concorde command reads. It owns the module's responsibility, boundary, parent,
immediate children, and current-level inventories. A reader can stop here and go no deeper.

Its body has eight required H2 sections, in any order; further sections and diagrams are welcome:

| Section | Content |
|---|---|
| `Responsibility`, `Boundary` | Short prose |
| `Structure` | A link to the level's `architecture.json`. A leaf module without a view records a one-line rationale instead. Further diagrams may be linked or embedded. |
| `Features`, `Contracts`, `Submodules` | One inventory table each, or the line `None.` |
| `Representative Scenario` | One current-level scenario in prose |
| `Design Rationale` | The key rationale in a few sentences, plus a link to the adjacent `design.md` |

The summary has a reading budget: about 4,000 body words, or twenty minutes for a first-time
reader. Front matter, fenced code blocks, and HTML comments do not count. Validation reports an
overrun as a warning (`CONCORDE-SUMMARY-005`) that does not change the validation status; staying
within budget is a review responsibility. Narrative that would breach the budget belongs in
`design.md`.

### `design.md`: the module design reference

`design.md` records the implementation detail of the level and the ideas, rationales, alternatives,
and decisions developed during development, organized under stable headings such as
`Implementation Notes`, `Design Rationale`, `Alternatives Considered`, and `Decision Log`. It has no
front matter and no stable ID, may be as long as it needs to be, and may say that nothing has been
recorded yet. Validation requires a real, non-empty one beside every `module.md`
(`CONCORDE-MODULE-002`).

Neither humans nor agents need it to understand the level. It is opened only for a detail the
summary deliberately leaves out, and no workflow operation reads it implicitly: bounded context
returns it as a navigation reference, `ask` opens it only when a question asks for implementation
detail or rationale and cites it, and planning consults it deliberately. Maintainers may edit it
directly at any time as an ordinary maintained source; workflow operations write it only through an
approved hardening proposal (see
[Hardening](#hardening-changes-the-lifetime-not-the-behavior)).

### `architecture.json`: the level view

`architecture.json` owns the machine-readable organization visible at that level and is the
summary's required structure diagram. For a non-leaf module, it contains only the current module,
its immediate children, permitted externals, and connections among those participants. It must not
expose grandchildren or internal code structures. A leaf may omit the view when there is no lower
architectural level worth showing. Supplemental module-owned views under `diagrams/` answer
narrower questions and never own behavior or boundaries.

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

Every feature root—a top-level feature or one immediate sub-feature—owns `spec.md` and
`implementation.md`, plus at most one temporal `implementation/` attempt.

### Optional one-level sub-features

A feature stays atomic by default. When one specification mixes several correlated outcomes, the
parent may declare an ordered set of immediate sub-features under
`subfeatures/<number-name>/`. The parent owns the aggregate outcome, shared invariants, dependencies,
and decomposition rationale. Each child owns one focused `## Outcome`, requirements, scenarios, and
accepted realization, while inheriting the parent module. A sub-feature cannot contain another
sub-feature. This containment is separate from `refines`, which relates features across adjacent
module levels.

Any parent or child can be the one selected lifecycle root. A selected child uses its own durable
and temporal paths; its parent `spec.md`/`implementation.md` pair is read-only aggregate context and
siblings are concise navigation summaries only.

```text
<feature>/
├── spec.md            required behavior
├── implementation.md  accepted realization
├── contracts/
├── diagrams/
├── subfeatures/       top-level feature only; one level, same shape
└── implementation/    at most one temporal attempt
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

### `implementation.md`: accepted realization

`implementation.md` answers how the currently accepted implementation realizes that feature. It
should explain:

- collaborating modules and lower-level features;
- the contracts and data or control flow between them;
- realization of representative scenarios;
- durable implementation decisions;
- useful code and evidence references; and
- limitations or compatibility constraints that remain true after the delivery attempt ends.

It is not a second `architecture.json`. Module responsibilities, boundaries, and organization remain
owned by module architecture; `implementation.md` references those authorities while explaining
their use for this particular feature. Its required sections are `Realization Overview`, `Module and
Feature Collaboration`, `Scenario Realization`, `Durable Implementation Decisions`, `Traceability
and Evidence`, and `Known Limitations`.

The file exists from the moment the feature does. `speckit.specify` seeds a placeholder whose only
content is the statement that no implementation realization has been hardened yet; the first
approved hardening writes it in full, and each later hardening completes it. No other workflow step
writes its substantive content. Planning treats the placeholder as the absence of a baseline and
must not invent an accepted realization merely because work is proposed.

The name `design.md` is reserved for the module level and `implementation.md` for feature roots.
Validation rejects a feature root without `implementation.md` (`CONCORDE-LAYOUT-005`), a legacy
`design.md` at a feature root (`CONCORDE-LAYOUT-007`; rename it), and a root holding both names
(`CONCORDE-LAYOUT-008`). No compatibility alias or symlink may stand in for either name.

### `implementation/`: one temporary attempt

`implementation/` contains the current delivery proposal and its review state: checklists, research,
plan, tasks, technical models, acceptance guidance, and evidence. It represents at most one active
attempt, and hardening compacts it into `implementation.md`.

These files may contain alternatives, sequencing decisions, incomplete work, and transient notes.
Their presence beneath `specs/` does not make them durable intent. There must be no compatibility
copy of `plan.md`, `tasks.md`, or `checklists/` beside `spec.md` and `implementation.md`.

## Hardening changes the lifetime, not the behavior

Once every recognizable task and every existing checklist item is complete, the maintainer may ask
Concorde to harden the attempt. The coding agent synthesizes a candidate `implementation.md` and,
when the attempt produced implementation detail or rationale worth keeping, a full replacement of
the providing module's `design.md` that adds that material under the reference's stable headings.
The runtime binds both candidates and the exact `implementation/` removal target to the current
source digest, which covers the module `design.md` as well.

Nothing changes until the maintainer explicitly approves that exact proposal. On success,
`implementation.md` is updated, `design.md` is amended when the proposal included it, and the whole
`implementation/` directory is removed as one atomic, failure-safe operation. `spec.md`, every
`module.md`, contracts, views, code, and tests are not changed by hardening. Hardening is the only
workflow step that carries attempt-derived rationale into a module design reference.

A later change begins a fresh attempt. Planning reads both durable documents—`spec.md` as required
behavior and `implementation.md` as the accepted realization baseline—with the level's `module.md`
as bounded context.

## Where a fact lives

| A reader wants to know… | Reads |
|---|---|
| what a level does, how its parts hang together, and where to go next | `module.md` |
| why the level is designed this way, how it is implemented, what was tried and rejected | `design.md` |
| what a boundary promises and what crosses it | the contract document |
| what a feature must make observable | `spec.md` |
| how the accepted implementation realizes that feature | `implementation.md` |
| what is being attempted right now | `implementation/` |
| what the code actually does and whether it is proven | code and tests |

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

A module's `architecture.json` is its required structure diagram, linked from the summary and
embedded on the published module page. A cross-component feature normally declares at most one
**core** diagram. It must be an architecture view that shows stable components, responsibilities,
interactions, and governing contracts. A sequence, workflow, data-flow, or lifecycle diagram is
**supplemental** and answers a narrower dynamic question such as call order or state change; it
cannot serve as the core feature view.

Feature diagrams live under the feature's `diagrams/`, are declared by the feature specification,
and have an equivalent textual explanation; supplemental module-owned views live under the module's
`diagrams/` and are explained by `module.md`. Their generated HTML is a reproducible projection.
Neither source JSON nor generated HTML may introduce requirements or boundaries absent from the
owning text and contracts.

Use [Project structure and source authority](project-structure.md) next when you need to identify the
correct file for a change.
