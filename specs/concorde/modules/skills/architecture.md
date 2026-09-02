---
id: module.concorde.skills
kind: module
parent: module.concorde
modules: []
features:
  - feature.skills.project-workflow
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-skills-system-overview.html
---

# Architecture: Skills

## Responsibility

Define the complete leaf capabilities through which users ask an agent to perform one bounded
Concorde phase, and project those capabilities consistently to supported coding-agent integrations.

## Boundary

Skills owns canonical `skills/<name>/SKILL.md` prompts, stable `concorde-*` names, leaf metadata,
complete Markdown format references, capability parsing, and checkout projection. A leaf Skill may
invoke deterministic Tools but contains no multi-Skill loop or LangGraph topology. This module does
not own Tool implementation, Operation control graphs, project specifications, agent execution, or
integration-specific product internals.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.skills.manifest` | configuration | Package Manifest 2 declares the exact leaf Skill inventory and globally shared capability namespace. | `concorde.json` |
| `entity.skills.sources` | directory | Canonical directories containing exactly one independently invocable leaf `SKILL.md` each. | `skills` |
| `entity.skills.skill-prompt` | document | One complete leaf capability prompt that may invoke Tools but does not orchestrate multiple Skills. | `concept:skills/<name>/SKILL.md` |
| `entity.skills.feature-template` | document | Complete direct-feature format with outcome, usage, scenarios, interfaces, architecture zoom, requirements, and criteria. | `templates/feature-template.md` |
| `entity.skills.plan-template` | document | Temporal planning format grounded in feature, architecture, code, tests, risks, and evidence. | `templates/plan-template.md` |
| `entity.skills.tasks-template` | document | Dependency-ordered traced task format with test-first and evidence gates. | `templates/tasks-template.md` |
| `entity.skills.checklist-template` | document | Reviewer-owned requirements-quality checklist format. | `templates/checklist-template.md` |
| `entity.skills.constitution-template` | document | Governance-document format reference. | `templates/constitution-template.md` |
| `entity.skills.reflection-template` | document | Project reflection-log grammar. | `templates/reflections-template.md` |
| `entity.skills.projector` | program | Parses leaf and Operation skill metadata, resolves package tokens, and renders Codex/Claude Skill files. | `src/concorde/skill_assets.py` |
| `entity.skills.reflection-assets` | directory | Internal reflection investigator/implementer roles and integration templates. | `agent-assets/reflections` |
| `entity.skills.checkout-sync` | program | Compares and refreshes this repository's generated agent capability surfaces. | `scripts/development/sync-agent-surfaces.py` |
| `entity.skills.coding-agent` | external-system | Executes one installed Skill within its declared authority boundary. | `external:coding-agent` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.skills.manifest` | `declares` | `entity.skills.sources` | Inventories every leaf Skill exactly once. |
| `entity.skills.sources` | `contains` | `entity.skills.skill-prompt` | Gives each leaf capability one canonical Markdown authority. |
| `entity.skills.manifest` | `declares` | `entity.skills.feature-template` | Includes the complete durable feature format. |
| `entity.skills.manifest` | `declares` | `entity.skills.plan-template` | Includes the temporal plan format. |
| `entity.skills.manifest` | `declares` | `entity.skills.tasks-template` | Includes the temporal task format. |
| `entity.skills.projector` | `reads_from` | `entity.skills.sources` | Loads leaf Skills without composing or rewriting their prompt semantics. |
| `entity.skills.projector` | `transforms` | `entity.skills.skill-prompt` | Produces one integration-native Skill from each canonical leaf Skill. |
| `entity.skills.checkout-sync` | `calls` | `entity.skills.projector` | Regenerates checkout projections for both supported integrations. |
| `entity.skills.skill-prompt` | `calls` | `module.concorde.runtime` | Invokes deterministic workspace and lifecycle Tools when required. |
| `entity.skills.skill-prompt` | `reads_from` | `module.concorde.workspace` | Uses one selected feature's bounded durable, temporal, and executable context. |
| `entity.skills.coding-agent` | `implements` | `entity.skills.skill-prompt` | Follows installed instructions and their write boundaries. |
| `entity.skills.reflection-assets` | `writes_to` | `module.concorde.workspace` | Supports reflection triage while retaining one persisted project log. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.skills.project` | Installer or checkout sync requests an integration. | Validate Package Manifest 2; parse each canonical leaf or paired Operation skill; resolve installed entry points; add provenance; compare owned outputs. | Codex or Claude receives one globally unique Skill per declared capability. | `contract.skills.agent-surface` |
| `interaction.skills.execute` | Maintainer or Operation invokes a leaf Skill. | Resolve Protocol 13 when path-sensitive; read only bounded authorities; perform the declared phase; invoke deterministic Tools as needed; report checks and limitations. | One independently invocable phase completes or stops without crossing its authority boundary. | `contract.skills.workflow-guidance`, `contract.runtime.tools`, `contract.workspace.feature-workspace` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.skills.project-workflow` | Expose every Concorde lifecycle phase as one complete, independently invocable leaf Skill with consistent installed semantics. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- `skills/<name>/SKILL.md` is the sole prompt authority for a leaf capability; installed files are
  generated projections.
- Leaf Skills may invoke Tools but never embed a multi-Skill LangGraph or duplicate another Skill's
  prompt body.
- Leaf and Operation capabilities share one global `concorde-*` installed namespace.
- Templates remain readable format references, not fragments merged into Skill prompts.
- Reflection role assets are internal support for the paired reflection-triage Operation, not
  additional user-facing leaf capabilities.
