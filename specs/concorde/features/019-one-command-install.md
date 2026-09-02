---
id: feature.concorde.install.one-command
kind: feature
module: module.concorde
related_features:
  - feature.concorde.install
  - feature.distribution.package-concorde
interfaces:
  provided:
    - interface.concorde.one-command-install
  required:
    - contract.concorde.installation
evidence_status: verified
---

# Feature Design: One-Command Native Install

## Outcome and Scope

A maintainer can preview or install Concorde from a source checkout or extracted standalone archive
with one Python command, without first initializing or installing another framework.

## Usage

From a Concorde checkout run `python3 scripts/install-concorde.py --target <project> --integration
codex` to preview. Add `--apply` to accept. From an extracted release, pass `--checkout concorde`.

## User Scenarios & Testing

### User Story 1 — Local Checkout Install (Priority: P1)

**Independent Test**: Run one apply command against an empty target and invoke the installed validator
launcher from `.concorde/framework/scripts/concorde.py`.

1. **Given** a checkout and empty target, **When** the one command runs with `--apply`, **Then** all
   framework/agent outputs and a receipt exist without `.specify`.

### User Story 2 — Extracted Release Install (Priority: P2)

**Independent Test**: Extract the verified archive and run its included installer with the extracted
package root.

1. **Given** a verified release archive, **When** its included installer runs, **Then** the installed
   output inventory matches a checkout installation of that version.

## Interfaces

### `interface.concorde.one-command-install` — Install a Concorde package

- **Consumer**: Project maintainer and installation automation.
- **Direction**: CLI arguments to preview or applied native installation result.
- **Entry points**: `python3 scripts/install-concorde.py` in checkout or `python3 concorde/scripts/install-concorde.py` after extraction.
- **Inputs**: `--target`, optional `--checkout`, `--integration`, preview/default or `--apply`, and output format.
- **Outputs**: Human or JSON installation plan/result plus `.concorde/install.json` after apply.
- **Obligations**: Require only Python 3.11+; preview by default; use exact package inventory/ownership semantics; preserve all unowned paths.
- **Failures**: Invalid source, target, integration, inventory, ownership, symlink, or write failure produces non-zero status and actionable diagnostics.
- **Compatibility**: Package schema 1; Profile 7; Protocol 12; Codex/Claude integrations.
- **Example**: `python3 scripts/install-concorde.py --target ../my-project --integration codex --apply`.
- **Implementing entities**: `entity.concorde.installer`, `entity.concorde.package-manifest`, `entity.concorde.commands`, `entity.concorde.runtime`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.concorde.installer` | Single entry command. | Loads package, plans ownership, and applies/rolls back. |
| `entity.concorde.package-manifest` | Package discovery contract. | Makes checkout and extracted archive equivalent inputs. |
| `entity.concorde.commands` | User-facing workflow surface. | Becomes integration-native skills during apply. |
| `entity.concorde.runtime` | Installed deterministic operations. | Is copied beside scripts under the framework projection. |

## Related Features

- `feature.concorde.install` defines lifecycle and ownership semantics.
- `feature.distribution.package-concorde` ensures release archives include the same installer/package.

## Requirements

- **FR-001**: One invocation MUST discover/validate the package and calculate the complete installation.
- **FR-002**: Preview MUST be the default and apply MUST require an explicit flag.
- **FR-003**: Checkout and extracted archive installation MUST produce equivalent desired outputs.
- **FR-004**: An empty target MUST require no prior framework initialization or network access.
- **FR-005**: JSON mode MUST return stable schema/status/action fields for automation.

## Success Criteria

- **SC-001**: One command installs every declared command for Codex and Claude targets.
- **SC-002**: A second identical apply is a zero-change `unchanged` result.

## Edge Cases

- Target exists but is not a real directory.
- Extracted archive is incomplete, modified, or points at the wrong package root.
- Python can run the installer but a target parent is a symlink or non-directory.
