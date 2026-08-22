---
id: feature.distribution.package-starter-bundle
kind: feature
module: module.concorde.distribution
refines:
  - feature.concorde.install-starter-workflow
scenarios:
  - scenario.distribution.install-bundle
contracts:
  provided:
    - contract.distribution.bundle-lifecycle
  required:
    - contract.distribution.component-packages
evidence_status: verified
canonical_spec: specs/concorde/modules/distribution/features/001-package-starter-bundle/spec.md
---

# Package the Concorde Starter Bundle

**Status**: Implemented

## Outcome

A maintainer can inspect, install, update, and remove one native Spec Kit bundle whose resolved plan
contains exactly the compatible Concorde preset and command extension, while project-owned sources
and shared components remain safe.

## Representative Scenario

`scenario.distribution.install-bundle` illustrates a maintainer previewing the bundle plan through
Spec Kit, accepting it, and receiving an installation result governed by
`contract.distribution.bundle-lifecycle`. The scenario is an example, not the feature definition.

## Requirements

- The bundle pins one preset and one extension and inherits the active integration.
- The bundle is presented as an installation recipe, while catalogs are presented as discovery and
  trust metadata rather than runtime components.
- Preview and installation resolve the same component identities and versions.
- Repeat installation is idempotent; updates are explicit; removal respects ownership.
- Failures do not record success and name residual state that could not be rolled back.
