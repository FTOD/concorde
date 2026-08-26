---
id: feature.concorde.workflow.retrieve-bounded-context
kind: feature
module: module.concorde
parent_feature: feature.concorde.workflow
refines: []
subfeatures: []
scenarios:
  - scenario-concorde-establish-and-place-feature
contracts:
  provided:
    - contract.concorde.workflow
  required:
    - contract.concorde.spec-kit-platform
architecture_view: specs/concorde/architecture.json
evidence_status: partial
canonical_spec: specs/concorde/features/001-concorde-workflow/subfeatures/002-retrieve-bounded-context/spec.md
---

# Feature Specification: Retrieve Bounded Context

**Created**: 2026-08-26
**Status**: Specified; existing realization has not been hardened into this sub-feature design
**Input**: Return exactly one useful architecture or feature-containment level through `speckit.concorde.context`.

## Outcome

A maintainer or coding agent can retrieve enough maintained context to reason about one target
without implicitly expanding unrelated or deeper specification and implementation detail.

## Parent Context and Boundary

The parent owns the shared meaning of modules, features, containment, and refinement. This child owns
target resolution and the bounded context result. It does not own validation or explanatory Q&A.
The parent core diagram and bounded module view are sufficient; no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Navigate one deliberate level (Priority: P1)

A maintainer requests a module, parent feature, or immediate sub-feature and receives its current
responsibility, relationships, contracts, scenarios, and stable navigation references.

**Independent Test**: Query every target kind in a three-level module and two-level feature fixture
and inspect the result for required inclusions and forbidden expansions.

**Acceptance Scenarios**:
1. **Given** a module target, **When** context is requested, **Then** only that module and immediate
   children, current-level features/contracts, permitted externals, and scenarios are expanded.
2. **Given** a child feature target, **When** context is requested, **Then** its parent and siblings
   appear only as concise durable summaries without implementation paths or bodies.
3. **Given** an invalid or ambiguous target, **When** context is requested, **Then** findings are
   returned and maintained sources remain unchanged.

### Edge Cases

- Duplicate IDs, cycles, unreadable sources, or malformed containment metadata.
- A target is valid but has no children, siblings, scenarios, or contracts.

## Requirements

- **FR-001**: Context retrieval MUST resolve exactly one stable module or feature target.
- **FR-002**: A module result MUST expand only the current module and its immediate children.
- **FR-003**: A parent feature result MUST summarize immediate children in authored order.
- **FR-004**: A child result MUST summarize its parent and siblings without their bodies or attempts.
- **FR-005**: Results MUST distinguish containment from adjacent-module refinement.
- **FR-006**: Retrieval MUST be read-only and MUST return actionable findings for invalid sources.

## Success Criteria

- **SC-001**: All bounded-context fixtures include every required current-level item and zero forbidden deeper items.
- **SC-002**: All child queries exclude parent and sibling implementation paths and bodies.
- **SC-003**: Repeating a query against unchanged sources produces an equivalent ordered result.

## Assumptions

- Maintained sources are the authority; navigation references do not authorize automatic expansion.
