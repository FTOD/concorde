---
id: module.concorde.distribution
kind: module
parent: module.concorde
modules: []
features:
  - feature.distribution.package-concorde
  - feature.distribution.install-concorde
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-distribution-system-overview.html
---

# Architecture: Distribution

## Responsibility

Package, validate, install, and update Concorde 2.1.0 while preserving identity, capability pairing,
integrity, path safety, explicit ownership, and user-authored files.

## Boundary

Distribution owns the preview/apply installer, installation receipt, isolated installed Operation
environment, and the manifest-pinned official Understand Anything Viewer payload and launcher stored
inside that managed environment; it reads the root Package Manifest 2 as package identity and
inventory authority rather than owning that entity itself. Agent capability projection and the
Operation launcher are owned by `module.concorde.capabilities`; distribution calls that module to
render public leaf/Operation projections into the selected integration and to verify every installed
Operation before it writes the receipt. The official Viewer remains upstream-owned, and its raw UA
graph semantics remain outside Distribution. Distribution does not own project specifications/code,
the project's root `.venv`, `node_modules` or package-manager state, coding-agent behavior after
projection, Skill prompt semantics, Operation graph semantics, or Viewer UI behavior.

## Operation Contract Boundary

Distribution installs Operation definitions and projects each associated Skill into an agent CLI;
it does not create invocation state or own domain input types. Package Manifest 2 currently owns
three exact pairs, their launcher, and managed-runtime verification. The root concept's one-or-more
Python realization rule is presently satisfied by one primary `operation.py` per pair.

The target JSON invocation contract requires coordinated launcher/Skill projection and installation
tests when runtime support lands. Project Operation settings belong to the target init/config
contract, not package defaults silently repeated by installed scripts. Installation must preserve
project-authored configuration and expose any required migration explicitly. This specification
revision does not change installed payloads to an unsupported JSON ABI.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.distribution.installer` | program | Calculates ownership plus runtime actions and applies one package only after isolated Operation verification. | `scripts/install-concorde.py` |
| `entity.distribution.runtime-lock` | configuration | Exact install-time Operation dependency pin whose digest controls managed-environment reuse or rebuild. | `operations/requirements.lock` |
| `entity.distribution.runtime-provisioner` | program | Plans ownership/health, creates `.concorde/.venv`, installs the Operation lock plus manifest-pinned official Viewer payload, removes only obsolete owned runtime state, verifies every Operation and the Viewer entry point offline, and returns receipt metadata. | `src/concorde/distribution/managed_runtime.py` |
| `entity.distribution.managed-runtime` | directory | Installer-owned virtual environment containing all dependencies required for post-install offline Operation startup plus the digest-pinned official Viewer below its Concorde share directory; individual files are not framework receipt outputs. | `concept:.concorde/.venv` |
| `entity.distribution.framework-projection` | directory | Installed package bytes, including Scripts and the Viewer launcher, 17 leaf Skills, three Operation pairs, Runtime, templates, the docsite template, and support assets. | `concept:.concorde/framework` |
| `entity.distribution.receipt` | configuration | Output path/role/digest ownership plus managed-runtime path, Python and Node versions, Operation lock digest, Viewer pin/digest/entry point, launchers, and verified-Operation identity for one integration/version. | `concept:native-install-receipt` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.distribution.installer` | `reads_from` | `entity.concorde.package-manifest` | Validates exact package inventory and supported integration. |
| `entity.distribution.installer` | `generates` | `entity.distribution.framework-projection` | Copies canonical package sources, the docsite template, and every Operation pair into the owned framework. |
| `entity.concorde.package-manifest` | `declares` | `entity.distribution.runtime-lock` | Binds the one pinned Operation dependency artifact and managed environment path. |
| `entity.distribution.installer` | `calls` | `entity.distribution.runtime-provisioner` | Applies the previewed create/reuse/rebuild action before writing the receipt. |
| `entity.distribution.runtime-provisioner` | `reads_from` | `entity.distribution.runtime-lock` | Installs the exact pinned Operation dependency and combines its digest with the Package Manifest 2 Viewer pin when comparing prior runtime state. |
| `entity.distribution.runtime-provisioner` | `generates` | `entity.distribution.managed-runtime` | Creates or safely replaces only the isolated Concorde-owned environment, including the lock-verified official Viewer. |
| `entity.distribution.runtime-provisioner` | `calls` | `module.concorde.capabilities` | Verifies every installed Operation through the managed launcher offline. |
| `entity.distribution.installer` | `calls` | `module.concorde.capabilities` | Renders 18 public leaf/Operation projections through the capability projector. |
| `entity.distribution.installer` | `writes_to` | `entity.concorde.control-state` | Persists the native install receipt and `.concorde/install.json` ownership record. |
| `entity.distribution.receipt` | `documents` | `entity.distribution.framework-projection` | Records owned bytes used for safe update/removal decisions. |
| `entity.distribution.receipt` | `documents` | `entity.distribution.managed-runtime` | Records runtime identity and verification without claiming every generated environment file. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.distribution.install` | Maintainer selects target, Package Manifest 2 checkout, and integration. | Validate exact 17/3/runtime/Viewer identity; calculate file plus `.concorde/.venv` actions; preview without network; on apply install framework/projections, create or rebuild only an owned runtime, install the pinned Operation dependency and digest-verified official Viewer, verify all three Operation entry points plus the Viewer entry point offline, then update the receipt last and roll back owned files/remove partial runtime on failure. | Idempotent owned Concorde 2.1.0 installation with offline-capable Operations and official Viewer, or exact conflict/failure diagnostics. | `contract.distribution.native-installation`, `contract.capabilities.agent-surface` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.distribution.package-concorde` | Ship one inspectable, directly installable package with Tools, 17 leaves, three pairs, 18 owned public integration projections, and the pinned official Viewer lock/launcher. |
| `feature.distribution.install-concorde` | Preview or explicitly apply a checkout into a Codex or Claude project, provisioning offline Operations and the official Viewer without a host framework or project npm mutation. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Package Manifest 2 and version 2.1.0 define one no-shim capability layout.
- Package roots are exactly `agent-assets`, `docsite`, `operations`, `scripts`, `skills`, `src`,
  `templates`, and `viewer`; the `viewer` root carries only the official release npm package/lock
  and provenance, while `docsite` ships the adapter template without disposable output, `site.json`,
  or repository-specific evidence.
- Installation preview is default; mutation requires `--apply`.
- Explicit apply may contact the configured package index and the exact manifest-pinned official
  Viewer release URL; a successful installation subsequently starts all Operations and the Viewer
  from `.concorde/.venv` without dependency resolution or network access.
- The repository root `.venv` is source-development state; installed Concorde owns only
  `.concorde/.venv` and never discovers, mutates, or deletes a target-root `.venv`, `node_modules`, or
  package-manager file. Node.js 18+ and npm are validated as external prerequisites rather than
  installed.
- Every leaf and both files of every Operation pair remain installed in the framework; internal leaves
  stay unprojected while `module.concorde.capabilities` renders each public leaf/Operation Markdown as
  a user Skill through its managed Operation launcher.
- Exact output digests and roles, not a third-party registry, establish ownership.
- Project-authored `.concorde` control/specification/code and unrelated agent assets are never claimed.
