---
title: Concorde Documentation
slug: /
sidebar_position: 1
---

# Concorde Documentation

Concorde is a Spec Kit-native workflow for directing software development when coding agents write
much of the code. It shifts the maintainer's attention from individual code details to the things
that must remain intentional: required behavior, module ownership, boundary contracts, component
collaboration, accepted design, and evidence.

The central idea is simple: feature specifications are not enough to control the structure of a
large AI-developed system. Concorde combines spec-driven development with Architecture as Code, then
organizes both as a hierarchy that can be inspected one level at a time.

## What this site contains

This site is one read-only view over maintained project sources. Its three navigation areas answer
different questions:

| Area | Use it to answer | Maintained authority |
|---|---|---|
| **Architecture** | Which module owns this behavior? What can cross its boundary? Which immediate components collaborate? | `module.md`, module contracts, and declared Archify sources under `specs/` |
| **Features** | What must a feature do, why does it matter, and how does the accepted implementation realize it? | The feature's durable `spec.md` and `design.md` under `specs/` |
| **Documentation** | How do I understand, install, use, and contribute to Concorde? | Explanatory Markdown under `docs/` |

The website does not become a new source of truth. Every generated page identifies the maintained
file from which it was built. If a page is wrong, edit that source and rebuild the site.

## Choose a path

If you are evaluating Concorde, start with [What Concorde controls](framework-overview.md). It
explains why behavioral specifications, architecture, and accepted design are separate authorities.

If you want to try it, use the [Quick start](quick-start.md). It separates terminal commands from
agent-invoked skills and takes you from installation to a first selected feature.

If you are already working in a Concorde project:

1. Use [Specifications, design, and architecture](specification-model.md) to decide what kind of
   information you are changing.
2. Use [Project structure and source authority](project-structure.md) to find its canonical file.
3. Follow the [Concorde workflow](concorde-workflow.md) from ownership and specification through validation
   and hardening.
4. Consult [Commands and installed surfaces](commands.md) to choose the right operation and
   understand what actually executes it.

If you are modifying the publication system, read [Contributing to the docsite](contributing/docsite.md).

## The normative project sources

These guides explain the framework; they do not replace its specifications. Complete requirements,
edge cases, status, and acceptance criteria live in:

- the [root Concorde architecture](../specs/concorde/module.md);
- [Feature 001: the Concorde workflow](../specs/concorde/features/001-concorde-workflow/spec.md);
- [Feature 002: project docsite publication](../specs/concorde/features/002-create-project-docsite/spec.md); and
- [Feature 003: installation through Spec Kit](../specs/concorde/features/003-install-concorde-speckit/spec.md).

Feature status is shown rather than interpreted. A published draft remains a draft; publication does
not imply approval, implementation, or verified evidence.

## One rule to remember

Do not resolve disagreement by editing a generated page or by making the code the implicit
specification. Identify which maintained authority owns the disputed fact, update it through the
appropriate review step, validate the result, and regenerate the read model.
