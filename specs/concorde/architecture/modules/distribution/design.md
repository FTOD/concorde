# Design Reference: Distribution

This reference explains and justifies the Distribution module. Responsibility, boundary, and the
lifecycle contracts remain owned by `module.md` and the contract documents under `architecture/contracts/`.

## Implementation Notes

### Bundle and catalog model

A bundle is a versioned recipe, not a runtime. `concorde-bundle` names and pins the independently
versioned `concorde-core` preset and `concorde` extension that have been tested together. Bundle
inspection expands that recipe before installation; installation delegates each component to Spec
Kit's preset or extension machinery and records ownership for safe update and removal.

Catalogs are trusted indexes used to discover those three release units. Each catalog entry carries
identity, version, compatibility, download location, and integrity metadata. The URL embedded while
building a release describes where the completed catalog and archives will be served; the builder
does not need to contact that URL. Local directory, manifest, and archive bundle inputs bypass bundle
discovery, but referenced components still must resolve from permitted component catalogs or safe
installed state.

### Release building

Release archives are built from explicit allowlists with stable member ordering, permissions,
timestamps, versions, URLs, and SHA-256 digests, so repeated builds of the same sources are
byte-equivalent. A release is accepted only from built artifacts installed into checkout-isolated
projects, which prevents repository-local `.agents/` and `.specify/` content from masquerading as
distributed functionality. Releases are published from version tags.

### Contract summaries (bounded context)

The maintained definitions are `contracts/bundle-lifecycle/contract.md` and
`contracts/component-packages/contract.md`.

`contract.distribution.bundle-lifecycle`

- **Role / flow**: provided, bidirectional.
- **Counterparty**: Spec Kit and the maintainer.
- **Representation**: commonly adopted Spec Kit bundle format, version `0.16.4`.
- **Information**: exact component plan, versions, trust source, lifecycle result, and diagnostics.
- **Guarantees**: preview and install resolve the same component set; repeated installation is
  idempotent; update is explicit; removal affects only owned components.
- **Failure**: unresolved or incompatible components stop installation and are named in diagnostics.
- **Evidence**: package preview/install/update/failure/removal acceptance is verified; evidence remains
  partial until clean targets execute every installed winning command surface and preset
  recomposition restores the correct lower layer.

`contract.distribution.component-packages`

- **Role / flow**: required, input.
- **Provider**: `module.concorde.spec-kit-integration`.
- **Representation**: commonly adopted Spec Kit preset and extension manifests, version `0.16.4`.
- **Information**: component identity, version, compatibility, provided artifacts, and dependencies.
- **Guarantees**: each component is independently valid and its declared files resolve.
- **Failure**: invalid components cannot be included in a releaseable bundle.
- **Evidence**: verified by component source installation, archive, catalog, and digest tests.

## Design Rationale

- A passive recipe keeps Spec Kit as the host: the bundle contributes no executable workflow, so
  trust, compatibility, provenance, and materialization stay where Spec Kit already implements them.
- Independent versioning of preset and extension lets each evolve on its own compatibility rule while
  the bundle pin records which pair was tested together.
- Catalog integrity metadata and allowlisted, digest-bearing archives make an installation
  inspectable before anything is written and reproducible afterwards.
- Reusing the same recipe to constrain development self-hosting proves that the locally composed
  preset and extension are the pair distributed to user projects, without giving the bundle a
  second, runtime role.

## Alternatives Considered

- Turning the bundle into an executable self-hosting or installation runtime was rejected; checkout
  mutation, receipts, and freshness belong to the root self-hosting feature and installation belongs
  to Spec Kit.
- No other alternatives have been recorded for this module yet.

## Decision Log

- 2026-08-27 — Adopted the module summary / design reference split and renamed feature design.md to
  implementation.md (feature.concorde.workflow); this module's `module.md` was rewritten to the
  summary shape and the bundle/catalog model and contract narratives moved here. The same attempt
  proposes bumping `concorde-core` and `concorde` to 0.2.0 with the bundle pin following, keeping
  the catalog counts at 4 templates / 9 commands; release publication itself stays with Feature 003.
- 2026-08-27 — Concorde releases are published from version tags; v0.1.0 publication evidence
  recorded.
- 2026-08-26 — Renamed `concorde-starter` to `concorde-bundle`.
