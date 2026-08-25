---
title: Commands and Installed Surfaces
sidebar_position: 7
---

# Commands and Installed Surfaces

Concorde has two command families. Normal Spec Kit phases keep their familiar names but gain nested
workspace routing from the Concorde preset. Concorde-specific operations are added by the extension.

## Normal Spec Kit phases

| Phase | Durable or temporary target in Concorde |
|---|---|
| `specify` | Creates or updates durable `spec.md`, preserves existing `design.md`, and opens temporary checklist state when needed. |
| `clarify` | Resolves ambiguity in durable feature behavior. |
| `checklist` | Writes review state beneath `implementation/checklists/`. |
| `plan` | Builds the current attempt beneath `implementation/` from `spec.md` and the accepted `design.md`. |
| `tasks` | Writes dependency-ordered work to `implementation/tasks.md`. |
| `implement` | Executes the current task set using bounded architecture context. |
| `analyze` | Checks consistency across durable behavior/design and the temporary plan/tasks. |
| `converge` | Assesses code against intent and appends genuinely unbuilt work. |
| `taskstoissues` | Projects the active task set into issue-ready work items. |

The preset replaces the agent instructions for these phases so each one first resolves the active
nested feature. It does not reimplement Spec Kit's lifecycle.

## Concorde-specific commands

In package-neutral form, the extension owns six commands:

| Command | Purpose | Mutation rule |
|---|---|---|
| `speckit.concorde.init` | Propose the root module package and Concorde configuration. | Writes only an explicitly approved proposal. |
| `speckit.concorde.feature.create` | Propose a feature beneath a reviewed owning module. | Creates one canonical feature root only after approval. |
| `speckit.concorde.feature.select` | Select an existing nested feature for normal phases. | Atomically updates workflow control state. |
| `speckit.concorde.context` | Return one bounded module or feature context. | Read-only. |
| `speckit.concorde.validate` | Check hierarchy, identities, references, contracts, views, scenarios, and evidence. | Read-only. |
| `speckit.concorde.feature.harden` | Propose and promote accepted implementation detail into durable design. | Requires complete tasks, resolved checklists, current digests, and explicit approval. |

An integration may present dots as hyphens. For example, Codex skills use names such as
`$speckit-concorde-feature-select`. The presentation changes; command intent does not.

## Skill, command, launcher, and runtime

These terms refer to different layers:

1. A **package-neutral command definition** is Markdown shipped in the preset or extension.
2. An **installed skill or slash command** is the active coding-agent integration's presentation of
   that definition. It tells the agent what procedure to follow; it is not the implementation.
3. A **workspace adapter or launcher** resolves selected feature paths or locates the installed
   extension payload using project-relative locations.
4. The **Concorde Python runtime** performs deterministic initialization, feature selection, context,
   validation, and hardening controls.

This separation lets the same Concorde package work across supported coding-agent integrations while
keeping path resolution and validation reproducible. It also prevents repository-local skill edits
from masquerading as a distributable framework change: user projects receive the command overrides
through the installed preset and extension.

For installation details, see the [quick start](quick-start.md). For the normative package boundary,
see the [Feature 003 specification](../specs/concorde/features/003-install-concorde-speckit/spec.md).
