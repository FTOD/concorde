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
**Status**: Specified; existing realization has not been hardened into this sub-feature design
**Input**: Deterministically validate Concorde maintained sources through `speckit.concorde.validate`.

## Outcome

A maintainer receives a repeatable, complete, actionable account of structural validity and known
evidence agreement without validation rewriting the sources it evaluates.

## Parent Context and Boundary

The parent owns which invariants connect the workflow. This child owns deterministic discovery,
rule evaluation, target scoping, findings, status, and evidence classification. It does not judge
whether prose is elegant or whether an application behaves correctly. The parent diagram and bounded
architecture view are sufficient; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Validate maintained intent (Priority: P1)

A maintainer validates the whole project or one supported target after structural changes and receives
sorted findings with rule, severity, source, explanation, and remediation.

**Independent Test**: Run validation repeatedly across valid and seeded-invalid hierarchy, contract,
scenario, refinement, containment, layout, diagram, selection, and evidence fixtures.

**Acceptance Scenarios**:
1. **Given** valid unchanged sources, **When** validation is repeated, **Then** status, digest, summary,
   and ordered findings are equivalent.
2. **Given** seeded structural faults, **When** validation runs, **Then** every applicable fault is
   reported without hiding later findings.
3. **Given** missing or conflicting implementation evidence, **When** validation assesses freshness,
   **Then** it reports unknown or disagreement rather than agreement.

### Edge Cases

- Malformed metadata prevents normal source indexing.
- A path looks feature-like but is at an illegal depth or crosses a symlink.
- A scoped target is unknown or ambiguous.

## Requirements

- **FR-001**: Validation MUST be read-only, deterministic, and repeatable for unchanged inputs.
- **FR-002**: Findings MUST include stable rule ID, severity, location, explanation, and actionable remediation.
- **FR-003**: Validation MUST cover identities, paths, module hierarchy, contracts, scenarios, views, refinements, feature containment, diagrams, selection safety, and evidence references.
- **FR-004**: Containment and refinement MUST be validated as distinct acyclic relationships.
- **FR-005**: Illegal third-level, alternate-depth, dangling, duplicate, cyclic, symlinked, or mismatched feature roots MUST be actionable findings.
- **FR-006**: Validation MUST preserve complete sorted findings and stable success, invalid, conflict, and failed statuses.
- **FR-007**: Unknown evidence MUST NOT be promoted to agreement.

## Success Criteria

- **SC-001**: Repeated unchanged validation outputs are byte-equivalent in all deterministic fixtures.
- **SC-002**: Every seeded structural rule violation is detected with its expected stable rule ID.
- **SC-003**: Validation produces zero source changes in every success and failure fixture.
- **SC-004**: All valid two-level feature fixtures pass containment validation with zero findings.

## Assumptions

- Semantic simplicity and non-duplication of prose remain requirements-review judgments.
