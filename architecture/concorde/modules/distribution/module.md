---
id: module.concorde.distribution
kind: module
parent: module.concorde
children: []
features: []
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

Explicitly empty during root-feature specification. Lower-level distribution features MUST be
specified before implementation begins and MUST refine `feature.concorde.install-starter-workflow`.

## Canonical Contract Definitions

### `contract.distribution.bundle-lifecycle`

- **Role / flow**: provided, bidirectional.
- **Counterparty**: Spec Kit and the maintainer.
- **Representation**: commonly adopted Spec Kit bundle format, version `0.16.4`.
- **Information**: exact component plan, versions, trust source, lifecycle result, and diagnostics.
- **Guarantees**: preview and install resolve the same component set; repeated installation is
  idempotent; update is explicit; removal affects only owned components.
- **Failure**: unresolved or incompatible components stop installation and are named in diagnostics.
- **Evidence**: unknown until clean-project lifecycle acceptance tests exist.

### `contract.distribution.component-packages`

- **Role / flow**: required, input.
- **Provider**: `module.concorde.spec-kit-integration`.
- **Representation**: commonly adopted Spec Kit preset and extension manifests, version `0.16.4`.
- **Information**: component identity, version, compatibility, provided artifacts, and dependencies.
- **Guarantees**: each component is independently valid and its declared files resolve.
- **Failure**: invalid components cannot be included in a releaseable bundle.
- **Evidence**: unknown until component manifest validation exists.
