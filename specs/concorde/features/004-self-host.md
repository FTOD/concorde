---
id: feature.concorde.self-host-framework
kind: feature
module: module.concorde
related_features:
  - feature.distribution.package-concorde-bundle
  - feature.concorde.install-with-spec-kit
interfaces:
  provided:
    - interface.concorde.self-host
  required:
    - contract.concorde.spec-kit-installation
evidence_status: unknown
---

# Feature Design: Self-Host the Concorde Framework

## Outcome and Scope

A Concorde maintainer can preview, atomically apply, and verify the current checkout through the same
public package/component path users receive while preserving unrelated and inactive-integration state.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.self-host` | Computes source/install digests, reviewed proposals, rollback, and freshness status. |
| `entity.concorde.preset-package` | Supplies canonical preset sources to materialization. |
| `entity.concorde.extension-package` | Supplies canonical extension/runtime/asset sources. |
| `entity.concorde.spec-kit` | Composes installed registries/templates/commands for the active integration. |

## Interfaces

### `interface.concorde.self-host` — Materialize the current checkout

- **Consumer**: Concorde framework maintainer.
- **Direction**: Checkout/integration/mode input to preview/applied/status result.
- **Entry points**: `scripts/development/self-host-concorde.py` preview, apply, status, and verify modes.
- **Inputs**: Project root, active integration, current canonical package sources, installed state, and optional current proposal.
- **Outputs**: Exact digest-bound change plan, atomic applied result/rollback, installed projection receipts, and source/installed/runtime freshness.
- **Obligations**: Use public component composition, write only owned/digest-matching paths, preserve shared/user/inactive state, and verify after apply.
- **Failures**: Conflict, registry drift, stale proposal, unsafe ownership, injected/filesystem failure, or verification mismatch rolls back the transaction.
- **Compatibility**: Profile 7 moves workflow control state and changes Protocol 12/Initialization 2 command bytes as one reviewed refresh while Delivery 8 remains stable.
- **Implementing entities**: `entity.concorde.self-host`, `entity.concorde.preset-package`, `entity.concorde.extension-package`, `entity.concorde.spec-kit`.

## Usage Scenarios

1. Preview the exact canonical-to-installed delta and inspect paths/digests before apply.
2. Apply through public component composition and agent-asset synchronization with rollback staging.
3. Report source, installed, registry, and active/inactive integration freshness without mutation.

## Requirements

- **FR-001**: Canonical preset/extension sources MUST be the only framework input; installed paths are projections.
- **FR-002**: Proposals MUST bind source, installed state, active integration, exact paths/actions, and current digests.
- **FR-003**: Apply MUST be atomic and preserve unrelated/user/shared/inactive state on success and failure.
- **FR-004**: Status MUST distinguish canonical-source, installed-byte, registry, agent-asset, and runtime-session freshness.
- **FR-005**: Profile 7 removal of specification-local control paths and Protocol 11 wording MUST be represented as owned deletion, never stale preservation.

## Edge Cases

- Installed files have user edits and therefore no longer match the ownership receipt.
- An inactive integration is materialized but unavailable to the current self-host invocation.
