---
title: Concorde Documentation
slug: /
sidebar_position: 1
---

# Concorde Documentation

Concorde is a Spec Kit-native, architecture-aware workflow for AI-developed software. It keeps
behavioral specifications, accepted feature design, module boundaries, implementation work, and
evidence connected without asking maintainers to control every line of generated code.

This site is the project's generated read model. It presents three complementary views:

| View | What it answers | Canonical source |
|---|---|---|
| Architecture | Where does behavior belong, what are the boundaries, and how do immediate components interact? | Module, contract, and Archify sources under `specs/` |
| Features | What must the system do, why, and how does the accepted implementation realize it? | Each feature's durable `spec.md` and `design.md` under `specs/` |
| Documentation | How do people understand, adopt, operate, and contribute to the framework? | Hand-written guides under `docs/` |

## Recommended reading path

1. Follow the [quick start](quick-start.md) to preview this site or install Concorde into a test
   project.
2. Read [What Concorde is](framework-overview.md) for the problem, principles, and relationship to
   Spec Kit.
3. Learn the [specification and design model](specification-model.md), including durable and
   temporary artifacts.
4. Use the [project structure guide](project-structure.md) to find the authoritative file for a
   change.
5. Walk through the [core workflow](core-workflow.md) and keep the [command reference](commands.md)
   nearby.

For canonical project intent, browse the [root Concorde architecture](../specs/concorde/module.md),
the [core workflow feature](../specs/concorde/features/001-concorde-starter-workflow/spec.md), the
[project-docsite feature](../specs/concorde/features/002-create-project-docsite/spec.md), and the
[Spec Kit installation feature](../specs/concorde/features/003-install-concorde-speckit/spec.md).
Contributors changing publication behavior should also read the
[docsite contributor guide](contributing/docsite.md).

## Source of truth

Edit Markdown in its canonical repository location. The build keeps `docs/` direct and materializes
only ignored renderer projections from `specs/`; those projections never become maintained copies.

When a guide and a canonical specification disagree, treat the specification as authoritative and
fix the guide. Generated HTML is always a projection, never a place to edit project meaning.
