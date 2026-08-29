---
id: feature.concorde.workflow.validate-architecture
kind: feature
module: module.concorde
parent_feature: feature.concorde.workflow
refines: []
subfeatures: []
scenarios:
  - feature-work
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
evidence_status: partial
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/008-validate-architecture/design.md
---

# Feature Design: Validate Architecture

**Created**: 2026-08-26
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been accepted into this sub-feature's `implementation.md`
**Input**: Deterministically validate Concorde maintained sources through `speckit.concorde.validate`,
including the module summary and feature abstract shape and reading-budget rules, reference presence,
the durable trio, and legacy names.

## Outcome

A maintainer receives a repeatable, complete, actionable account of structural validity, document-model
compliance, and known evidence agreement without validation rewriting the sources it evaluates.

## Parent Context and Boundary

The parent owns which invariants connect the workflow and defines the document model and reading
budgets. This child owns deterministic discovery, rule evaluation, target scoping, findings, status,
and evidence classification. It does not judge whether prose is elegant, whether a abstract is a
faithful summary, or whether an application behaves correctly. The parent diagram and bounded
architecture view are sufficient; no child diagram is needed.

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
   inventory table, a module without `implementation.md` or with one unreachable from its summary, a feature
   root without `abstract.md` or with a abstract that is over budget, missing a section, missing its
   structure link, or citing no requirement in its `Logic` rules, or a feature root with legacy names,
   **When** validation runs, **Then** each is reported with a stable rule ID and
   a concrete remediation.
4. **Given** missing or conflicting implementation evidence, **When** validation assesses freshness,
   **Then** it reports unknown or disagreement rather than agreement.

### Edge Cases

- Malformed metadata prevents normal source indexing.
- A path looks feature-like but is at an illegal depth or crosses a symlink.
- A leaf module omits a structure diagram without recording a rationale.
- A feature root contains a legacy filename or lacks `abstract.md`/`implementation.md`.
- A abstract `Logic` rule cites a requirement ID that does not exist in the adjacent `design.md`.
- A scoped target is unknown or ambiguous.

## Requirements

- **FR-001**: Validation MUST be read-only, deterministic, and repeatable for unchanged inputs.
- **FR-002**: Findings MUST include stable rule ID, severity, location, explanation, and actionable
  remediation.
- **FR-003**: Validation MUST cover identities, paths, module hierarchy, contracts, scenarios, views,
  refinements, feature containment, diagrams including the required `meta.legend.mode: hidden`
  presentation policy, selection safety, evidence references, module summary
  shape and reading budget, module design-reference presence and reachability, feature abstract
  presence, shape, structure link, requirement citations, and reading budget, the feature-root
  durable trio, and legacy document names.
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
- **FR-009**: Validation MUST check every feature root for a `abstract.md` with exactly the parent's
  five sections in order, a structure section that links a maintained diagram or contains a text
  sketch, a `Logic` section whose rules name requirement IDs present in the adjacent `design.md`, and
  the abstract reading budget.
- **FR-010**: Validation MUST report legacy `tldr.md`/`spec.md` files and `implementation/` attempt
  directories, a missing `implementation.md`, and a missing `abstract.md` with distinct remediations.
- **FR-011**: Reading-budget findings for summaries and abstracts MUST use the deterministic proxies
  the parent records, MUST be warnings that leave the status unchanged, and MUST NOT judge prose
  quality or summary faithfulness.

## Success Criteria

- **SC-001**: Repeated unchanged validation outputs are byte-equivalent in all deterministic fixtures.
- **SC-002**: Every seeded structural rule violation, including a maintained diagram with a visible
  or implicit legend, is detected with its expected stable rule ID.
- **SC-003**: Validation produces zero source changes in every success and failure fixture.
- **SC-004**: All valid two-level feature fixtures pass containment validation with zero findings.
- **SC-005**: Every seeded document-model violation (over-budget summary or abstract, missing diagram,
  table, section, structure link, or requirement citation, missing or unreachable module reference,
  missing abstract or feature reference, legacy or duplicated feature-root name) is detected with its
  expected rule ID, and every compliant fixture passes with zero document-model findings.

## Assumptions

- Semantic simplicity, non-duplication of prose, and abstract faithfulness remain requirements-review
  judgments.
- The reading-budget proxies are the ones recorded in the parent's assumptions; changing them is a
  parent specification change, not a validation change.
