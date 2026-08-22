---
id: module.concorde.distribution
kind: module
parent: module.concorde
children: []
features:
  - feature.distribution.package-starter-bundle
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

## Feature Set

- `feature.distribution.package-starter-bundle` refines
  `feature.concorde.install-with-spec-kit` and owns bundle lifecycle behavior at this level.

## Bundle and Catalog Model

A bundle is a versioned recipe, not a runtime. `concorde-starter` names and pins the independently
versioned `concorde-core` preset and `concorde` extension that have been tested together. Bundle
inspection expands that recipe before installation; installation delegates each component to Spec
Kit's preset or extension machinery and records ownership for safe update and removal.

Catalogs are trusted indexes used to discover those three release units. Each catalog entry carries
identity, version, compatibility, download location, and integrity metadata. The URL embedded while
building a release describes where the completed catalog and archives will be served; the builder
does not need to contact that URL. Local directory, manifest, and archive bundle inputs bypass bundle
discovery, but referenced components still must resolve from permitted component catalogs or safe
installed state.

See the installation feature's
<a href="/architecture/concorde-spec-kit-component-model.html">component model</a> and
<a href="/architecture/concorde-starter-installation-flow.html">installation flow</a>. Their
maintained sources are `specs/concorde/features/003-install-concorde-speckit/spec-kit-component-model.json` and
`specs/concorde/features/003-install-concorde-speckit/starter-installation-flow.json`.

## Canonical Contract Definitions

The maintained definitions are `contracts/bundle-lifecycle/contract.md` and
`contracts/component-packages/contract.md`; the summaries below provide bounded context.

### `contract.distribution.bundle-lifecycle`

- **Role / flow**: provided, bidirectional.
- **Counterparty**: Spec Kit and the maintainer.
- **Representation**: commonly adopted Spec Kit bundle format, version `0.16.4`.
- **Information**: exact component plan, versions, trust source, lifecycle result, and diagnostics.
- **Guarantees**: preview and install resolve the same component set; repeated installation is
  idempotent; update is explicit; removal affects only owned components.
- **Failure**: unresolved or incompatible components stop installation and are named in diagnostics.
- **Evidence**: verified by clean-project preview/install/update/failure/removal acceptance.

### `contract.distribution.component-packages`

- **Role / flow**: required, input.
- **Provider**: `module.concorde.spec-kit-integration`.
- **Representation**: commonly adopted Spec Kit preset and extension manifests, version `0.16.4`.
- **Information**: component identity, version, compatibility, provided artifacts, and dependencies.
- **Guarantees**: each component is independently valid and its declared files resolve.
- **Failure**: invalid components cannot be included in a releaseable bundle.
- **Evidence**: verified by component source installation, archive, catalog, and digest tests.
