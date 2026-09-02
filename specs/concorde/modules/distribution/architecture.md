---
id: module.concorde.distribution
kind: module
parent: module.concorde
modules: []
features:
  - feature.distribution.package-concorde
diagrams:
  - source: diagrams/system-overview.json
    kind: architecture
    output: generated/architecture/concorde-distribution-system-overview.html
---

# Architecture: Distribution

## Responsibility

Package, verify, install, update, and publish one standalone Concorde version while preserving
identity, integrity, path safety, explicit ownership, integration parity, and user-authored files.

## Boundary

Distribution owns the package manifest, allowlisted archive, release pointer, preview/apply installer,
installation receipt, release verification, and immutable publication. It does not own project
specifications/code, coding-agent behavior after projection, GitHub service internals, or unrelated
files in a target integration directory.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.distribution.manifest` | configuration | Single version/profile/protocol/inventory authority for the standalone package. | `concorde.json` |
| `entity.distribution.installer` | program | Calculates ownership actions and applies one package to a target. | `scripts/install-concorde.py` |
| `entity.distribution.command-projector` | program | Renders root commands to supported integration surfaces. | `src/concorde/command_assets.py` |
| `entity.distribution.archive-builder` | program | Builds one deterministic `concorde-<version>.zip` and `release.json`. | `scripts/release/build-release.py` |
| `entity.distribution.release-verifier` | program | Checks identity, digest, safe members, installation, and byte-equivalent rebuild. | `scripts/release/verify-release.py` |
| `entity.distribution.publisher` | program | Publishes verified immutable archive/pointer assets through a draft transaction. | `scripts/release/publish-release.py` |
| `entity.distribution.archive` | resource | Allowlisted native package with a single `concorde/` root. | `concept:concorde-<version>.zip` |
| `entity.distribution.release-pointer` | schema | Version/tag/profile/protocol plus archive URL and digest. | `concept:release.json` |
| `entity.distribution.framework-projection` | directory | Installed package bytes copied under project control. | `concept:installed-framework-projection` |
| `entity.distribution.receipt` | configuration | Output path, role, and digest ownership for one integration/version. | `concept:native-install-receipt` |
| `entity.distribution.codex-surface` | directory | Rendered command skills and reflection agents for Codex. | `.agents` |
| `entity.distribution.claude-surface` | directory | Rendered command skills and reflection agents for Claude. | `.claude` |
| `entity.distribution.github` | external-system | Immutable release asset host used by publication. | `external:github-releases` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.distribution.manifest` | `declares` | `entity.distribution.archive` | Defines the exact source inventories and version embedded in the archive. |
| `entity.distribution.archive-builder` | `reads_from` | `entity.distribution.manifest` | Uses one release identity and allowlisted root assets. |
| `entity.distribution.archive-builder` | `generates` | `entity.distribution.archive` | Produces a timestamp/mode-stable archive. |
| `entity.distribution.archive-builder` | `generates` | `entity.distribution.release-pointer` | Binds the archive URL and SHA-256 to version/protocol identity. |
| `entity.distribution.release-verifier` | `validates` | `entity.distribution.archive` | Rejects unsafe, incomplete, non-installable, or non-reproducible bytes. |
| `entity.distribution.release-verifier` | `validates` | `entity.distribution.release-pointer` | Requires pointer identity and digest agreement. |
| `entity.distribution.installer` | `reads_from` | `entity.distribution.manifest` | Validates package inventory and supported integration. |
| `entity.distribution.installer` | `generates` | `entity.distribution.framework-projection` | Copies one package into an owned target namespace. |
| `entity.distribution.installer` | `calls` | `entity.distribution.command-projector` | Renders canonical commands with installed runtime/template paths. |
| `entity.distribution.command-projector` | `generates` | `entity.distribution.codex-surface` | Produces Codex skills when selected. |
| `entity.distribution.command-projector` | `generates` | `entity.distribution.claude-surface` | Produces Claude skills when selected. |
| `entity.distribution.receipt` | `documents` | `entity.distribution.framework-projection` | Records owned bytes used for safe update/removal decisions. |
| `entity.distribution.publisher` | `depends_on` | `entity.distribution.release-verifier` | Publishes only verified local assets. |
| `entity.distribution.publisher` | `publishes` | `entity.distribution.github` | Creates or repairs a draft, uploads two assets, then publishes immutably. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.distribution.install` | Maintainer selects target, package checkout, and integration. | Validate `concorde.json`; calculate create/adopt/update/remove/conflict actions from desired/prior/observed digests; preview by default; on explicit apply reject unsafe parents, stage writes, update receipt last, and roll back failures. | Idempotent owned installation or unchanged target with exact diagnostics. | `contract.distribution.native-installation` |
| `interaction.distribution.release` | Maintainer builds a version tag. | Build one deterministic archive/pointer; verify identity, safe members, digests, isolated installation, and reproducibility; publish a draft only if tag/version agree; refuse divergent published assets. | Discoverable immutable standalone release with two mutually consistent assets. | `contract.distribution.standalone-package` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.distribution.package-concorde` | Ship one inspectable, reproducible, directly installable Concorde package with owned integration projections. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- One package manifest/version/archive replaces separately versioned and composed components.
- Installation preview is default; mutation requires `--apply`.
- Exact output digests and roles, not a third-party registry, establish ownership.
- Project-authored `.concorde` control/specification/code and unrelated agent assets are never claimed.
- Published assets are immutable; changed bytes require a new version.
