---
id: feature.concorde.install
kind: feature
module: module.concorde
related_features:
  - feature.concorde.release.publish
  - feature.concorde.install.one-command
  - feature.distribution.package-concorde
interfaces:
  provided:
    - contract.concorde.installation
  required:
    - contract.concorde.agent-platform
evidence_status: verified
---

# Feature Design: Install Concorde Natively

## Outcome and Scope

A maintainer can preview and explicitly apply one standalone Concorde package to a clean or existing
project. Concorde owns only its framework projection and generated integration files; it preserves
project-authored control/specification/code and unrelated agent assets.

## Usage

Run the installer with target, checkout, and integration to inspect exact file actions. Re-run with
`--apply` only after accepting that plan. Repeating the same apply returns `unchanged`; a new package
version updates only receipt-owned unchanged outputs.

## User Scenarios & Testing

### User Story 1 — Inspect Before Mutation (Priority: P1)

**Independent Test**: Preview against an empty target and prove no file is written while every desired
framework, command, agent, and default path appears in the plan.

1. **Given** a clean target, **When** installation runs without `--apply`, **Then** status is `preview`
   and the target remains empty.
2. **Given** an existing divergent target path, **When** preview runs, **Then** status is `conflict`
   and no path changes.

### User Story 2 — Apply and Update Owned Files (Priority: P2)

**Independent Test**: Apply twice, then apply a changed package and verify installed/unchanged/update
outcomes plus preservation of unrelated files.

1. **Given** an accepted conflict-free plan, **When** `--apply` runs, **Then** one framework projection,
   selected integration surface, reflection assets/defaults, and ownership receipt are written.

## Interfaces

### `contract.concorde.installation` — Standalone Concorde installation

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Package request to preview plan or applied installation result.
- **Entry points**: `scripts/install-concorde.py` with `--target`, `--checkout`, `--integration`, and optional `--apply`.
- **Inputs**: Real target directory, package root containing `concorde.json`, Codex/Claude choice, and preview/apply mode.
- **Outputs**: Status, version, integration, receipt path, and sorted create/adopt/update/remove/conflict actions with role/digest.
- **Obligations**: Preview by default; validate manifest/inventory; reject symlink/ownership collisions; update only prior matching digests; write receipt last; restore prior bytes on apply failure.
- **Failures**: Invalid package, unsupported integration/profile, unsafe path, modified owned output, unrelated collision, or filesystem failure returns diagnostics without claiming success.
- **Compatibility**: Package Profile 7/Protocol 12 must match runtime; `speckit-*` names are rendered as Concorde-owned commands.
- **Example**: `python3 scripts/install-concorde.py --target ../app --integration codex --apply`.
- **Implementing entities**: `module.concorde.distribution`, `entity.concorde.installer`, `entity.concorde.package-manifest`, `entity.concorde.commands`, `entity.concorde.agent-assets`.

### `contract.concorde.agent-platform` — Supported project integration surface

- **Provider**: `external:coding-agent-platform`.
- **Consumer**: Concorde installer, rendered commands, and project maintainer.
- **Direction**: Canonical agent assets to a supported coding-agent project layout.
- **Entry points**: `.agents/skills/**` plus `.codex/agents/**` for Codex; `.claude/skills/**` plus `.claude/agents/**` for Claude.
- **Inputs**: Canonical command Markdown, reflection templates/roles, package-relative runtime/template prefix, and integration ID.
- **Outputs**: Regular project files with Concorde metadata and no external composer or registry.
- **Obligations**: Preserve command semantics across integrations; never follow target symlinks or overwrite unowned divergent files.
- **Failures**: Unsupported integration, invalid source front matter/template, output collision, or unsafe target path blocks projection.
- **Compatibility**: Codex and Claude are the complete supported set for package schema 1.
- **Example**: `speckit-plan` in both agents invokes the installed `.concorde/framework/scripts/workspace.py`.
- **Implementing entities**: `entity.concorde.installer`, `entity.concorde.commands`, `entity.concorde.coding-agent`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `module.concorde.distribution` | Owns package/install/release semantics. | Supplies the verified package contract. |
| `entity.concorde.package-manifest` | Defines identity and exact inventories. | Gates every desired output calculation. |
| `entity.concorde.installer` | Plans and applies ownership changes. | Compares desired, prior receipt, and observed bytes. |
| `entity.concorde.commands` | Supplies canonical command intent. | Is rendered directly for the selected integration. |
| `entity.concorde.agent-assets` | Supplies reflection roles and templates. | Is projected beside lifecycle commands. |

## Related Features

- `feature.distribution.package-concorde` supplies verified package bytes.
- `feature.concorde.install.one-command` exposes the normal invocation.
- `feature.concorde.release.publish` publishes the same installable package immutably.

## Requirements

- **FR-001**: One manifest/version MUST inventory every command/template and supported integration.
- **FR-002**: Preview MUST be non-mutating and MUST report exact action/path/role/digest state.
- **FR-003**: Apply MUST reject all conflicts and unsafe parents before writing owned outputs.
- **FR-004**: Update/removal MUST require the observed bytes to match the prior receipt digest.
- **FR-005**: Failed apply MUST restore updated/removed bytes and the prior receipt.
- **FR-006**: Repeating an identical accepted installation MUST return `unchanged`.

## Success Criteria

- **SC-001**: Clean Codex and Claude targets install and expose all 16 commands with no `.specify` path.
- **SC-002**: Conflict, idempotence, integration-change, rollback, and preservation tests pass.

## Edge Cases

- A desired path is a symlink, directory, or divergent unowned file.
- The prior receipt owns a file that was modified or deleted between preview and apply.
- Integration changes while prior generated outputs remain owned or user-modified.
