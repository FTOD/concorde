---
id: feature.distribution.package-concorde
kind: feature
module: module.concorde.distribution
related_features:
  - id: feature.distribution.install-concorde
    relation: depended_on_by
  - id: feature.capabilities.provide-capability-surfaces
    relation: depends_on
  - id: feature.lifecycle.standard-development-loop
    relation: relates_to
interfaces:
  provided:
    - contract.distribution.standalone-package
    - contract.distribution.native-installation
  required:
    - contract.capabilities.agent-surface
---

# Feature Design: Package Standalone Concorde

## Outcome and Scope

Maintainers receive one inspectable Concorde 3.0.0 package that installs from a checkout, packages
17 leaves/three pairs, projects 15 public leaves plus three Operations, retains every Operation
Python/Markdown pair, provisions their pinned dependency into an isolated `.concorde/.venv`, and
ships a lifecycle-script-disabled npm lock for the official Understand Anything Viewer v2.9.0, and
updates through digest plus managed-runtime ownership without touching a project's `.venv` or npm
state.

## Usage

Validate Package Manifest 2, then preview/apply its package to a target. Any checkout that contains
`concorde.json` and its declared package roots is a valid source for the same installer and desired
inventory.

## Interfaces

### `contract.distribution.standalone-package` — Native package bytes

- **Consumer**: Installer and maintainer.
- **Direction**: Canonical sources to package identity and desired inventory.
- **Entry points**: `concorde.json`; `agent-assets/`, `docsite/`, `operations/`, `scripts/`,
  `skills/`, `src/`, `templates/`, and `viewer/`; `operations/requirements.lock`;
  `viewer/package.json`; `viewer/package-lock.json`; `scripts/run-operation.py`; and
  `scripts/run-viewer.py`.
- **Inputs**: Version 3.0.0, Profile 7, Protocol 13, exact 17-Skill/three-Operation inventories,
  managed-runtime declaration and Operation dependency pin, official Viewer identity/release
  metadata and npm integrity lock, templates, supported integrations, and allowlisted regular files.
- **Outputs**: One validated source package root with a desired file inventory and one deterministic
  installed-runtime identity.
- **Obligations**: Reject missing/extra manifest inventory, symlinks, unsafe names, cross-kind
  collisions, unpaired Operations, and missing/invalid runtime artifacts; include the native
  installer, standard-library Operation bootstrap, Viewer launcher, and exact official Viewer npm
  lock; include the docsite template without
  disposable output, `site.json`, or repository evidence.
- **Failures**: Invalid identity/inventory/pair/path/version prevents installation.
- **Compatibility**: Package Manifest 2 supports Architecture Profile 7, Workspace Protocol 13,
  Delivery Proposal 9, Codex, and Claude. No legacy capability layout is read.
- **Example**: A checkout contains `concorde.json`, 17 leaf directories (including two internal
  planner leaves), both files for each of three Operations, the pinned runtime requirement and
  bootstrap, the pinned official Viewer npm lock and launcher, and the `docsite/` template.
- **Implementing entities**: `entity.concorde.package-manifest` and `entity.distribution.installer`.

### `contract.distribution.native-installation` — Preview/apply ownership lifecycle

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Package/target/integration input to sorted plan or installed state.
- **Entry points**: `scripts/install-concorde.py` and `.concorde/install.json`.
- **Inputs**: Package root, target, integration, desired bytes, runtime lock/health, prior receipt,
  Viewer lock/health, observed filesystem, and explicit apply flag.
- **Outputs**: Create/adopt/update/remove/conflict plan; framework capability/runtime/template assets,
  runtime create/unchanged/rebuild/conflict action; isolated `.concorde/.venv`; leaf and Operation
  Skill projections; installed official Viewer; internal agent assets; defaults; and file/runtime
  receipt after apply.
- **Obligations**: Preview by default; reject unsafe/unowned paths; install exact Operation pairs;
  project their Markdown skills through the managed launcher; allow dependency download only during
  apply; run Viewer `npm ci` with lifecycle scripts disabled inside the managed runtime only; remove
  only an obsolete owned runtime; verify all Operations and the Viewer entry point offline; stage
  replacements; restore owned files/remove a partial runtime on failure; write receipt last;
  preserve project, root `.venv`, project npm state, and unrelated files.
- **Failures**: Package, ownership, collision, pairing, symlink, parent, dependency provisioning,
  runtime verification, or filesystem errors produce failure/conflict without false ownership.
- **Compatibility**: Receipt schema 1 keys ownership by path/role/SHA-256; unchanged receipt-owned
  obsolete outputs may be removed during the one-way 3.0.0 update, while modified outputs conflict.
- **Example**: A modified prior projected Skill is a conflict; an unchanged owned Skill updates safely.
- **Implementing entities**: `entity.distribution.installer`,
  `entity.distribution.runtime-provisioner`, `entity.distribution.managed-runtime`,
  `entity.distribution.framework-projection`, `entity.distribution.receipt`, and
  `module.concorde.capabilities`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.concorde.package-manifest` | Single Package Manifest 2 identity. | Drives source validation and desired inventory. |
| `entity.distribution.installer` | Ownership transaction. | Compares desired/prior/observed state and applies safely. |
| `entity.distribution.runtime-lock` | Pinned Operation dependency. | Supplies the reuse/rebuild digest and install input. |
| `entity.distribution.runtime-provisioner` | Isolated environment lifecycle. | Creates, health-checks, safely rebuilds, and verifies the managed venv. |
| `module.concorde.capabilities` | Agent projection and Operation launch. | Renders public leaf/Operation surfaces and verifies every installed Operation through the managed launcher. |
| `entity.distribution.managed-runtime` | Installed Operation and Viewer environment. | Retains dependencies required for offline startup separately from user Python and npm environments. |
| `entity.distribution.framework-projection` | Installed canonical package copy. | Retains Scripts, all 17 leaves, three pairs, Runtime, Viewer lock/launcher, templates, the docsite template, and support assets. |

## Related Features

- `feature.distribution.install-concorde` depends on this feature for validated Package Manifest 2
  bytes and packaged inventory; installation previews and applies them but does not redefine them.
- `feature.capabilities.provide-capability-surfaces` supplies the capability projector and Operation
  launcher that render this package's public leaves/Operations into an agent surface during install.
- `feature.lifecycle.standard-development-loop` supplies the paired Operation whose Python/Markdown
  files this feature packages and installs through the same capability namespace.

## Usage Scenarios

1. Validate and install Package Manifest 2 into a clean Codex or Claude project; observe 15 public
   leaf Skills, three Operation skills, two framework-only planner leaves, all three pairs, one
   verified `.concorde/.venv`, and no legacy root.
2. Upgrade an owned 1.x installation; remove only byte-identical receipt-owned command/example
   outputs, preserve modified files as conflicts, and write the new receipt last.

## Requirements

- **FR-001**: Package Manifest 2 MUST be the sole version/profile/protocol/inventory authority.
- **FR-002**: Any checkout containing Package Manifest 2 and its declared roots MUST be a valid
  package root.
- **FR-003**: Every declared Operation MUST retain exactly `operation.py` and associated `SKILL.md` in
  source and installed framework, and its Markdown MUST project to the user Skill namespace.
- **FR-007**: Every internal leaf MUST remain packaged/loadable but absent from public projections;
  the stable `concorde-plan` target MUST transition from owned Skill role to owned Operation role
  without overwriting unowned or modified bytes.
- **FR-004**: Preview/apply MUST preserve every unowned path and reject modified owned outputs.
- **FR-006**: No package/receipt may depend on a compatibility source reader or alias.
- **FR-008**: Package Manifest 2 MUST bind the managed venv, pinned requirements, Python
  compatibility, and bootstrap paths, and installation MUST reject missing or divergent artifacts.
- **FR-009**: Explicit apply MUST provision and verify `.concorde/.venv` before writing the receipt;
  preview and post-install Operation startup MUST NOT require package-index access.
- **FR-010**: Runtime reuse/rebuild MUST be driven by receipt/marker ownership, lock digest, and
  health; a target-root `.venv` MUST remain outside every install action.
- **FR-011**: Package Manifest 2 MUST bind the official Viewer provider/version/asset integrity,
  Node engine, npm package/lock, installed entry point, launcher, and conventional raw graph paths;
  installation MUST reject any missing or divergent Viewer artifact.

## Success Criteria

- **SC-001**: Native install/update/idempotence/conflict/rollback suites pass for both integrations
  with 17 packaged leaves, three pairs, and exactly 18 public projected skills.
- **SC-003**: Preview and base Tool imports remain offline/lazy; explicit apply may download the
  pinned Operation and Viewer dependencies, after which all three projected Operations and the
  official Viewer start offline from `.concorde/.venv` for both integrations.

## Edge Cases

- Package Manifest 2 capability inventory differs from regular root files.
- A package root contains a symlink, an unsafe name, or an unpaired Operation member.
- A superseded receipt-owned output is user-modified and cannot be removed.
- `.concorde/.venv` is unowned, symlinked, stale, corrupt, or only partially provisioned.
- A project already has its own root `.venv`; installation preserves it byte-for-byte.
- The official Viewer lock, integrity, Node engine, entry point, or dashboard bytes are missing or
  inconsistent; package validation fails before installation.
