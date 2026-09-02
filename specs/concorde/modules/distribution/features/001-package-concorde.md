---
id: feature.distribution.package-concorde
kind: feature
module: module.concorde.distribution
related_features:
  - feature.concorde.install
  - feature.concorde.release.publish
  - feature.skills.project-workflow
  - feature.operations.standard-development-loop
interfaces:
  provided:
    - contract.distribution.standalone-package
    - contract.distribution.native-installation
  required:
    - contract.skills.agent-surface
evidence_status: partial
---

# Feature Design: Package Standalone Concorde

## Outcome and Scope

Maintainers receive one inspectable Concorde 2.0.0 package that installs from a checkout or
reproducible archive, projects leaf and Operation skills, retains every Operation Python/Markdown
pair, updates through digest ownership, and publishes as two immutable release assets.

## Usage

Validate Package Manifest 2, preview/apply its package to a target, or build
`concorde-2.0.0.zip` and `release.json`. Extracted and checkout sources use the same installer and
desired inventory.

## Interfaces

### `contract.distribution.standalone-package` — Native package and release bytes

- **Consumer**: Installer, release tooling, and maintainer.
- **Direction**: Canonical sources to package identity, archive, and release pointer.
- **Entry points**: `concorde.json`; `agent-assets/`, `operations/`, `scripts/`, `skills/`,
  `src/`, and `templates/`; and the release builder.
- **Inputs**: Version 2.0.0, Profile 7, Protocol 13, exact 16-Skill and paired-Operation inventories,
  templates, supported integrations, and allowlisted regular files.
- **Outputs**: Source package or deterministic single-root archive plus schema-1 release pointer.
- **Obligations**: Reject missing/extra manifest inventory, symlinks, unsafe names, cross-kind
  collisions, and unpaired Operations; include native installer; normalize archive metadata; bind
  URL/digest/version.
- **Failures**: Invalid identity/inventory/member/pair/path/version/digest/rebuild prevents installation
  or release.
- **Compatibility**: Package Manifest 2 supports Architecture Profile 7, Workspace Protocol 13,
  Delivery Proposal 9, Codex, and Claude. No legacy capability layout is read.
- **Example**: `concorde-2.0.0.zip` contains `concorde/concorde.json`, 16 leaf Skill directories, and
  both files for each declared Operation.
- **Implementing entities**: `entity.distribution.manifest`,
  `entity.distribution.archive-builder`, `entity.distribution.archive`, and
  `entity.distribution.release-pointer`.

### `contract.distribution.native-installation` — Preview/apply ownership lifecycle

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Package/target/integration input to sorted plan or installed state.
- **Entry points**: `scripts/install-concorde.py` and `.concorde/install.json`.
- **Inputs**: Package root, target, integration, desired bytes, prior receipt, observed filesystem,
  and explicit apply flag.
- **Outputs**: Create/adopt/update/remove/conflict plan; framework capability/runtime/template assets,
  leaf and Operation Skill projections, internal agent assets, defaults, and receipt after apply.
- **Obligations**: Preview by default; reject unsafe/unowned paths; install exact Operation pairs;
  project their Markdown skills with framework entry points; stage replacements; restore on failure;
  write receipt last; preserve project/unrelated files.
- **Failures**: Package, ownership, collision, pairing, symlink, parent, or filesystem errors produce
  failure/conflict without false ownership.
- **Compatibility**: Receipt schema 1 keys ownership by path/role/SHA-256; unchanged receipt-owned
  obsolete outputs may be removed during the one-way 2.0.0 update, while modified outputs conflict.
- **Example**: A modified prior projected Skill is a conflict; an unchanged owned Skill updates safely.
- **Implementing entities**: `entity.distribution.installer`,
  `entity.distribution.framework-projection`, `entity.distribution.receipt`, and
  `entity.distribution.capability-projector`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.distribution.manifest` | Single Package Manifest 2 identity. | Drives source validation and desired inventory. |
| `entity.distribution.installer` | Ownership transaction. | Compares desired/prior/observed state and applies safely. |
| `entity.distribution.capability-projector` | Agent integration renderer. | Projects both leaf and Operation Markdown to the Skill namespace. |
| `entity.distribution.framework-projection` | Installed canonical package copy. | Retains Scripts, leaf Skills, Operation pairs, Runtime, templates, and support assets. |
| `entity.distribution.archive-builder` | Deterministic packager. | Emits archive and pointer from the same identity. |
| `entity.distribution.release-verifier` | Release gate. | Installs extracted bytes and proves reproducibility. |

## Related Features

- `feature.skills.project-workflow` supplies canonical leaf Skill behavior and projection rules.
- `feature.operations.standard-development-loop` supplies a paired Operation installed through the
  same Skill namespace.
- `feature.concorde.install` exposes package ownership behavior at the root workflow.
- `feature.concorde.release.publish` immutably publishes verified package bytes.

## Usage Scenarios

1. Validate and install Package Manifest 2 into a clean Codex or Claude project; observe sixteen
   leaf Skills, two Operation skills, both framework-local Python/Markdown pairs, and no legacy root.
2. Upgrade an owned 1.x installation; remove only byte-identical receipt-owned command/example
   outputs, preserve modified files as conflicts, and write the new receipt last.
3. Build and verify `concorde-2.0.0.zip`; prove its capability inventory, pair completeness, safe
   members, isolated install, pointer digest, and byte-reproducible rebuild.

## Requirements

- **FR-001**: Package Manifest 2 MUST be the sole version/profile/protocol/inventory authority.
- **FR-002**: Checkout and extracted archive MUST be valid equivalent package roots.
- **FR-003**: Every declared Operation MUST retain exactly `operation.py` and associated `SKILL.md` in
  source, archive, and installed framework, and its Markdown MUST project to the user Skill namespace.
- **FR-004**: Preview/apply MUST preserve every unowned path and reject modified owned outputs.
- **FR-005**: Release verification MUST exercise isolated installation and byte-equivalent rebuild.
- **FR-006**: No package/archive/receipt may depend on a compatibility source reader or alias.

## Success Criteria

- **SC-001**: Native install/update/idempotence/conflict/rollback suites pass for both integrations
  with all 16 leaf and two Operation skills.
- **SC-002**: Release build produces exactly one archive and one pointer with matching SHA-256 and
  reproducible bytes.
- **SC-003**: Base installation and Tool imports succeed offline without importing LangGraph.

## Edge Cases

- Package Manifest 2 capability inventory differs from regular root files.
- Archive contains a duplicate, absolute, escaping, backslash, unexpected-root, or unpaired member.
- A superseded receipt-owned output is user-modified and cannot be removed.
