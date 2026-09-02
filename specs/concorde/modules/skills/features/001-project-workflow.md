---
id: feature.skills.project-workflow
kind: feature
module: module.concorde.skills
related_features:
  - feature.concorde.workflow
  - feature.operations.standard-development-loop
  - feature.runtime.run-lifecycle-tools
  - feature.workspace.manage-feature-workspace
interfaces:
  provided:
    - contract.skills.agent-surface
    - contract.skills.workflow-guidance
  required:
    - contract.runtime.tools
    - contract.workspace.feature-workspace
evidence_status: partial
---

# Feature Design: Provide Leaf Project Skills

## Outcome and Scope

Users receive one complete, independently invocable Skill for each Concorde lifecycle phase. The same
canonical prompt semantics reach Codex and Claude, and an Operation may compose those Skills without
copying prompt text.

This feature covers leaf Skill source, metadata, Tool crossings, projection, and phase boundaries. It
does not define LangGraph topology, execute an agent model, or own project artifacts.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.skills.sources` | Owns one canonical directory per leaf Skill. |
| `entity.skills.skill-prompt` | Supplies a complete independently invocable phase contract. |
| `entity.skills.projector` | Validates and renders both leaf and paired Operation skills. |
| `entity.skills.coding-agent` | Executes the installed prompt within its declared boundary. |
| `entity.skills.manifest` | Declares the exact leaf inventory and shared capability namespace. |

## Interfaces

### `contract.skills.agent-surface` — Installed capability projection

- **Consumer**: Installer, checkout synchronization, Codex, and Claude.
- **Direction**: Canonical leaf and paired Operation Markdown to integration-native Skill files.
- **Entry points**: `skills/<name>/SKILL.md`, `operations/<name>/SKILL.md`, and
  `src/concorde/skill_assets.py`.
- **Inputs**: Package Manifest 2 inventories, canonical metadata/body, integration, installed
  framework prefix, and paired Operation entry point when applicable.
- **Outputs**: One regular `.agents/skills/<name>/SKILL.md` or
  `.claude/skills/<name>/SKILL.md` file with source, kind, and entry-point provenance.
- **Obligations**: Require globally unique safe names; resolve only declared package tokens; preserve
  prompt bodies; distinguish leaf and Operation provenance; reject extras, symlinks, collisions, or
  unpaired Operations before writing.
- **Failures**: Invalid metadata, manifest drift, unsafe source/target, unknown composed Skill,
  unresolved token, or output collision blocks projection.
- **Compatibility**: Package Manifest 2 and Concorde 2.0.0 expose 16 leaf Skills plus declared paired
  Operations in one namespace, with no legacy capability reader.
- **Implementing entities**: `entity.skills.manifest`, `entity.skills.sources`,
  `entity.skills.projector`.
- **Example**: `skills/concorde-plan/SKILL.md` projects to
  `.agents/skills/concorde-plan/SKILL.md` with `kind: skill` provenance.

### `contract.skills.workflow-guidance` — Leaf phase behavior

- **Consumer**: Maintainers, coding agents, and paired Operations.
- **Direction**: User or Operation input plus bounded project context to one phase result and its
  explicitly authorized effects.
- **Entry points**: The 16 Package Manifest 2 leaf Skills under `skills/`.
- **Inputs**: User intent, Protocol 13 context when path-sensitive, complete canonical prompt, and
  only the maintained/temporal/executable sources that prompt authorizes.
- **Outputs**: Conversational result, explicit Tool results, evidence, and only phase-authorized file
  changes.
- **Obligations**: Remain independently invocable; preserve the complete prompt and phase boundary;
  invoke Tools explicitly; surface failures and evidence limitations; contain no multi-Skill graph.
- **Failures**: Workspace/tool failure, missing authority, invalid project state, denied permission,
  or unmet phase gate stops that Skill without fallback to another source.
- **Compatibility**: Protocol 13 and Delivery Proposal 9 use Tool terminology. Stable public names are
  `concorde-*`; retired dotted prompt identities are not aliases.
- **Implementing entities**: `entity.skills.skill-prompt`, `entity.skills.coding-agent`,
  `module.concorde.runtime`, `module.concorde.workspace`.
- **Example**: The `concorde-plan` Skill invokes the workspace Tool, reads the returned feature and
  architecture, and writes only temporal planning artifacts.

## Usage Scenarios

1. A maintainer invokes one installed leaf Skill directly and receives that bounded phase behavior.
2. The standard development Operation resolves the same leaf Skill authority, supplies accumulated
   state, and receives an equivalent phase result.
3. Checkout synchronization and installation render identical source semantics for Codex and Claude.

## Requirements

- **FR-001**: Every path-sensitive Skill MUST resolve Protocol 13 before other project artifact reads.
- **FR-002**: Each Package Manifest 2 leaf capability MUST have exactly one canonical
  `skills/<name>/SKILL.md` and one globally unique public name.
- **FR-003**: A leaf Skill MUST remain independently invocable and MUST NOT declare or implement
  LangGraph topology over multiple Skills.
- **FR-004**: Projection MUST preserve prompt semantics and add source/kind/entry-point provenance
  deterministically for Codex and Claude.
- **FR-005**: Operations MUST load canonical leaf Skill bodies; they MUST NOT embed copies of those
  bodies in Python or Markdown.

## Success Criteria

- **SC-001**: Both integrations expose exactly the 16 declared leaf Skills and every declared paired
  Operation skill with no cross-kind name collision.
- **SC-002**: Source/projection parity and installed workflow tests prove that leaf Skill semantics and
  Tool entry points are equivalent across supported integrations.

## Edge Cases

- A Skill directory name and declared `name` differ.
- A leaf Skill declares an Operation token or contains multi-Skill graph topology.
- A paired Operation uses the same public name as a leaf Skill.
- A Skill declares a Tool script that does not resolve inside the installed framework.
