---
id: feature.distribution.package-concorde
kind: feature
module: module.concorde.distribution
related_features:
  - feature.concorde.install
  - feature.concorde.release.publish
interfaces:
  provided:
    - contract.distribution.standalone-package
    - contract.distribution.native-installation
  required:
    - contract.commands.agent-surface
evidence_status: verified
---

# Feature Design: Package Standalone Concorde

## Outcome and Scope

Maintainers receive one inspectable package identity that can be installed from a checkout or a
reproducible archive, updated through digest ownership, and published as two immutable release assets.

## Usage

Validate `concorde.json`, preview/apply its package to a target, or build `concorde-<version>.zip` and
`release.json`. Extracted and checkout sources use the same installer and desired output inventory.

## Interfaces

### `contract.distribution.standalone-package` — Native package and release bytes

- **Consumer**: Installer, release tooling, and maintainer.
- **Direction**: Root sources to package identity, archive, and release pointer.
- **Entry points**: `concorde.json`, `commands/`, `templates/`, `src/concorde/`, `scripts/`, `agent-assets/`, and release builder.
- **Inputs**: One version/profile/protocol, exact command/template inventory, supported integrations, and allowlisted regular files.
- **Outputs**: Source package or deterministic single-root archive plus schema-1 release pointer.
- **Obligations**: Reject missing/extra manifest inventory and symlinks; include native installer; normalize archive metadata; bind URL/digest/version.
- **Failures**: Invalid identity/inventory/member/path/version/digest/rebuild prevents installation or release.
- **Compatibility**: Schema 1 supports Architecture Profile 7, Workspace Protocol 12, Codex, and Claude.
- **Example**: `concorde-1.0.0.zip` contains `concorde/concorde.json` and its included installer.
- **Implementing entities**: `entity.distribution.manifest`, `entity.distribution.archive-builder`, `entity.distribution.archive`, `entity.distribution.release-pointer`.

### `contract.distribution.native-installation` — Preview/apply ownership lifecycle

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Package/target/integration input to sorted plan or installed state.
- **Entry points**: `scripts/install-concorde.py` and `.concorde/install.json`.
- **Inputs**: Package root, target, integration, desired bytes, prior receipt, observed filesystem, and explicit apply flag.
- **Outputs**: Create/adopt/update/remove/conflict plan; framework/agent/default files and receipt after apply.
- **Obligations**: Preview by default, reject unsafe/unowned paths, stage replacements, restore on failure, write receipt last, and preserve project/unrelated files.
- **Failures**: Package, ownership, collision, symlink, parent, or filesystem errors produce failure/conflict without false ownership.
- **Compatibility**: Receipt schema 1 keys ownership by path/role/SHA-256 rather than an external registry.
- **Example**: A modified prior command skill is a conflict; an unchanged prior command updates safely.
- **Implementing entities**: `entity.distribution.installer`, `entity.distribution.framework-projection`, `entity.distribution.receipt`, `entity.distribution.command-projector`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.distribution.manifest` | Single package identity. | Drives source validation and desired inventory. |
| `entity.distribution.installer` | Ownership transaction. | Compares desired/prior/observed state and applies safely. |
| `entity.distribution.command-projector` | Agent integration renderer. | Adds Codex or Claude command/reflection outputs. |
| `entity.distribution.archive-builder` | Deterministic packager. | Emits archive and pointer from the same identity. |
| `entity.distribution.release-verifier` | Release gate. | Installs extracted bytes and proves reproducibility. |

## Related Features

- `feature.concorde.install` exposes package ownership behavior at the root workflow.
- `feature.concorde.release.publish` immutably publishes verified package bytes.

## Usage Scenarios

1. Validate and install the package directly from this checkout.
2. Build/extract the archive and produce the same installed inventory.
3. Update only unchanged receipt-owned outputs while preserving divergent and unrelated files.

## Requirements

- **FR-001**: One manifest MUST be the sole version/profile/protocol/inventory authority.
- **FR-002**: Checkout and extracted archive MUST be valid equivalent package roots.
- **FR-003**: Preview/apply MUST preserve every unowned path and reject modified owned outputs.
- **FR-004**: Release verification MUST exercise isolated installation and byte-equivalent rebuild.
- **FR-005**: No package/archive/receipt may depend on removed host component state.

## Success Criteria

- **SC-001**: Native install/update/idempotence/conflict/rollback suites pass for both integrations.
- **SC-002**: Release build produces exactly one archive and one pointer with matching SHA-256.

## Edge Cases

- Manifest command/template inventory differs from regular root files.
- Archive contains a duplicate, absolute, escaping, backslash, or unexpected-root member.
- A superseded receipt-owned output is user-modified and cannot be removed.
