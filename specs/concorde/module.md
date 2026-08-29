---
id: module.concorde
kind: module
parent: null
children:
  - module.concorde.skills
  - module.concorde.scripts
  - module.concorde.workspace-files
  - module.concorde.distribution
  - module.concorde.auto-docs
features:
  - feature.concorde.workflow
  - feature.concorde.publish-project-docsite
  - feature.concorde.install-with-spec-kit
  - feature.concorde.self-host-framework
  - feature.concorde.record-workflow-reflections
contracts:
  provided:
    - contract.concorde.workflow
    - contract.auto-docs.architecture-site
    - contract.concorde.spec-kit-installation
  required:
    - contract.concorde.spec-kit-platform
---

# Concorde

## Responsibility

Provide a skill-guided development workflow in which maintainers invoke skills, agents run supporting
scripts when deterministic behavior is required, and both work through an explicit set of durable,
temporal, and generated files.

## Boundary

Concorde owns the installed skill instructions, portable launchers and runtime, workspace-file model,
installable packages, and optional documentation projection. It does not own the coding-agent runtime,
Spec Kit's base lifecycle, user product code, Archify rendering semantics, or Docusaurus.

## Structure

The primary architecture is a three-part interaction:

1. **Skills** are the only feature-work interface exposed to maintainers and coding agents.
2. **Scripts** provide routing and deterministic operations requested by those skills.
3. **Workspace Files** hold the durable specification and the current attempt's temporal working memory.

**Distribution** installs the skill and script packages. **Auto-Docs** reads validated workspace
files and publishes a disposable read model. Neither supporting module participates in ordinary
feature authoring. The maintained interaction view is
[level-view.json](architecture/diagrams/level-view.json).

In tooling, `module.concorde` is the **specification root** only because `.concorde/config.json`
selects it as the top-level package for this project. “Root” describes storage and lookup, not a
runtime component or a special architectural layer. Features registered directly here are
**project-level features**: user outcomes realized across the modules below, not blocks beside them.

At setup time, Spec Kit resolves the `concorde-bundle` from a catalog, installs its preset and
extension, and uses the active coding-agent integration to materialize their command sources.

The extension contributes five Concorde-specific skills: four invoke Scripts operations and the
read-only `ask` skill is followed directly by the coding agent.

## Features

| Feature ID | Observable outcome | Primary path |
|---|---|---|
| `feature.concorde.workflow` | Direct a feature from specification through explicit implementation acceptance. | Skills → Scripts when needed → Workspace Files |
| `feature.concorde.record-workflow-reflections` | Record workflow problems in the one durable project reflection log. | Skills → Workspace Files |
| `feature.concorde.install-with-spec-kit` | Inspect, install, update, and remove the supported Concorde package set. | Distribution → Skills + Scripts |
| `feature.concorde.self-host-framework` | Materialize and verify the current checkout through the public installation path. | Distribution → Skills + Scripts |
| `feature.concorde.publish-project-docsite` | Publish validated specifications and project docs as a browsable site. | Workspace Files → Auto-Docs |

The feature specifications remain under `features/`. They describe user outcomes; the
module split above describes how those outcomes are realized.

## Contracts

| Contract ID | Role | Purpose |
|---|---|---|
| `contract.concorde.workflow` | provided | User-visible workflow behavior across installed skills. |
| `contract.concorde.spec-kit-installation` | provided | Bundle inspection and installation behavior. |
| `contract.auto-docs.architecture-site` | provided through Auto-Docs | Published read-only project site. |
| `contract.concorde.spec-kit-platform` | required | Spec Kit component and lifecycle host behavior. |

## Submodules

| Module | Owns | Does not own |
|---|---|---|
| `module.concorde.skills` | Skill instructions, command composition, and the user-visible workflow surface. | Deterministic operation semantics or file-format authority. |
| `module.concorde.scripts` | Launchers, workspace routing, structured runtime operations, and deterministic diagnostics. | User-facing workflow prose or agent-authored content. |
| `module.concorde.workspace-files` | File roles, paths, lifetimes, selection state, and durable/temporal promotion rules. | The agent or scripts that operate on those files. |
| `module.concorde.distribution` | Bundle, catalogs, release artifacts, install/update/remove lifecycle. | Workflow behavior after installation. |
| `module.concorde.auto-docs` | Validation-gated site build and generated read model. | Maintained source authority. |

## Interaction Rules

- A maintainer MUST start feature work through an installed skill; scripts are not a parallel product UI.
- A skill MAY instruct the coding agent to read or write named workspace files directly.
- A skill MUST invoke Scripts for operations whose result must be deterministic or structurally safe.
- Scripts MUST treat Workspace Files as their input/output boundary and return structured results.
- Durable files MUST live outside `attempt/`; temporal delivery memory MUST live inside `attempt/`.
- Generated documentation MUST remain a disposable projection of validated maintained files.
- Distribution and Auto-Docs MUST NOT redefine skill, script, or workspace-file semantics.

## Representative Scenario

`feature-work` in the level view follows the normal path. The maintainer invokes a skill. The skill
names the selected feature workspace and the files relevant to the phase. The coding agent reads or
writes those files and invokes a launcher only for initialization, context retrieval, validation, or
implementation acceptance. The script resolves the selection, operates on the named files, and
returns a structured result to the skill. No other user-facing Concorde runtime exists.

## Design Rationale

The modules are named after the things a maintainer can find in an installed project: skills,
scripts, and workspace files. Distribution and Auto-Docs remain explicit because they cross the
project boundary, but they are supporting adapters rather than the center of the workflow. Detailed
source mapping and file-lifetime rules are recorded in the [design reference](design.md).
