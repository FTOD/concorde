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

Package, verify, install, update, and publish Concorde 2.0.0 while preserving identity, capability
pairing, integrity, path safety, explicit ownership, integration parity, and user-authored files.

## Boundary

Distribution owns Package Manifest 2, the allowlisted archive, release pointer, preview/apply
installer, installation receipt, agent capability projection, release verification, and immutable
publication. It does not own project specifications/code, coding-agent behavior after projection,
Skill prompt semantics, Operation graph semantics, GitHub internals, or unrelated target files.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.distribution.manifest` | configuration | Package Manifest 2: sole version/profile/protocol/Skill/Operation/template/root/integration authority. | `concorde.json` |
| `entity.distribution.installer` | program | Calculates ownership actions and applies one package to a target. | `scripts/install-concorde.py` |
| `entity.distribution.capability-projector` | program | Renders canonical leaf and Operation Markdown into one supported agent Skill namespace. | `src/concorde/skill_assets.py` |
| `entity.distribution.archive-builder` | program | Builds one deterministic `concorde-<version>.zip` and `release.json`. | `scripts/release/build-release.py` |
| `entity.distribution.release-verifier` | program | Checks identity, digest, safe members, capability pairs, installation, and byte-equivalent rebuild. | `scripts/release/verify-release.py` |
| `entity.distribution.publisher` | program | Publishes verified immutable archive/pointer assets through a draft transaction. | `scripts/release/publish-release.py` |
| `entity.distribution.archive` | resource | Allowlisted Package Manifest 2 content with a single `concorde/` root. | `concept:concorde-<version>.zip` |
| `entity.distribution.release-pointer` | schema | Version/tag/profile/protocol plus archive URL and digest. | `concept:release.json` |
| `entity.distribution.framework-projection` | directory | Installed package bytes, including Scripts, leaf Skills, Operation pairs, Runtime, templates, and support assets. | `concept:.concorde/framework` |
| `entity.distribution.receipt` | configuration | Output path, role, and digest ownership for one integration/version. | `concept:native-install-receipt` |
| `entity.distribution.codex-surface` | directory | Projected leaf and Operation skills plus internal reflection agents for Codex. | `.agents` |
| `entity.distribution.claude-surface` | directory | Projected leaf and Operation skills plus internal reflection agents for Claude. | `.claude` |
| `entity.distribution.github` | external-system | Immutable release asset host used by publication. | `external:github-releases` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.distribution.manifest` | `declares` | `entity.distribution.archive` | Defines exact package roots/inventories and version embedded in the archive. |
| `entity.distribution.archive-builder` | `reads_from` | `entity.distribution.manifest` | Uses one release identity and allowlisted regular root assets. |
| `entity.distribution.archive-builder` | `generates` | `entity.distribution.archive` | Produces a timestamp/mode-stable archive. |
| `entity.distribution.archive-builder` | `generates` | `entity.distribution.release-pointer` | Binds archive URL and SHA-256 to version/protocol identity. |
| `entity.distribution.release-verifier` | `validates` | `entity.distribution.archive` | Rejects unsafe, incomplete, unpaired, non-installable, or non-reproducible bytes. |
| `entity.distribution.release-verifier` | `validates` | `entity.distribution.release-pointer` | Requires pointer identity and digest agreement. |
| `entity.distribution.installer` | `reads_from` | `entity.distribution.manifest` | Validates exact package inventory and supported integration. |
| `entity.distribution.installer` | `generates` | `entity.distribution.framework-projection` | Copies canonical package sources and every Operation pair into the owned framework. |
| `entity.distribution.installer` | `calls` | `entity.distribution.capability-projector` | Renders leaf and paired Operation skills with installed entry points. |
| `entity.distribution.capability-projector` | `generates` | `entity.distribution.codex-surface` | Produces Codex Skill projections when selected. |
| `entity.distribution.capability-projector` | `generates` | `entity.distribution.claude-surface` | Produces Claude Skill projections when selected. |
| `entity.distribution.receipt` | `documents` | `entity.distribution.framework-projection` | Records owned bytes used for safe update/removal decisions. |
| `entity.distribution.publisher` | `depends_on` | `entity.distribution.release-verifier` | Publishes only verified local assets. |
| `entity.distribution.publisher` | `publishes` | `entity.distribution.github` | Creates or repairs a draft, uploads two assets, then publishes immutably. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.distribution.install` | Maintainer selects target, Package Manifest 2 checkout/archive, and integration. | Validate exact roots and global capability names; verify Operation pairs; calculate create/adopt/update/remove/conflict actions; preview; on explicit apply stage writes, project all skills, update receipt last, and roll back failures. | Idempotent owned Concorde 2.0.0 installation or exact conflict diagnostics. | `contract.distribution.native-installation`, `contract.skills.agent-surface` |
| `interaction.distribution.release` | Maintainer builds a 2.0.0 version tag. | Build archive/pointer; verify identity, safe members, pairs, digests, isolated installation, and reproducibility; publish a draft only if tag/version agree; refuse divergent published assets. | Discoverable immutable standalone release with two mutually consistent assets. | `contract.distribution.standalone-package` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.distribution.package-concorde` | Ship one inspectable, reproducible, directly installable package with Tools, 16 leaf Skills, paired Operations, and owned integration projections. |

## Decisions

- [System overview](diagrams/system-overview.json) is the required Archify projection of the principal
  entities and directed relationships in this architecture.
- Package Manifest 2 and version 2.0.0 define one no-shim capability layout.
- Package roots are exactly `agent-assets`, `operations`, `scripts`, `skills`, `src`, and `templates`.
- Installation preview is default; mutation requires `--apply`.
- Both files of every Operation pair remain installed in the framework while its Markdown is also
  projected as a user Skill.
- Exact output digests and roles, not a third-party registry, establish ownership.
- Project-authored `.concorde` control/specification/code and unrelated agent assets are never claimed.
- Published assets are immutable; changed bytes require a new version.
