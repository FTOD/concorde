---
id: module.concorde.distribution
kind: module
parent: module.concorde
modules: []
features:
  - feature.distribution.package-concorde-bundle
diagrams: []
---

# Architecture: Distribution

## Responsibility

Package, catalog, verify, install, update, and remove a tested Concorde preset/extension pair through
Spec Kit while preserving component provenance, compatibility, integrity, and ownership.

## Boundary

Distribution owns canonical component manifests, the passive bundle recipe, catalog records,
reproducible archive construction, the one-command installer, and release verification. It does not
own workflow behavior after installation, Spec Kit's component machinery, installed user sources, or
development self-host policy.

## Entities

| Entity ID | Type | Definition | Locator |
|---|---|---|---|
| `entity.distribution.bundle` | configuration | Passive versioned recipe pinning one compatible preset and extension. | `bundles/concorde-bundle/bundle.yml` |
| `entity.distribution.bundle-catalog` | configuration | Trusted discovery index for bundle versions, locations, compatibility, and integrity. | `catalogs/bundles.json` |
| `entity.distribution.preset-catalog` | configuration | Trusted discovery index for preset archives. | `catalogs/presets.json` |
| `entity.distribution.extension-catalog` | configuration | Trusted discovery index for extension archives. | `catalogs/extensions.json` |
| `entity.distribution.installer` | program | Inspects and applies bundle/component lifecycle to a target project. | `scripts/install-concorde.py` |
| `entity.distribution.archive-builder` | program | Builds deterministic allowlisted component archives and updated catalogs. | `scripts/release/build-components.py` |
| `entity.distribution.release-verifier` | program | Installs built artifacts into isolated targets and validates declared winning surfaces. | `scripts/release/verify-release.py` |
| `entity.distribution.publisher` | program | Publishes verified artifacts/catalog updates from version tags. | `scripts/release/publish-release.py` |
| `entity.distribution.preset-source` | directory | Canonical preset package input. | `presets/concorde` |
| `entity.distribution.extension-source` | directory | Canonical extension package input. | `extensions/concorde` |
| `entity.distribution.spec-kit` | external-system | Host resolver/materializer and ownership ledger for components. | `external:specify-cli==0.16.4` |

## Relationships

| Source | Predicate | Target | Description |
|---|---|---|---|
| `entity.distribution.bundle` | `depends_on` | `entity.distribution.preset-source` | Pins the tested preset version. |
| `entity.distribution.bundle` | `depends_on` | `entity.distribution.extension-source` | Pins the tested extension version. |
| `entity.distribution.bundle-catalog` | `documents` | `entity.distribution.bundle` | Publishes trusted version/location/integrity discovery metadata. |
| `entity.distribution.archive-builder` | `reads_from` | `entity.distribution.preset-source` | Selects allowlisted canonical preset members. |
| `entity.distribution.archive-builder` | `reads_from` | `entity.distribution.extension-source` | Selects allowlisted canonical extension members. |
| `entity.distribution.archive-builder` | `writes_to` | `entity.distribution.preset-catalog` | Records the archive URL, compatibility, and digest. |
| `entity.distribution.archive-builder` | `writes_to` | `entity.distribution.extension-catalog` | Records the archive URL, compatibility, and digest. |
| `entity.distribution.release-verifier` | `calls` | `entity.distribution.installer` | Exercises artifacts in checkout-isolated targets. |
| `entity.distribution.installer` | `calls` | `entity.distribution.spec-kit` | Delegates component preview/apply/update/remove to the host. |
| `entity.distribution.publisher` | `depends_on` | `entity.distribution.release-verifier` | Publishes only verified tag-matching artifacts. |

## Interactions

| Interaction ID | Trigger | Steps | Result | Interfaces |
|---|---|---|---|---|
| `interaction.distribution.install` | Maintainer supplies bundle name/version or local input. | Resolve trusted catalog/recipe; preview exact components and ownership; Spec Kit applies accepted changes; verify installed commands/assets. | Idempotent owned installation or an unchanged target with diagnostics. | `contract.distribution.bundle-lifecycle`, `contract.distribution.component-packages` |
| `interaction.distribution.release` | Maintainer builds a version tag. | Build reproducible archives; calculate digests/catalogs; install into isolated fixtures; run surface/behavior checks; publish only matching verified results. | Discoverable release artifacts whose manifests, catalogs, bytes, and behavior agree. | `contract.distribution.component-packages` |

## Modules

None.

## Features

| Feature | Outcome |
|---|---|
| `feature.distribution.package-concorde-bundle` | Ship an inspectable, versioned, compatible preset/extension pair that Spec Kit can own safely. |

## Decisions

- A bundle is passive composition metadata, never another runtime.
- Preset and extension retain independent typed identity even though both IDs are `concorde`.
- Reproducible archives and isolated installation are required release evidence.
