---
id: module.concorde.commands
kind: module
parent: module.concorde
modules: []
features:
  - feature.commands.project-workflow
diagrams: []
---

# Architecture: Commands

## Responsibility

Define complete, readable lifecycle instructions and Markdown format references, then project them
consistently to supported coding-agent integrations without layered composition.

## Boundary

Commands owns root command prose, root templates, compatibility command IDs, projection metadata,
and phase authority rules. It does not own deterministic runtime behavior, project specifications,
agent execution, or integration-specific product internals.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.commands.manifest` | configuration | Declares the exact command/template inventory and supported integrations. | `concorde.json` |
| `entity.commands.sources` | directory | Canonical instructions for constitution, specification, planning, implementation, validation, and related phases. | `commands` |
| `entity.commands.feature-template` | document | Complete direct-feature format with outcome, usage, scenarios, interfaces, architecture zoom, requirements, and criteria. | `templates/feature-template.md` |
| `entity.commands.plan-template` | document | Temporal planning format grounded in feature, architecture, code, tests, risks, and evidence. | `templates/plan-template.md` |
| `entity.commands.tasks-template` | document | Dependency-ordered traced task format with test-first and evidence gates. | `templates/tasks-template.md` |
| `entity.commands.checklist-template` | document | Reviewer-owned requirements-quality checklist format. | `templates/checklist-template.md` |
| `entity.commands.constitution-template` | document | Governance-document format reference. | `templates/constitution-template.md` |
| `entity.commands.reflection-template` | document | Project reflection log grammar. | `templates/reflections-template.md` |
| `entity.commands.projector` | program | Parses canonical command front matter, resolves package tokens, and renders Codex/Claude skill files. | `src/concorde/command_assets.py` |
| `entity.commands.reflection-assets` | directory | Reflection triage orchestrator, roles, and integration templates. | `agent-assets/reflections` |
| `entity.commands.checkout-sync` | program | Compares and refreshes this repository's generated agent surfaces. | `scripts/development/sync-agent-surfaces.py` |
| `entity.commands.coding-agent` | external-system | Executes one rendered command within its declared phase boundary. | `external:coding-agent` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.commands.manifest` | `declares` | `entity.commands.sources` | Inventories every command exactly once. |
| `entity.commands.manifest` | `declares` | `entity.commands.feature-template` | Includes the complete durable feature format. |
| `entity.commands.manifest` | `declares` | `entity.commands.plan-template` | Includes the plan format without composition. |
| `entity.commands.manifest` | `declares` | `entity.commands.tasks-template` | Includes the tasks format without composition. |
| `entity.commands.projector` | `reads_from` | `entity.commands.sources` | Uses root command files as the only command authority. |
| `entity.commands.projector` | `transforms` | `entity.commands.sources` | Renders one integration-specific skill per command. |
| `entity.commands.checkout-sync` | `calls` | `entity.commands.projector` | Regenerates source-checkout projections for both integrations. |
| `entity.commands.sources` | `calls` | `module.concorde.runtime` | Requests deterministic workspace and lifecycle operations. |
| `entity.commands.sources` | `reads_from` | `module.concorde.workspace` | Uses one selected feature's bounded maintained, temporal, and executable context. |
| `entity.commands.coding-agent` | `implements` | `entity.commands.sources` | Follows rendered instructions and their write boundaries. |
| `entity.commands.reflection-assets` | `writes_to` | `module.concorde.workspace` | Coordinates reflection plans while retaining one persisted project log. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.commands.project` | Installer or checkout sync requests an integration. | Validate root inventory; parse each command; resolve `{SCRIPT}` and `{FRAMEWORK}` for the target; add integration metadata; render reflection roles; compare owned outputs. | Codex or Claude receives the same Concorde phase intent with correct runtime/template paths. | `contract.commands.agent-surface` |
| `interaction.commands.execute` | Maintainer invokes a rendered command. | Resolve Protocol 12 when path-sensitive; read only bounded authorities; perform the declared phase; call Runtime for deterministic work; report checks and limitations. | One phase completes or stops without crossing its authority boundary. | `contract.commands.workflow-guidance`, `contract.runtime.operations`, `contract.workspace.feature-workspace` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.commands.project-workflow` | Project one canonical command set and complete Markdown formats into consistent agent-native workflow surfaces. |

## Decisions

- Root `commands/` and `templates/` are canonical; `.agents/**` and `.claude/**` are generated.
- Commands are complete documents, not fragments merged through priorities or strategies.
- Templates are complete format references; project files become authority only after being authored.
- Compatibility `speckit-*` IDs are retained while metadata names Concorde as author and source owner.
- Deterministic filesystem semantics remain in Runtime, not conversational command prose.
