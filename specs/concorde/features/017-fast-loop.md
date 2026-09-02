---
id: feature.concorde.workflow.fast-loop
kind: feature
module: module.concorde
related_features:
  - feature.concorde.workflow
interfaces:
  provided:
    - interface.concorde.fast-loop
  required:
    - contract.concorde.workflow
evidence_status: unknown
---

# Feature Design: Fast Loop

## Outcome and Scope

A maintainer can explicitly request one eligible, small, already-specified change and receive direct
reconciliation of affected architecture/design/code/test/projection sources without creating an attempt.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.concorde.skills` | Defines deterministic eligibility, bounded impact, evidence, and reporting rules. |
| `entity.concorde.workspace-resolver` | Resolves the anchor and each explicitly discovered affected flat feature. |
| `entity.concorde.coding-agent` | Discovers semantic impact and applies the bounded test-backed change. |

## Interfaces

### `interface.concorde.fast-loop` — Reconcile one eligible small change

- **Consumer**: Maintainer requesting a low-risk established modification.
- **Direction**: Explicit request to directly reconciled source/test result.
- **Entry points**: Leaf Skill `concorde-fast-loop`.
- **Inputs**: Selected anchor, requested change, clean worktree, complete current architecture/design/code/test context.
- **Outputs**: Exact changed sources, affected features/interfaces/entities, checks, evidence limits, or preflight rejection.
- **Obligations**: Reject structural/interface/policy ambiguity, discover all affected authorities, preserve unrelated/user state, and run proportional checks.
- **Failures**: Any ineligible condition stops before mutation and redirects to the full attempt workflow.
- **Compatibility**: Smallness is ownership/risk based, never line-count based; no accepted-realization prerequisite exists.
- **Implementing entities**: `entity.concorde.skills`, `entity.concorde.workspace-resolver`, `entity.concorde.coding-agent`.

## Usage Scenarios

1. Preflight the selected anchor, clean worktree, related-feature/entity/interface impact, and required evidence.
2. Reject any structural/public-interface/policy/ambiguous change before mutation and recommend the full lifecycle.
3. For an eligible change, edit all bounded owners, run proportional checks, and report exact sources/claims without an attempt.

## Requirements

- **FR-001**: Every affected feature MUST already have durable design, valid architecture references, current code/tests, and no active attempt.
- **FR-002**: Eligibility MUST reject module/feature creation/restructure, responsibility/ownership/dependency-direction, public interface, migration-policy, or ambiguous impact changes.
- **FR-003**: Affected architecture/design/code/test/docs/projection sources MUST be discovered and reconciled completely.
- **FR-004**: Completion MUST disclose changed sources/features/entities/interfaces, executed checks, and evidence limitations.

## Edge Cases

- A logic-preserving rename crosses many files but keeps all stable architectural semantics.
- A one-line change alters a public interface or dependency direction and is therefore not small.
