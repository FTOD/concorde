---
title: Project Structure and Source Authority
sidebar_position: 5
---

# Project Structure and Source Authority

A Concorde project contains installed workflow machinery, maintained intent, temporary delivery
artifacts, executable code, and generated projections. Their location tells you who owns them and
whether they should survive a milestone.

```text
<project>/
├── .concorde/config.json
├── .specify/feature.json
├── .specify/extensions/concorde/
├── .agents/skills/speckit-*/SKILL.md
├── specs/<root-module>/
│   ├── module.md
│   ├── architecture.json
│   ├── contracts/
│   ├── features/<feature>/
│   │   ├── spec.md
│   │   ├── design.md
│   │   ├── contracts/
│   │   ├── diagrams/
│   │   └── implementation/
│   └── modules/<child-module>/
├── docs/
├── generated/
├── docsite/
├── <source directories>/
└── <test directories>/
```

## What each area owns

| Location | Role | Maintained? |
|---|---|---|
| `.concorde/config.json` | Selects the specification root and Concorde runtime profile. | Yes, as project control state |
| `.specify/feature.json` | Selects the active nested feature for normal Spec Kit phases. | Yes, as workflow control state |
| `.specify/extensions/concorde/` | Installed launchers, adapters, and deterministic runtime. | Installed package payload, not project intent |
| `.agents/skills/` or another integration directory | Agent-facing materialization of command instructions. | Installed command surface, not project intent |
| `specs/` | Durable architecture, feature behavior, accepted design, contracts, and maintained diagrams. | Yes; canonical intent |
| `specs/**/implementation/` | Current plan, tasks, checklists, research, and evidence for one attempt. | Temporary until hardening |
| `docs/` | Explanatory project guides such as this page. | Yes; canonical documentation |
| Source and tests | Runtime behavior and executable evidence. | Yes |
| `generated/` | Reproducible delivered diagrams and other projections. | Project policy decides tracking; never canonical intent |
| `docsite/.generated/`, `docsite/build/` | Disposable renderer input and verified static-site output. | No; regenerate them |

## Where to make a change

- Change required user-visible behavior in the owning feature's `spec.md`.
- Change an accepted feature realization through a completed, explicitly approved hardening step.
- Change module ownership, boundaries, or current-level organization in `module.md`, its contracts,
  and `architecture.json` together.
- Change an in-progress delivery approach under the selected feature's `implementation/` directory.
- Change explanatory adoption or contributor guidance under `docs/`.
- Change code and tests when implementation behavior changes, then reconcile evidence with maintained
  intent.

Do not edit materialized content beneath `docsite/.generated/` or the built website. Do not use
generated HTML to correct a diagram; edit its maintained Archify JSON and redeliver the projection.

## Architecture and feature nesting

Feature workspaces belong beneath the module that provides the behavior. A large project therefore
does not need one flat `specs/NNN-feature` list. The selected feature may be several module levels
deep, while Concorde's workspace adapter still gives normal Spec Kit commands the canonical feature
root and temporary implementation paths.

The project website preserves this hierarchy in its Architecture and Features views. It also shows
source provenance so a reader can navigate from a rendered page back to the correct maintained file.

See [Specifications, Design, and Architecture](specification-model.md) for artifact semantics and the
[canonical root architecture](../specs/concorde/module.md) for this project's concrete module
hierarchy. The [docsite contributor guide](contributing/docsite.md) defines publication rules.
