---
title: What Concorde Controls
sidebar_position: 3
---

# What Concorde Controls

Concorde is designed for a development model in which people decide what the system should do and
how it should be structured, while coding agents may produce most of the implementation. In that
model, reviewing every generated line is neither a scalable architecture practice nor a reliable way
to recover intent.

Concorde therefore makes five things explicit and reviewable:

1. the behavior a feature must provide;
2. the level of the hierarchy at which it is specified and the modules that realize it;
3. the contracts and immediate components involved in realizing it;
4. the implementation detail and rationale each level accumulates, kept beneath a short summary; and
5. the realization that was actually accepted after implementation.

The principles behind this are the five workflow principles of the project constitution
(`.specify/memory/constitution.md`, version 2.0.0): fast human comprehension at every level,
completeness beneath the surface, architecture-driven rather than only feature-driven development,
contracts as human-readable promises, and deterministic validation with human-reviewed evidence. The
normative definition of the workflow is
[Feature 001](../specs/concorde/features/001-concorde-workflow/spec.md).

The installed `speckit.concorde.ask` surface makes that framework discoverable from inside the agent
conversation. It answers from version-aligned extension/preset guidance, module summaries, and
feature TL;DRs first, opens deeper sources only deliberately and with citation, labels its basis and
uncertainty, and is strictly read-only. It complements rather than replaces deterministic
`context`/`validate` operations or normal Spec Kit delivery phases.

## Two ideas combined

Concorde takes inspiration from two related practices.

**Spec-driven development** makes behavior and purpose explicit before implementation. In Concorde,
the durable feature specification describes observable behavior, constraints, failures, and
measurable outcomes. It does not prescribe code structure.

**Architecture as Code** makes responsibilities, boundaries, contracts, and component organization
versioned and machine-checkable. Architecture is not kept in a disconnected diagram folder: it is
part of the same recursive `specs/` hierarchy as feature behavior.

Neither practice is sufficient alone. A feature list can leave the agent free to create accidental
module boundaries. An architecture model can be internally valid while saying nothing about whether
the implementation provides the required behavior. Concorde keeps the two connected without
pretending they are the same authority.

## The model: a module hierarchy realizes the features

A **module** is an architecturally meaningful unit with one responsibility, an explicit boundary,
and declared provided and required contracts. The project is a module hierarchy rooted at the project
module, and every level of it is a deliberate abstraction: the modules visible at that level, their
responsibilities, and their interactions are chosen so the level can be understood on its own terms,
without the levels below.

A **feature** is an observable outcome with a stable ID. It is *specified* at exactly one level of
the hierarchy—the level at which every module it uses is visible—and *realized* by one module or by
several modules and lower-level features working together; it need not be owned by any single
module. Its text is the definition. User and system scenarios are representative examples that make
the behavior and component collaboration concrete; they are not an exhaustive substitute for the
requirements.

In the maintained sources the specifying level is recorded as the feature's `module` (the module
whose `features/` directory holds the feature root), and the workspace protocol still calls that
module the `providing_module`. Both names date from the earlier one-module-per-feature rule; the
constitution (principle A.III) no longer requires it, and aligning the path layout and field names
is tracked as follow-up work in Feature 001. Where features at the next level down refine a
feature, the `refines` links connect adjacent levels only and remain acyclic, so the feature
hierarchy stays aligned with the module hierarchy rather than becoming one flat backlog detached
from architecture.

Features also have one optional containment level. A large correlated feature may own immediate
sub-features, each with its own TL;DR, specification, and design reference, but those children
remain subordinate to the parent, inherit its level, and cannot contain more children. This is not
cross-level refinement: containment simplifies behavioral documentation inside one feature, while
`refines` explains realization across adjacent architecture levels.

## One level at a time

Large systems require abstraction. At one Concorde architecture level, a maintainer sees:

- the current module's responsibility, features, and provided/required boundary contracts;
- its immediate submodules, each with its features and boundary contracts;
- permitted external actors or systems;
- the organization of those visible participants;
- contract-governed interactions for current-level scenarios; and
- navigation references to the level's summary, design reference, and view, and to each feature's
  TL;DR, never their bodies.

Child feature bodies, grandchildren, classes, and deeper implementation details remain hidden. When
the maintainer deliberately zooms into a child, that child becomes the current module and the same
visibility rule repeats. A level may show selected detail from below when that makes the level
clearer, provided the detail stays authoritative at its own level; it should not do so by default.

This is the purpose of bounded context in Concorde: not to summarize the whole repository, but to
return the smallest architectural slice needed for the current ownership, planning, or implementation
decision.

## Five durable questions, five authorities

| Question | Authority |
|---|---|
| What must the feature do, and why? | Feature `spec.md` |
| At which level is it specified, which modules realize it, what are their boundaries, and how are immediate children organized? | `module.md` (the module summary), module contracts, and `architecture.json` |
| Why is the level built this way, how is it implemented, and what was tried and rejected? | Module `design.md` (the design reference), consulted deliberately and never read implicitly |
| How does the accepted implementation realize this feature across those boundaries? | Feature `design.md` (the feature design reference), needed only when writing the code or fixing a bug |
| What exists and has been demonstrated? | Code, tests, and explicit evidence references |

A feature's `tldr.md` is not a sixth authority but the read-first orientation over the feature: a
self-contained quick understanding of its purpose, functionality, structure, and logic that
summarizes `spec.md` and never defines beyond it. Read it first; open `spec.md` for a requirement's
exact wording and `design.md` only to write the code.

The current plan, task list, checklist state, research, and validation notes are useful during a
delivery attempt, but they are not permanent intent. Concorde keeps them in `implementation/` and
requires an explicit hardening decision before accepted realization knowledge enters the feature
`design.md` or attempt-derived rationale enters the module's `design.md`.

## What Concorde adds to Spec Kit

Spec Kit continues to own specification, clarification, planning, tasks, implementation, analysis,
and convergence. Concorde adds architectural controls around that lifecycle:

- root architecture initialization;
- bounded context retrieval and read-only, source-grounded workflow questions;
- resolution and validation of nested feature workspaces selected through standard Spec Kit;
- phase routing between durable feature files and a temporary implementation attempt;
- deterministic validation of identity, hierarchy, contracts, views, scenarios, references, and
  evidence status; and
- approval-gated hardening of a completed attempt into the durable accepted realization,
  optionally amending the module design reference.

Installation is also Spec Kit-native. A bundle pins a preset and extension; the active coding-agent
integration presents their command definitions as skills or slash commands. The detailed boundary is
specified by [Feature 003](../specs/concorde/features/003-install-concorde-speckit/spec.md).

## What Concorde deliberately does not do

Concorde does not replace Spec Kit, choose architecture without maintainer review, model every class
or function, or treat valid diagrams as proof that code works. It also does not turn Docusaurus or
generated HTML into a source of intent. The documentation site specified by
[Feature 002](../specs/concorde/features/002-create-project-docsite/spec.md) is a reproducible read
model over the maintained sources.

The next guide, [Specifications, design, and architecture](specification-model.md), explains how these
authorities are represented and how their lifetimes differ.
