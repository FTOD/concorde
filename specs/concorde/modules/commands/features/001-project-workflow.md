---
id: feature.commands.project-workflow
kind: feature
module: module.concorde.commands
related_features:
  - feature.concorde.workflow
  - feature.concorde.record-workflow-reflections
  - feature.concorde.install
  - feature.concorde.maintain-agent-surfaces
interfaces:
  provided:
    - contract.commands.workflow-guidance
    - contract.commands.agent-surface
  required:
    - contract.runtime.operations
    - contract.workspace.feature-workspace
    - contract.workspace.records
    - contract.distribution.standalone-package
evidence_status: verified
---

# Feature Design: Project the Concorde Workflow

## Outcome and Scope

Root command and template authorities become complete Codex/Claude lifecycle surfaces with identical
phase intent, native runtime paths, bounded workspace rules, and no composition framework.

## Usage

Package installation renders commands with `.concorde/framework` paths. Checkout sync renders the same
sources with root paths. Maintainers invoke the canonical command IDs normally in either integration.

## Interfaces

### `contract.commands.workflow-guidance` — Canonical lifecycle intent

- **Consumer**: Supported coding agents and maintainers.
- **Direction**: Root command/template sources to executable conversational workflow.
- **Entry points**: Every file under `commands/` and referenced file under `templates/`.
- **Inputs**: User arguments, Protocol 12 workspace, optional constitution, selected attempt, root template formats, and bounded code/tests.
- **Outputs**: Exact phase read/write/evidence/reflection behavior and completion report expectations.
- **Obligations**: Preserve authority boundaries, resolve native selection first, use complete root templates, allocate reflection IDs through the helper, and expose deterministic failures.
- **Failures**: Invalid/missing workspace, template, command metadata, interface/reference, task/evidence, or runtime check stops the phase without hidden fallback layers.
- **Compatibility**: Sixteen canonical `concorde.*` command IDs render as `concorde-*` skills while
  current content/metadata remains Concorde-owned.
- **Example**: `concorde-plan` resolves Protocol 12, reads `templates/plan-template.md`, and writes only the selected attempt.
- **Implementing entities**: `entity.commands.manifest`, `entity.commands.sources`, `entity.commands.feature-template`, `entity.commands.plan-template`, `entity.commands.tasks-template`.

### `contract.commands.agent-surface` — Rendered integration commands

- **Consumer**: Project maintainer and coding agent.
- **Direction**: Canonical commands to integration-native skill files.
- **Entry points**: `.agents/skills/<command>/SKILL.md` or `.claude/skills/<command>/SKILL.md`.
- **Inputs**: Canonical command front matter/body, integration ID, and source/installed framework prefix.
- **Outputs**: One regular Markdown skill per command with Concorde author/source metadata and resolved package tokens.
- **Obligations**: Validate command filename/front matter, preserve body semantics, resolve every script/framework token, and produce deterministic sorted outputs.
- **Failures**: Unknown metadata, unsafe script path, unsupported integration, collision, symlink, or unresolved token blocks projection.
- **Compatibility**: Codex and Claude output metadata may differ; command name/description/body behavior remains equivalent.
- **Example**: Root `commands/concorde.plan.md` renders `concorde-plan` with source or installed workspace adapter path.
- **Implementing entities**: `entity.commands.projector`, `entity.commands.sources`, `entity.commands.checkout-sync`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.commands.manifest` | Exact inventory. | Rejects missing/extra command/template sources. |
| `entity.commands.sources` | Canonical phase behavior. | Feeds the projector and agents. |
| `entity.commands.projector` | Integration renderer. | Parses metadata and resolves package tokens. |
| `entity.commands.checkout-sync` | Source repository materializer. | Renders both integrations with root paths. |
| `entity.commands.reflection-assets` | Reflection-specific orchestration. | Is projected beside lifecycle skills. |

## Related Features

- `feature.concorde.workflow` consumes the command lifecycle.
- `feature.concorde.install` projects installed paths and ownership.
- `feature.concorde.maintain-agent-surfaces` projects source-checkout paths.
- `feature.concorde.record-workflow-reflections` supplies reflection behavior/roles.

## Usage Scenarios

1. Render every root command into Codex source-checkout skills with root script/template paths.
2. Render the same commands into Claude installed skills with `.concorde/framework` paths.
3. Reject invalid command metadata, unsafe script paths, collisions, or unresolved package tokens.

## Requirements

- **FR-001**: Every path-sensitive phase MUST resolve Protocol 12 before other artifact reads.
- **FR-002**: Each root command MUST render deterministically to Codex and Claude.
- **FR-003**: Every rendered file MUST identify Concorde as author and root command as source.
- **FR-004**: Complete templates MUST require no base/priority/strategy resolution.
- **FR-005**: Installed surfaces MUST contain no unresolved token or removed host path.

## Success Criteria

- **SC-001**: Both integrations expose exactly the manifest's 16 commands.
- **SC-002**: Checkout sync and installed projection tests prove equivalent phase markers and correct path prefixes.

## Edge Cases

- A command declares a script token but no safe `scripts.py` metadata value.
- Codex and Claude metadata differ while lifecycle body semantics must remain equal.
- A generated skill path is a legacy symlink into removed host state.
