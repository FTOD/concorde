---
id: feature.architecture-core.manage-bounded-sources
kind: feature
module: module.concorde.architecture-core
refines:
  - feature.concorde.install-starter-workflow
scenarios:
  - scenario.architecture-core.manage-bounded-sources
contracts:
  provided:
    - contract.core.architecture-services
  required: []
evidence_status: verified
canonical_spec: specs/concorde/modules/architecture-core/features/001-manage-bounded-sources/spec.md
---

# Manage Bounded Architecture Sources

**Status**: Implemented

## Outcome

A maintainer or coding agent can safely propose a root specification hierarchy, retrieve exactly one
architectural level, and deterministically validate maintained module, feature, contract, scenario,
and view relationships.

## Representative Scenario

`scenario.architecture-core.manage-bounded-sources` shows proposal-only initialization followed by
approved apply, bounded context retrieval, and read-only validation. It illustrates the feature but
does not replace this textual definition.

## Requirements

- Initialization separates proposal from explicit accepted apply and refuses overwrites.
- Context includes the current module and immediate children only, with concise boundary I/O.
- Validation is deterministic, complete, non-mutating, and preserves unknown evidence honestly.
