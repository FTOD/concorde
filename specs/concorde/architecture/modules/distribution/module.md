---
id: module.concorde.distribution
kind: module
parent: module.concorde
children: []
features:
  - feature.distribution.package-concorde-bundle
contracts:
  provided:
    - contract.distribution.bundle-lifecycle
  required:
    - contract.distribution.component-packages
---

# Distribution

## Responsibility

Package the compatible Concorde components into a transparent, versioned, installable stack and
manage their preview, installation, update, and removal lifecycle.

## Boundary

Distribution owns bundle composition, version pins, release metadata, lifecycle outcomes, and
component provenance. It does not own preset content, agent command behavior, architecture semantics,
or user-authored architecture sources.

## Structure

This leaf module has no submodules, so it keeps no level view of its own under
`architecture/diagrams/`; its structure is the `concorde-bundle` recipe, the two lifecycle contracts
(under `architecture/contracts/`) inventoried below, and the release archives and catalogs it
produces. See the installation feature's
<a href="/architecture/concorde-spec-kit-component-model.html">component model</a> and
<a href="/architecture/concorde-bundle-installation-flow.html">installation flow</a>. Their
maintained sources are
`specs/concorde/features/003-install-concorde-speckit/diagrams/spec-kit-component-model.json` and
`specs/concorde/features/003-install-concorde-speckit/diagrams/bundle-installation-flow.json`.

## Features

| Feature ID | Outcome | Refines | Specification |
|---|---|---|---|
| `feature.distribution.package-concorde-bundle` | A maintainer can inspect, install, update, and remove one native Spec Kit bundle whose resolved plan contains exactly the compatible Concorde preset and command extension, while project-owned sources and shared components remain safe; the same versioned recipe constrains development self-hosting without becoming a self-hosting runtime. | `feature.concorde.install-with-spec-kit`, `feature.concorde.self-host-framework` (the root self-hosting feature owns checkout mutation and freshness) | [design.md](features/001-package-concorde-bundle/design.md) |

## Contracts

| Contract ID | Role | Flow | Counterparty | Definition |
|---|---|---|---|---|
| `contract.distribution.bundle-lifecycle` | provided | bidirectional | Spec Kit and the maintainer | [contract.md](architecture/contracts/bundle-lifecycle/contract.md) |
| `contract.distribution.component-packages` | required | input | `module.concorde.skills` | [contract.md](architecture/contracts/component-packages/contract.md) |

## Submodules

None.

## Representative Scenario

`scenario.distribution.install-bundle` shows a maintainer asking Spec Kit to preview `concorde-bundle`.
Distribution expands the versioned recipe into its exact component plan, the pinned `concorde`
preset and `concorde` extension resolved from permitted component catalogs and supplied by Skills
across `contract.distribution.component-packages`, and reports versions, trust source,
and diagnostics across `contract.distribution.bundle-lifecycle`. After the maintainer accepts,
installation delegates each component to Spec Kit's preset or extension machinery and records
ownership so later update and removal touch only owned components. Unresolved or incompatible
components stop the installation and are named in the diagnostics.

## Design Rationale

A bundle is a versioned recipe, not a runtime: pinning independently versioned components that were
tested together gives one inspectable installation unit while Spec Kit keeps ownership of resolution,
provenance, and materialization. Catalogs are trusted indexes rather than installed components, so
trust and integrity metadata travel with the archives and local inputs still resolve through them.
The bundle and catalog model and the contract narratives are in the [design reference](design.md).
