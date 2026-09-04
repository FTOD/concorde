---
id: feature.lifecycle.fast-loop
kind: feature
module: module.concorde.lifecycle
related_features:
  - id: feature.concorde.workflow
    relation: composed_by
interfaces:
  provided:
    - interface.concorde.fast-loop
  required: []
evidence_status: unknown
---

# Feature Design: Fast Loop

## Outcome and Scope

A maintainer can explicitly request one eligible, small, already-specified change and receive direct
reconciliation of affected architecture/design/code/test/projection sources without creating an attempt.

## Architecture Zoom

| Entity ID | Role |
|---|---|
| `entity.lifecycle.fast-loop-skill` | Defines deterministic eligibility, bounded impact, evidence, and reporting rules. |
| `module.concorde.understanding` | Resolves the anchor and each explicitly discovered affected flat feature. |
| `entity.concorde.coding-agent` | Discovers semantic impact and applies the bounded test-backed change. |
| `entity.concorde.specification` | Receives the directly reconciled architecture/feature text for the eligible change. |
| `entity.concorde.source-code` | Receives the directly reconciled code for the eligible change. |
| `entity.concorde.tests` | Receives the directly reconciled tests for the eligible change. |

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
- **Implementing entities**: `entity.lifecycle.fast-loop-skill`, `module.concorde.understanding`,
  `entity.concorde.coding-agent`.

## Related Features

- `feature.concorde.workflow` is the root umbrella feature this phase offers as a bounded shortcut
  around the full lifecycle for one eligible small change.

## Usage Scenarios

1. Preflight the selected anchor, clean worktree, related-feature/entity/interface impact, and required evidence.
2. Reject any structural/public-interface/policy/ambiguous change before mutation and recommend the full lifecycle.
3. For an eligible change, edit all bounded owners, run proportional checks, and report exact sources/claims without an attempt.

## Requirements

- **FR-001**: Every affected feature MUST already have durable design, valid architecture references, current code/tests, and no active attempt.
- **FR-002**: Eligibility MUST reject module/feature creation/restructure, responsibility/ownership/dependency-direction, public interface, migration-policy, or ambiguous impact changes.
- **FR-003**: Affected architecture/design/code/test/projection sources MUST be discovered and reconciled completely; no parallel custom documentation owner may be created.
- **FR-004**: Completion MUST disclose changed sources/features/entities/interfaces, executed checks, and evidence limitations.

## Edge Cases

- A logic-preserving rename crosses many files but keeps all stable architectural semantics.
- A one-line change alters a public interface or dependency direction and is therefore not small.
