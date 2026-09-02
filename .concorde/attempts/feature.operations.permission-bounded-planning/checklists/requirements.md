# Requirements Quality Checklist: Permission-Bounded Planning Operations

**Purpose**: Confirm that the feature is complete, testable, hierarchy-preserving, and explicit
about the enforcement boundary before technical planning begins.
**Created**: 2026-09-02
**Feature**: `specs/concorde/modules/operations/features/002-permission-bounded-planning.md`

**Review Ownership**: This checklist evaluates requirements quality, not implementation completion.

## Scope and outcome

- [x] CHK001 The outcome identifies an observable consumer result for both permission enforcement and planning.
- [x] CHK002 In-scope behavior separates normalized policy, native configuration, and outer isolation.
- [x] CHK003 Out-of-scope behavior states that LangGraph and prompts do not enforce filesystem access.
- [x] CHK004 Codex and Claude are both covered without assuming identical native syntax.
- [x] CHK005 Network, credentials, destructive actions, and external writes are denied unless separately authorized.

## Hierarchy and context boundary

- [x] CHK006 The selected module's owned implementation context is distinguished from dependency-module internals.
- [x] CHK007 Complete dependency feature bodies require ownership of an explicitly required interface and carry that interface ID as the reason trace.
- [x] CHK008 Dependency architecture, source, tests, attempts, descendants, and unrelated features are explicitly excluded.
- [x] CHK009 The behavior for a change that genuinely crosses a dependency module boundary is stated.
- [x] CHK010 Related-feature summaries remain navigation rather than implicit permission grants.

## Permission enforcement

- [x] CHK011 Every Operation and composed Skill occurrence requires exact policy coverage.
- [x] CHK012 Concrete read, write, deny, network, and credential posture is present before agent launch.
- [x] CHK013 Unsafe paths, symlinks, unknown tokens, missing sandboxes, and policy widening fail closed.
- [x] CHK014 Multi-Skill stages cannot grant the union of all permissions to each Skill.
- [x] CHK015 User or managed configuration may narrow but cannot widen the Operation boundary.
- [x] CHK016 Codex named permission-profile selection and an equivalent-enforcement fallback are specified.
- [x] CHK017 Claude permission rules, strict sandbox startup, and disabled unsandboxed retry are specified.

## Plan Operation

- [x] CHK018 The public `concorde-plan` migration from leaf Skill to paired Operation is explicit.
- [x] CHK019 The Operation composes a read-only context leaf before a temporal plan-authoring leaf.
- [x] CHK020 The plan author's allowed writes are limited to the selected attempt and authorized reflection occurrence.
- [x] CHK021 Failure in context or policy resolution prevents plan authorship and downstream work.
- [x] CHK022 No compatibility alias or cross-kind name collision is permitted.

## Interfaces, evidence, and edge cases

- [x] CHK023 Both provided interfaces identify consumers, direction, entry points, inputs, outputs, obligations, failures, compatibility, examples, and implementing entities.
- [x] CHK024 Every Architecture Zoom entity resolves in the providing module architecture.
- [x] CHK025 Related-feature relationships state refinement or dependency meaning.
- [x] CHK026 Acceptance scenarios cover success plus missing, unsafe, widened, and unenforceable policies.
- [x] CHK027 Success criteria are measurable through policy coverage, two-module isolation, parity, graph ordering, and full validation tests.
- [x] CHK028 Requirements distinguish native enforcement evidence from structural configuration validation.

## Notes

- All items were reviewed against the initial feature specification on 2026-09-02.
- Checked markers establish requirements quality only; they do not assert implementation completion.
