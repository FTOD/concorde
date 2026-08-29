---
id: feature.concorde.workflow.retrieve-bounded-context
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
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/002-retrieve-bounded-context/design.md
---

# Feature Design: Retrieve Bounded Context

**Created**: 2026-08-26
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been accepted into this sub-feature's `implementation.md`
**Input**: Return exactly one useful architecture or feature-containment level through
`speckit.concorde.context`, built from module summaries and feature summary fields and returning
every design reference as navigation only.

## Outcome

A maintainer or coding agent can retrieve enough maintained context to reason about one target
without implicitly expanding unrelated or deeper specification, reference, or implementation detail.

## Parent Context and Boundary

The parent owns the shared meaning of modules, features, containment, refinement, and the
read/consult split at both levels. This child owns target resolution and the bounded context result.
It does not own validation or explanatory Q&A. The parent core diagram and bounded module view are
sufficient; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Navigate one deliberate level (Priority: P1)

A maintainer requests a module, parent feature, or immediate sub-feature and receives its current
responsibility, relationships, contracts, scenarios, and stable navigation references — including
where each feature's abstract and where the deeper reference material live, without that material
being expanded.

**Independent Test**: Query every target kind in a three-level module and two-level feature fixture
and inspect the result for required inclusions and forbidden expansions.

**Acceptance Scenarios**:
1. **Given** a module target, **When** context is requested, **Then** only that module's summary,
   immediate children, current-level features/contracts, permitted externals, and scenarios are
   expanded.
2. **Given** a child feature target, **When** context is requested, **Then** its parent and siblings
   appear only as concise durable summary fields (ID, title, outcome, evidence status, canonical
   root, abstract path) without attempt paths or bodies.
3. **Given** any target, **When** context is requested, **Then** the level's module `design.md` and
   any feature's `implementation.md` appear only as stable navigation references, never as expanded content.
4. **Given** an invalid or ambiguous target, **When** context is requested, **Then** findings are
   returned and maintained sources remain unchanged.

### Edge Cases

- Duplicate IDs, cycles, unreadable sources, or malformed containment metadata.
- A target is valid but has no children, siblings, scenarios, or contracts.
- A module has no `design.md`, a feature root lacks a durable companion, or it carries a legacy name.
- The only source of a requested fact is a design reference.

## Requirements

- **FR-001**: Context retrieval MUST resolve exactly one stable module or feature target.
- **FR-002**: A module result MUST expand only the current module and its immediate children.
- **FR-003**: A parent feature result MUST summarize immediate children in authored order.
- **FR-004**: A child result MUST summarize its parent and siblings without their bodies or attempts.
- **FR-005**: Results MUST distinguish containment from adjacent-module refinement.
- **FR-006**: Retrieval MUST be read-only and MUST return actionable findings for invalid sources.
- **FR-007**: A result MUST be built from module summaries, level views, contracts, and feature
  summary fields, and MUST include the module `design.md` only as a stable navigation reference.
- **FR-008**: A result MUST reference feature `abstract.md`, `design.md`, and `implementation.md` paths without
  expanding any body beyond the summary fields the parent defines (ID, title, outcome, evidence
  status, canonical root, abstract path).
- **FR-009**: A missing module reference, missing feature companion, or legacy feature name MUST
  surface as a finding, not silent substitution.

## Success Criteria

- **SC-001**: All bounded-context fixtures include every required current-level item and zero
  forbidden deeper items.
- **SC-002**: All child queries exclude parent and sibling attempt paths and bodies.
- **SC-003**: Repeating a query against unchanged sources produces an equivalent ordered result.
- **SC-004**: Zero fixture results contain a module `design.md`, feature `implementation.md`, `design.md`, or
  `abstract.md` body; every fixture result that has one available lists it as a reference.

## Assumptions

- Maintained sources are the authority; navigation references do not authorize automatic expansion.
- Deliberately opening a reference is the caller's act, outside this operation.
