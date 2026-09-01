---
id: module.concorde.skills
kind: module
parent: module.concorde
modules: []
features:
  - feature.skills.compose-workflow
diagrams: []
---

# Architecture: Skills

## Responsibility

Compose Concorde's module/entity/interface authority model into precise user-visible coding-agent
instructions for normal Spec Kit phases and Concorde-specific operations.

## Boundary

Skills owns canonical command prose, feature/plan/task/reflection templates, phase write boundaries,
and platform-neutral operation intent. It does not own deterministic runtime semantics, Spec Kit's
command composer, installed projection locations, maintained project specifications, or product code.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.skills.preset-manifest` | configuration | Declares Concorde's composed templates and normal/additive command sources. | `presets/concorde/preset.yml` |
| `entity.skills.phase-commands` | directory | Canonical replacements/additions for specify, clarify, checklist, plan, tasks, implement, analyze, converge, issue projection, and fast loop. | `presets/concorde/commands` |
| `entity.skills.feature-template` | document | Appended feature-design structure for outcome, interfaces, usage, architecture zoom, requirements, and evidence expectations. | `presets/concorde/templates/design-template.md` |
| `entity.skills.plan-template` | document | Appended planning gate for bounded architecture, code/test reality, interface deltas, and temporal artifacts. | `presets/concorde/templates/plan-template.md` |
| `entity.skills.tasks-template` | document | Appended task rules for traced architecture/design/code/test/projection reconciliation and evidence. | `presets/concorde/templates/tasks-template.md` |
| `entity.skills.reflection-template` | document | Grammar for the tracked project-control reflection log. | `presets/concorde/templates/reflections-template.md` |
| `entity.skills.extension-commands` | directory | Canonical init, context, validate, deliver, and read-only ask operation guidance. | `extensions/concorde/commands` |
| `entity.skills.reflection-assets` | directory | Canonical reflection triage orchestrator, roles, and platform projections. | `extensions/concorde/agent-assets/reflections` |
| `entity.skills.spec-kit-composer` | external-system | Host that composes the preset/extension command sources for a selected coding-agent integration. | `external:specify-cli==0.16.4` |
| `entity.skills.coding-agent` | external-system | Executes the composed instructions and authors only the files the phase permits. | `external:coding-agent` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.skills.preset-manifest` | `declares` | `entity.skills.phase-commands` | Registers canonical phase guidance and composition strategy. |
| `entity.skills.preset-manifest` | `declares` | `entity.skills.feature-template` | Adds the Concorde feature authority profile to specification. |
| `entity.skills.preset-manifest` | `declares` | `entity.skills.plan-template` | Adds bounded architecture/code planning gates. |
| `entity.skills.preset-manifest` | `declares` | `entity.skills.tasks-template` | Adds architecture/evidence task rules. |
| `entity.skills.phase-commands` | `reads_from` | `module.concorde.workspace-files` | Resolve one feature design, module architecture, and attempt context. |
| `entity.skills.phase-commands` | `calls` | `module.concorde.scripts` | Request deterministic workspace, validation, and delivery operations. |
| `entity.skills.extension-commands` | `calls` | `module.concorde.scripts` | Invoke init/context/validate/deliver through portable launchers. |
| `entity.skills.spec-kit-composer` | `transforms` | `entity.skills.phase-commands` | Produces platform-specific installed skills/slash commands from canonical intent. |
| `entity.skills.spec-kit-composer` | `transforms` | `entity.skills.extension-commands` | Produces installed Concorde-specific operation surfaces. |
| `entity.skills.coding-agent` | `implements` | `entity.skills.phase-commands` | Follows the composed workflow while preserving phase authority. |
| `entity.skills.reflection-assets` | `writes_to` | `module.concorde.workspace-files` | Coordinates maintainer-owned reflection plans/worktrees without duplicating reflection identity. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.skills.compose` | Spec Kit installs or recomposes the Concorde preset/extension. | Read manifests; compose canonical command/template layers; project the active integration; verify declared installed surfaces. | Each platform exposes the same operation intent and Profile 7 authority rules. | `contract.skills.agent-surface`, `contract.concorde.spec-kit-platform` |
| `interaction.skills.execute-phase` | Maintainer invokes a phase skill. | Resolve Protocol 12 context; read the direct feature file, module architecture, code/tests, and matching stable-ID control attempt; author only allowed paths; invoke Scripts for deterministic work; report evidence. | One bounded phase completes or stops with sources preserved. | `contract.skills.workflow-guidance`, `contract.scripts.operations`, `contract.workspace-files.feature-workspace` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.skills.compose-workflow` | Materialize consistent, platform-appropriate instructions that direct every Concorde phase through the same architecture and authority model. |

## Decisions

- Canonical package prose is authoritative; `.specify`, Codex, and Claude copies are generated and verified.
- Skills may authorize agent-authored changes but delegate deterministic structural operations to Scripts.
- The source profile is described once across shared gates and checked by contract tests to prevent command drift.
