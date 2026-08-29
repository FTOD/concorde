---
title: Abstract, Design, Implementation, and Architecture
sidebar_position: 4
---

# Abstract, Design, Implementation, and Architecture

In Concorde, `specs/` means the maintained specification of the system, not merely a collection of
feature requests. Behavioral specifications, module architecture, boundary contracts, accepted
feature realization, and explanatory diagrams share one recursive hierarchy because they constrain
the same system from different viewpoints.

Every level of that hierarchy separates what is **read** from what is **consulted**. What is read—a
module summary or a feature abstract—is the primary interface for humans and coding agents and must be
absorbable in minutes; what is consulted keeps the durable model complete beneath that surface
without making anyone read it first. Module packages use `design.md` for module rationale, while
feature roots use `design.md` for required behavior and `implementation.md` for accepted realization.

The complete source profile is governed by
[Feature 001](../specs/concorde/features/001-concorde-workflow/design.md). This guide explains
how to use it.

## Module packages define architectural levels

Each module package repeats the same shape:

```text
<module>/
├── module.md          summary: read first and, usually, only
├── design.md          module design reference: consulted for one specific question
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

## Features are specified at one level

Every feature has one stable identity and exactly one place in the hierarchy where it is specified:
the level at which every module it uses is visible. Its workspace sits under that module's
`features/` directory, and the specification records that module as the feature's `module`. A
feature may be realized by that module alone or by several of its visible modules and lower-level
features working together; it need not be owned by any single module.

If behavior needs several immediate child modules, it is therefore specified at their common parent
level. The parent-level feature describes the observable outcome and the current-level
collaboration. Features specified at the children may refine it, but refinement links move only
between adjacent levels and must remain acyclic.

This means the feature hierarchy and module hierarchy reinforce one another:

```text
parent-level feature
├── refined by child-module feature A
└── refined by child-module feature B
```

The parent feature does not need the children's implementation details. It needs their visible
contracts and enough scenario information to explain their collaboration.

The `module` front-matter field and the workspace protocol's `providing_module` name come from the
earlier rule of one providing module per feature. The constitution (principle A.III) no longer
requires that rule; validation still checks that every feature names exactly one specifying module
and sits under its canonical root, and aligning the layout and field names with A.III is tracked
follow-up work in Feature 001.

## A feature has three durable documents

Every feature root—a top-level feature or one immediate sub-feature—owns `abstract.md`, `design.md`,
and `implementation.md`, plus at most one temporal `attempt/`. The reading path is
**orientation → authority → realization**: `abstract.md` answers "what is this", `design.md` answers
"exactly what must hold", and `implementation.md` answers "how is it built".

### Optional one-level sub-features

A feature stays atomic by default. When one specification mixes several correlated outcomes, the
parent may declare an ordered set of immediate sub-features under
`subfeatures/<number-name>/`. The parent owns the aggregate outcome, shared invariants, dependencies,
and decomposition rationale. Each child owns one focused `## Outcome`, requirements, scenarios, and
accepted realization, while inheriting the parent module. A sub-feature cannot contain another
sub-feature. This containment is separate from `refines`, which relates features across adjacent
module levels.

Any parent or child can be the one selected lifecycle root. A selected child uses its own durable
and temporal paths; its parent's `abstract.md`/`design.md`/`implementation.md` trio is read-only aggregate
context and siblings are concise navigation summaries only.

```text
<feature>/
├── abstract.md            read first: what the feature is, in under 15 minutes
├── design.md            the complete behavioral authority
├── implementation.md accepted realization and full implementation detail
├── diagrams/
├── contracts/
├── subfeatures/       top-level feature only; one level, same shape
└── attempt/    at most one temporal attempt
    ├── checklists/
    ├── plan.md
    ├── tasks.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── validation.md
```

The files at the feature root and those below `attempt/` have deliberately different
lifetimes.

### `abstract.md`: the feature abstract

`abstract.md` is the first—and for most questions the only—feature document a programmer or agent
opens. From it alone, without opening anything else, a reader gets a quick understanding of the
feature's purpose, functionality, basic structure, and logic. It has no front matter and no stable
ID. Its body has exactly five H2 sections, in this order:

| Section | Content |
|---|---|
| `Purpose` | The outcome and for whom |
| `Functionality` | What the feature does and does not do: its operations, surfaces, parts, and boundaries |
| `Structure` | The participating parts and how they collaborate, linking the feature's declared core diagram (or the parent's core view, the level view, or an inline fenced `text` sketch) |
| `Logic` | How it works—the main flows in order—and the rules an implementer must not break, each rule citing the `FR-NNN` requirement in `design.md` it summarizes |
| `Read Next` | Links to `design.md`, `implementation.md`, the contracts, the module summary, and any sub-features or parent |

Its links redirect; they are never required to understand it. The abstract summarizes `design.md` and
never defines beyond it: it may not state a requirement, scope boundary, or success criterion that
`design.md` does not state, and where the two disagree `design.md` prevails and analysis reports the
disagreement. It has a reading budget of about 3,000 body words, or fifteen minutes; validation
reports an overrun as a warning (`CONCORDE-ABSTRACT-004`) and checks the section shape
(`CONCORDE-ABSTRACT-001`), the structure link or sketch (`CONCORDE-ABSTRACT-002`), and that every
requirement ID cited in `Logic` exists in `design.md` (`CONCORDE-ABSTRACT-003`). Whether it is a faithful
summary remains a review responsibility.

`speckit.specify` authors it together with `design.md`, `speckit.clarify` keeps it current, and no
other workflow step writes it. It is authored, not generated, because a faithful summary requires
editorial judgment.

### `design.md`: required behavior

`design.md` answers exactly what the feature must make observable and why it matters. It includes
actors, requirements, constraints, failures, success criteria, and representative scenarios without
prescribing source layout or implementation mechanics. It is complete and self-contained: readable
without the abstract, more detailed than it, and free of realization detail; it may link
`abstract.md` and `implementation.md` for redirection. It has no deterministic reading budget.

The prose is the definition. A scenario is an example used to make the behavior testable and show
which visible components participate; it cannot silently narrow or expand the textual requirements.

### `implementation.md`: the accepted feature implementation

`implementation.md` answers how the currently accepted implementation realizes the feature, with the full
implementation detail a coder needs. It is needed only when writing the code or fixing a bug. It
should explain:

- collaborating modules and lower-level features;
- the contracts and data or control flow between them;
- realization of representative scenarios;
- durable implementation decisions;
- useful code and evidence references; and
- limitations or compatibility constraints that remain true after the delivery attempt ends.

It is not a second `architecture.json` and not a second behavioral design. Module responsibilities,
boundaries, and organization remain owned by module architecture and required behavior by `design.md`;
`implementation.md` references those authorities while explaining their use for this feature. Its
six fixed sections are `Realization Overview`, `Module and Feature Collaboration`, `Scenario
Realization`, `Durable Implementation Decisions`, `Traceability and Evidence`, and `Known
Limitations`, followed by any further headings the implementation detail needs.

The file exists from the moment the feature does. `speckit.specify` seeds a placeholder from the
`implementation-template` whose only content is the statement that no implementation realization has been
hardened yet; the first approved hardening writes it in full, and each later hardening completes it.
No other workflow step writes its substantive content. Planning treats the placeholder as the
absence of a baseline and must not invent an accepted realization merely because work is proposed.

Validation rejects a feature root without `implementation.md` (`CONCORDE-LAYOUT-005`) or without
`abstract.md` (`CONCORDE-LAYOUT-009`), reports legacy `tldr.md`/`spec.md` names as
`CONCORDE-LAYOUT-007`, and reports a legacy `implementation/` attempt directory as
`CONCORDE-LAYOUT-008`. No compatibility alias or symlink may stand in for the canonical names.

### `attempt/`: one temporary attempt

`attempt/` contains the current delivery proposal and its review state: checklists, research,
plan, tasks, technical models, acceptance guidance, and evidence. It represents at most one active
attempt, and hardening compacts it into `implementation.md`.

These files may contain alternatives, sequencing decisions, incomplete work, and transient notes.
Their presence beneath `specs/` does not make them durable intent. There must be no compatibility
copy of `plan.md`, `tasks.md`, or `checklists/` beside `abstract.md`, `design.md`, and `implementation.md`.

### `reflections.md`: the project's one reflection log

Problems met during an attempt are not attempt-local: they usually concern something that already
exists — another feature's realization, a module boundary, an instruction, a tool. They are recorded
in one maintained file, `reflections.md` directly inside the specification root, as entries that
name the feature being worked on (`Feature`) and the source the problem concerns (`Concerns`), with
a kind, an effect, and a maintainer-owned status. Every phase after specification appends to it; no
operation removes it; hardening cites a feature's open entries in its implementation and leaves
the log byte-identical; validation checks its shape; the docsite does not publish it.

## Hardening changes the lifetime, not the behavior

Once every recognizable task and every existing checklist item is complete, the maintainer may ask
Concorde to harden the attempt. The coding agent synthesizes candidate feature `implementation.md` and,
when the attempt produced implementation detail or rationale worth keeping, a full replacement of
the `design.md` of the module at which the feature is specified, adding that material under the
reference's stable headings.
The runtime binds both candidates and the exact `attempt/` removal target to the current
source digest, which covers the module `design.md` and the abstract as well.

Nothing changes until the maintainer explicitly approves that exact proposal. On success, the
feature `implementation.md` is updated, module `design.md` is amended when the proposal included it, and
the whole `attempt/` directory is removed as one atomic, failure-safe operation. `abstract.md`,
`design.md`, every `module.md`, contracts, views, code, and tests are not changed by hardening.
Hardening is the only workflow step that carries attempt-derived rationale into a module design
reference.

A later change begins a fresh attempt. Planning reads two durable documents—`design.md` as required
behavior and feature `implementation.md` as the accepted realization baseline—with the level's
`module.md` as bounded context; the abstract is orientation only, never a planning input.

## Where a fact lives

| A reader wants to know… | Reads |
|---|---|
| what went wrong while building anything, and what was decided about it | `reflections.md` at the specification root |
| what a level does, how its parts hang together, and where to go next | `module.md` |
| why the level is designed this way, how it is implemented, what was tried and rejected | the module `design.md` |
| what a boundary promises and what crosses it | the contract document |
| what a feature does, how it is basically structured, and how it works | `abstract.md` |
| exactly what a feature must make observable, and how that is accepted and measured | `design.md` |
| how the accepted implementation realizes that feature, in full detail | feature `implementation.md` |
| what is being attempted right now | `attempt/` |
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

Feature diagrams live under the feature's `diagrams/`, are declared by feature `design.md`,
and have an equivalent textual explanation; supplemental module-owned views live under the module's
`diagrams/` and are explained by `module.md`. Their generated HTML is a reproducible projection.
Neither source JSON nor generated HTML may introduce requirements or boundaries absent from the
owning text and contracts.

Use [Project structure and source authority](project-structure.md) next when you need to identify the
correct file for a change.
