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
2. the module and abstraction level that own it;
3. the contracts and immediate components involved in realizing it;
4. the implementation detail and rationale each level accumulates, kept beneath a short summary; and
5. the realization that was actually accepted after implementation.

The normative definition is [Feature 001](../specs/concorde/features/001-concorde-workflow/spec.md).

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

## The model: modules provide features

Features have one optional decomposition level. A large correlated feature may own immediate
sub-features, each with its own TL;DR, specification, and design reference, but those children
remain subordinate to the parent, inherit its module, and cannot contain more children. This is not module-level feature refinement:
containment simplifies behavioral documentation inside one feature, while `refines` explains
realization across adjacent architecture levels.

A **module** is an architecturally meaningful unit with one responsibility and explicit provided and
required contracts. It normally groups correlated features so they can share internal realization
without exposing that realization across the boundary.

A **feature** is observable behavior provided by exactly one module at its current abstraction
level. Its text is the definition. User and system scenarios are representative examples that make
the behavior and component collaboration concrete; they are not an exhaustive substitute for the
requirements.

A feature that spans multiple immediate children belongs to their nearest common parent. Child-level
features may then refine that parent feature. This produces a feature hierarchy aligned with the
module hierarchy rather than one flat backlog detached from architecture.

## One level at a time

Large systems require abstraction. At one Concorde architecture level, a maintainer sees:

- the current module's responsibility, features, and provided/required I/O contracts;
- its immediate submodules and concise summaries of their I/O;
- permitted external actors or systems;
- the organization of those visible participants;
- contract-governed interactions for current-level scenarios; and
- navigation references to the level's summary, design reference, and view, and to each feature's
  TL;DR, never their bodies.

Child feature bodies, grandchildren, classes, and deeper implementation details remain hidden. When
the maintainer deliberately zooms into a child, that child becomes the current module and the same
visibility rule repeats.

This is the purpose of bounded context in Concorde: not to summarize the whole repository, but to
return the smallest architectural slice needed for the current ownership, planning, or implementation
decision.

## Five durable questions, five authorities

| Question | Authority |
|---|---|
| What must the feature do, and why? | Feature `spec.md` |
| Which module owns it, what are its boundaries, and how are immediate children organized? | `module.md` (the module summary), module contracts, and `architecture.json` |
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
- bounded context retrieval;
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
