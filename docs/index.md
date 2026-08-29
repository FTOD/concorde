---
title: Concorde Documentation
slug: /
sidebar_position: 1
---

# Concorde Documentation

Concorde is a Spec Kit-native workflow for directing software development when coding agents write
much of the code. It shifts the maintainer's attention from individual code details to the things
that must remain intentional: required behavior, the level at which each feature is specified and
the modules that realize it, boundary contracts, component collaboration, accepted realization, and
evidence.

The central idea is simple: feature specifications are not enough to control the structure of a
large AI-developed system. Concorde combines spec-driven development with Architecture as Code, then
organizes both as a hierarchy that can be inspected one level at a time.

## What this site contains

This site is one read-only view over maintained project sources. Its three navigation areas answer
different questions:

| Area | Use it to answer | Maintained authority |
|---|---|---|
| **Architecture** | At which level is this behavior specified, and which modules realize it? What can cross a boundary? Which immediate components collaborate? Why is it built this way? | `module.md` summaries, their adjacent `design.md` design references, module contracts, and the module-owned Archify diagrams under `specs/**/architecture/` |
| **Features** | What is this feature, exactly what must it do, and how does the accepted implementation realize it? | The feature's durable `abstract.md` (the page it opens on), `design.md`, and `implementation.md` under `specs/` |
| **Documentation** | How do I understand, install, use, and contribute to Concorde? | Explanatory Markdown under `docs/` |

The website does not become a new source of truth. Every generated page identifies the maintained
file from which it was built. If a page is wrong, edit that source and rebuild the site.

## Choose a path

If you are evaluating Concorde, start with [What Concorde controls](framework-overview.md). It
explains why behavioral specifications, architecture, and accepted realization are separate
authorities.

If you want to try it, use the [Quick start](quick-start.md). It separates terminal commands from
agent-invoked skills and takes you from installation to a first selected feature.

If you are already working in a Concorde project:

1. Use [Specifications, design, and architecture](specification-model.md) to decide what kind of
   information you are changing.
2. Use [Project structure and source authority](project-structure.md) to find its canonical file.
3. Follow the [Concorde workflow](concorde-workflow.md) from placement and specification through validation
   and hardening.
4. Consult [Commands and installed surfaces](commands.md) to choose the right operation and
   understand what actually executes it.
5. If you are contributing to Concorde itself, read
   [Developing Concorde with Concorde](self-hosting.md) before changing framework sources.
6. If you are cutting a release, follow [Releasing Concorde](releasing.md).

If you are modifying the publication system, read [Contributing to the docsite](contributing/docsite.md).

## The normative project sources

These guides explain the framework; they do not replace its specifications. Complete requirements,
edge cases, status, and acceptance criteria live in:

- the [root Concorde architecture](../specs/concorde/module.md) summary and its adjacent `design.md`
  reference;
- [Feature 001: the Concorde workflow](../specs/concorde/features/001-concorde-workflow/design.md),
  whose [abstract](../specs/concorde/features/001-concorde-workflow/abstract.md) is the fastest orientation;
- [Feature 002: project docsite publication](../specs/concorde/features/002-create-project-docsite/design.md); and
- [Feature 003: installation through Spec Kit](../specs/concorde/features/003-install-concorde-speckit/design.md); and
- [Feature 004: development self-hosting](../specs/concorde/features/004-self-host-concorde/design.md).

Feature status is shown rather than interpreted. A published draft remains a draft; publication does
not imply approval, implementation, or verified evidence.

## One rule to remember

Do not resolve disagreement by editing a generated page or by making the code the implicit
specification. Identify which maintained authority owns the disputed fact, update it through the
appropriate review step, validate the result, and regenerate the read model.
