---
id: feature.concorde.workflow.validate-architecture
kind: feature
module: module.concorde
parent_feature: feature.concorde.workflow
refines: []
subfeatures: []
scenarios:
  - scenario-concorde-review-implement-and-reconcile
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
architecture_view: specs/concorde/architecture.json
evidence_status: partial
canonical_spec: specs/concorde/features/001-concorde-workflow/subfeatures/008-validate-architecture/spec.md
---

# Feature Specification: Validate Architecture

**Created**: 2026-08-26
**Revised**: 2026-08-27
**Status**: Specified and revised for the parent's document model; existing realization has not been
hardened into this sub-feature's `implementation.md`
**Input**: Deterministically validate Concorde maintained sources through `speckit.concorde.validate`,
including the summary shape, reading budget, reference presence, and feature-root pairing rules.

## Outcome

A maintainer receives a repeatable, complete, actionable account of structural validity, document-model
compliance, and known evidence agreement without validation rewriting the sources it evaluates.

## Parent Context and Boundary

The parent owns which invariants connect the workflow and defines the document model and reading
budget. This child owns deterministic discovery, rule evaluation, target scoping, findings, status,
and evidence classification. It does not judge whether prose is elegant or whether an application
behaves correctly. The parent diagram and bounded architecture view are sufficient; no child diagram
is needed.

## User Scenarios & Testing

### User Story 1 - Validate maintained intent (Priority: P1)

A maintainer validates the whole project or one supported target after structural changes and receives
sorted findings with rule, severity, source, explanation, and remediation.

**Independent Test**: Run validation repeatedly across valid and seeded-invalid hierarchy, contract,
scenario, refinement, containment, layout, diagram, selection, evidence, and document-model fixtures.

**Acceptance Scenarios**:
1. **Given** valid unchanged sources, **When** validation is repeated, **Then** status, digest, summary,
   and ordered findings are equivalent.
2. **Given** seeded structural faults, **When** validation runs, **Then** every applicable fault is
   reported without hiding later findings.
3. **Given** a module summary over the reading budget or missing its structure diagram or an
   inventory table, a module without `design.md` or with one unreachable from its summary, or a
   feature root with a legacy `design.md`, **When** validation runs, **Then** each is reported with a
   stable rule ID and a concrete remediation.
4. **Given** missing or conflicting implementation evidence, **When** validation assesses freshness,
   **Then** it reports unknown or disagreement rather than agreement.

### Edge Cases

- Malformed metadata prevents normal source indexing.
- A path looks feature-like but is at an illegal depth or crosses a symlink.
- A leaf module omits a structure diagram without recording a rationale.
- A feature root holds both `design.md` and `implementation.md`, or neither.
- A scoped target is unknown or ambiguous.

## Requirements

- **FR-001**: Validation MUST be read-only, deterministic, and repeatable for unchanged inputs.
- **FR-002**: Findings MUST include stable rule ID, severity, location, explanation, and actionable
  remediation.
- **FR-003**: Validation MUST cover identities, paths, module hierarchy, contracts, scenarios, views,
  refinements, feature containment, diagrams, selection safety, evidence references, module summary
  shape and reading budget, module design-reference presence and reachability, feature-root document
  pairing, and legacy document names.
- **FR-004**: Containment and refinement MUST be validated as distinct acyclic relationships.
- **FR-005**: Illegal third-level, alternate-depth, dangling, duplicate, cyclic, symlinked, or
  mismatched feature roots MUST be actionable findings.
- **FR-006**: Validation MUST preserve complete sorted findings and stable success, invalid, conflict,
  and failed statuses.
- **FR-007**: Unknown evidence MUST NOT be promoted to agreement.
- **FR-008**: Validation MUST check every `module.md` for the parent's summary shape (required
  sections, a structure diagram or recorded leaf rationale, and feature, contract, and submodule
  inventory tables) and for the reading budget, and MUST check every module for a `design.md`
  reachable from its summary.
- **FR-009**: Validation MUST report a `design.md` at a feature root as a legacy artifact with a
  rename remediation, a root holding both `design.md` and `implementation.md` as ambiguous, and a
  root without `implementation.md` as missing its accepted realization.
- **FR-010**: Reading-budget findings MUST use the deterministic proxy the parent records and MUST
  NOT judge prose quality.

## Success Criteria

- **SC-001**: Repeated unchanged validation outputs are byte-equivalent in all deterministic fixtures.
- **SC-002**: Every seeded structural rule violation is detected with its expected stable rule ID.
- **SC-003**: Validation produces zero source changes in every success and failure fixture.
- **SC-004**: All valid two-level feature fixtures pass containment validation with zero findings.
- **SC-005**: Every seeded document-model violation (over-budget summary, missing diagram or table,
  missing or unreachable reference, legacy or duplicated feature-root name) is detected with its
  expected rule ID, and every compliant fixture passes with zero document-model findings.

## Assumptions

- Semantic simplicity and non-duplication of prose remain requirements-review judgments.
- The reading-budget proxy is the one recorded in the parent's assumptions; changing it is a parent
  specification change, not a validation change.
