---
title: Concorde Documentation
slug: /
sidebar_position: 1
---

# Concorde Documentation

Concorde is an architecture-aware workflow for keeping architecture, specifications, implementation,
and evidence in agreement. This site is the project's generated read model: architecture and feature
specifications share the hierarchical `specs/` tree, while project documentation lives in `docs/`.

Start with the [root Concorde architecture](../specs/concorde/module.md), continue to the
[starter workflow feature](../specs/concorde/features/001-concorde-starter-workflow/spec.md), or read the
[docsite contributor guide](contributing/docsite.md) before changing the publication pipeline.

## Source of truth

Edit Markdown in its canonical repository location. The build keeps `docs/` direct and materializes
only ignored renderer projections from `specs/`; those projections never become maintained copies.
