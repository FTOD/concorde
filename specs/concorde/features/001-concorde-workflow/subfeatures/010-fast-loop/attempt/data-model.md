# Data Model: Relaxed Fast-Loop Eligibility

## Anchor Feature

- **Fields**: stable feature ID, canonical root, durable trio paths, providing module, attempt state.
- **Source**: first successful Feature Workspace Protocol v8 result for `--phase fast-loop`.
- **Rule**: Supplies navigation and initial bounded context; it is not evidence that no other feature
  is affected.

## Affected Feature Set

- **Fields**: ordered unique feature IDs/roots, durable trio paths/hashes, accepted-baseline state,
  attempt state, behavior impact, realization impact.
- **Discovery evidence**: relevant module summaries, contracts, code, tests, implementation
  references, and maintained/user documentation.
- **Rules**: Every root resolves canonically through the adapter; every realization is non-placeholder;
  every attempt is absent; unrelated roots are excluded; each changed authority is reconciled.

## Module Boundary Decision

- **Fields**: affected modules, responsibility changed, dependency direction changed, related
  contracts/views/references.
- **Eligible state**: responsibility changed = false and dependency direction changed = false.
- **Ineligible state**: either boundary field is true, or bounded inspection cannot decide.

## Project Compatibility Decision

- **Fields**: whole-project user promise affected, supported environment/version/format promise,
  upgrade or migration commitment, governing project-level source.
- **Eligible state**: no project-level user promise changes.
- **Ineligible state**: a promise changes or its governing project-level policy is ambiguous.
- **Exclusion**: Internal module format or contract changes do not independently set this state.

## Architecture Review State

- **Values**: `not_required`, `review_pending`, `reviewed`.
- **Transition**: `not_required` → `review_pending` when an eligible run edits a maintained architecture
  source; `review_pending` → `reviewed` only after the maintainer confirms the exact validated diff.
- **Completion rule**: A final successful report is prohibited while state is `review_pending`.

## Direct Change Set

- **Fields**: code, tests, affected feature documents, contracts, diagrams/module references, user
  docs, pre-existing unrelated paths, required checks.
- **Rules**: All edits remain bounded to the request and affected authorities; unrelated bytes are
  preserved; no `attempt/` or acceptance artifact is created by an actual fast-loop run.

## Eligibility Result

- **Values**: `eligible`, `ineligible`, `blocked`, `review_pending`, `complete`.
- **Transitions**:
  1. resolved anchor → affected-set discovery;
  2. failed baseline/boundary/project-policy/worktree/clarity gate → `ineligible` or `blocked` with zero
     edits;
  3. passing gates → `eligible` → direct edit and validation;
  4. architecture source changed → `review_pending` → `complete` after review;
  5. no architecture source changed and all checks pass → `complete`.
