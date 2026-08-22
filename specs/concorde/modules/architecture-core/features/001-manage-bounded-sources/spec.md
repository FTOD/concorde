---
id: feature.architecture-core.manage-bounded-sources
kind: feature
module: module.concorde.architecture-core
refines:
  - feature.concorde.core-workflow
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
architectural level for feature placement or implementation, and deterministically validate
maintained module, feature, contract, scenario, evidence, and view relationships.

## Representative Scenario

`scenario.architecture-core.manage-bounded-sources` shows proposal-only initialization followed by
approved apply, bounded context retrieval, and read-only validation. It illustrates the feature but
does not replace this textual definition.

## Diagram Decision

The parent feature's `diagrams/core-workflow-components.json` core architecture view shows Architecture
Core's responsibility and its interactions with the agent, workspace, Integration, and evidence
producers. A separate child diagram would repeat those same component boundaries; this specification
relies on that text-backed parent view plus the Architecture Core module contract.

## Requirements

- Initialization separates proposal from explicit accepted apply and refuses overwrites.
- Context includes the current module and immediate children only, with concise boundary I/O.
- Validation is deterministic, complete, non-mutating, and preserves unknown evidence honestly.
