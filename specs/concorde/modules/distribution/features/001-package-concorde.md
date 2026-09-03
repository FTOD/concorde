---
id: feature.distribution.package-concorde
kind: feature
module: module.concorde.distribution
related_features:
  - feature.concorde.install
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

Maintainers receive one inspectable Concorde 2.1.0 package that installs from a checkout, packages
17 leaves/three pairs, projects 15 public leaves plus three Operations, retains every Operation
Python/Markdown pair, provisions their pinned dependency into an isolated `.concorde/.venv`, and
updates through digest plus managed-runtime ownership without touching a project's `.venv`.

## Usage

Validate Package Manifest 2, then preview/apply its package to a target. Any checkout that contains
`concorde.json` and its declared package roots is a valid source for the same installer and desired
inventory.

## Interfaces

### `contract.distribution.standalone-package` — Native package bytes

- **Consumer**: Installer and maintainer.
- **Direction**: Canonical sources to package identity and desired inventory.
- **Entry points**: `concorde.json`; `agent-assets/`, `docsite/`, `operations/`, `scripts/`,
  `skills/`, `src/`, and `templates/`; `operations/requirements.lock`; and
  `scripts/run-operation.py`.
- **Inputs**: Version 2.1.0, Profile 7, Protocol 13, exact 17-Skill/three-Operation inventories,
  managed-runtime declaration and dependency pin, templates, supported integrations, and allowlisted
  regular files.
- **Outputs**: One validated source package root with a desired file inventory and one deterministic
  installed-runtime identity.
- **Obligations**: Reject missing/extra manifest inventory, symlinks, unsafe names, cross-kind
  collisions, unpaired Operations, and missing/invalid runtime artifacts; include the native
  installer and standard-library Operation bootstrap; include the docsite template without
  disposable output, `site.json`, or repository evidence.
- **Failures**: Invalid identity/inventory/pair/path/version prevents installation.
- **Compatibility**: Package Manifest 2 supports Architecture Profile 7, Workspace Protocol 13,
  Delivery Proposal 9, Codex, and Claude. No legacy capability layout is read.
- **Example**: A checkout contains `concorde.json`, 17 leaf directories (including two internal
  planner leaves), both files for each of three Operations, the pinned runtime requirement and
  bootstrap, and the `docsite/` template.
- **Implementing entities**: `entity.distribution.manifest` and `entity.distribution.installer`.

### `contract.distribution.native-installation` — Preview/apply ownership lifecycle

- **Consumer**: Project maintainer and installation automation.
- **Direction**: Package/target/integration input to sorted plan or installed state.
- **Entry points**: `scripts/install-concorde.py` and `.concorde/install.json`.
- **Inputs**: Package root, target, integration, desired bytes, runtime lock/health, prior receipt,
  observed filesystem, and explicit apply flag.
- **Outputs**: Create/adopt/update/remove/conflict plan; framework capability/runtime/template assets,
  runtime create/unchanged/rebuild/conflict action; isolated `.concorde/.venv`; leaf and Operation
  Skill projections; internal agent assets; defaults; and file/runtime receipt after apply.
- **Obligations**: Preview by default; reject unsafe/unowned paths; install exact Operation pairs;
  project their Markdown skills through the managed launcher; allow dependency download only during
  apply; remove only an obsolete owned runtime; verify all Operations offline; stage replacements;
  restore owned files/remove a partial runtime on failure; write receipt last; preserve project,
  root `.venv`, and unrelated files.
- **Failures**: Package, ownership, collision, pairing, symlink, parent, dependency provisioning,
  runtime verification, or filesystem errors produce failure/conflict without false ownership.
- **Compatibility**: Receipt schema 1 keys ownership by path/role/SHA-256; unchanged receipt-owned
  obsolete outputs may be removed during the one-way 2.1.0 update, while modified outputs conflict.
- **Example**: A modified prior projected Skill is a conflict; an unchanged owned Skill updates safely.
- **Implementing entities**: `entity.distribution.installer`,
  `entity.distribution.runtime-provisioner`, `entity.distribution.operation-launcher`,
  `entity.distribution.managed-runtime`, `entity.distribution.framework-projection`,
  `entity.distribution.receipt`, and `entity.distribution.capability-projector`.

## Architecture Zoom

| Entity ID | Role in this feature | Interaction |
|---|---|---|
| `entity.distribution.manifest` | Single Package Manifest 2 identity. | Drives source validation and desired inventory. |
| `entity.distribution.installer` | Ownership transaction. | Compares desired/prior/observed state and applies safely. |
| `entity.distribution.runtime-lock` | Pinned Operation dependency. | Supplies the reuse/rebuild digest and install input. |
| `entity.distribution.runtime-provisioner` | Isolated environment lifecycle. | Creates, health-checks, safely rebuilds, and verifies the managed venv. |
| `entity.distribution.operation-launcher` | Deterministic interpreter handoff. | Selects the source or installed managed interpreter without activation. |
| `entity.distribution.managed-runtime` | Installed Operation environment. | Retains dependencies required for offline startup separately from user environments. |
| `entity.distribution.capability-projector` | Agent integration renderer. | Filters internal leaves and preserves public Skill/Operation role transitions. |
| `entity.distribution.framework-projection` | Installed canonical package copy. | Retains Scripts, all 17 leaves, three pairs, Runtime, templates, the docsite template, and support assets. |

## Related Features

- `feature.skills.project-workflow` supplies canonical leaf Skill behavior and projection rules.
- `feature.operations.standard-development-loop` supplies a paired Operation installed through the
  same Skill namespace.
- `feature.concorde.install` exposes package ownership behavior at the root workflow.

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

## Success Criteria

- **SC-001**: Native install/update/idempotence/conflict/rollback suites pass for both integrations
  with 17 packaged leaves, three pairs, and exactly 18 public projected skills.
- **SC-003**: Preview and base Tool imports remain offline/lazy; explicit apply may download the
  pinned dependency, after which all three projected Operations start offline from
  `.concorde/.venv` for both integrations.

## Edge Cases

- Package Manifest 2 capability inventory differs from regular root files.
- A package root contains a symlink, an unsafe name, or an unpaired Operation member.
- A superseded receipt-owned output is user-modified and cannot be removed.
- `.concorde/.venv` is unowned, symlinked, stale, corrupt, or only partially provisioned.
- A project already has its own root `.venv`; installation preserves it byte-for-byte.
