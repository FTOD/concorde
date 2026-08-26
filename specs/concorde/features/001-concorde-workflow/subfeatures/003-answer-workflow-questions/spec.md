---
id: feature.concorde.workflow.answer-workflow-questions
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
canonical_spec: specs/concorde/features/001-concorde-workflow/subfeatures/003-answer-workflow-questions/spec.md
---

# Feature Specification: Answer Workflow Questions

**Created**: 2026-08-26
**Status**: Specified; existing realization has not been hardened into this sub-feature design
**Input**: Answer grounded Concorde questions through `speckit.concorde.ask` without becoming a new authority.

## Outcome

A maintainer receives a concise, source-grounded answer about Concorde concepts, commands, artifact
placement, or current-project application without any workspace mutation.

## Parent Context and Boundary

The parent defines the workflow being explained. This child owns question interpretation, minimal
source selection, attribution, uncertainty, and read-only behavior. It does not execute a runtime
operation merely because one might help. The parent diagram already distinguishes the agent-only
question path from runtime operations, so no child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Ask a grounded question (Priority: P1)

A maintainer asks what a concept means, when to use a command, where an artifact belongs, or how the
workflow applies to a selected project context.

**Independent Test**: Ask representative conceptual, procedural, project-specific, ambiguous, and
unsupported questions and verify source use, attribution, uncertainty, and zero mutations.

**Acceptance Scenarios**:
1. **Given** an answer supported by installed guidance, **When** the question is asked, **Then** the
   answer identifies its authoritative basis and separates fact from inference.
2. **Given** project context is necessary, **When** the question concerns a child feature, **Then**
   only the child, parent durable pair, and concise sibling summaries are considered.
3. **Given** ambiguity or conflicting evidence, **When** no safe answer exists, **Then** the response
   states uncertainty or asks one focused clarification.

### Edge Cases

- Installed guidance is missing, stale, or conflicts with maintained project sources.
- The question implicitly requests a mutation or unrelated implementation detail.

## Requirements

- **FR-001**: Answers MUST use installed Concorde guidance as the primary workflow authority.
- **FR-002**: Project-specific answers MUST use only the smallest relevant maintained context.
- **FR-003**: Answers MUST identify their source basis and label inference, uncertainty, or conflict.
- **FR-004**: The question surface MUST distinguish containment, refinement, durable intent, attempts, and generated evidence.
- **FR-005**: The question surface MUST NOT invoke another operation or mutate any source or control state.
- **FR-006**: Unsupported or materially ambiguous questions MUST receive an honest limitation or focused clarification.

## Success Criteria

- **SC-001**: Every acceptance answer identifies all authoritative source categories it relies on.
- **SC-002**: Every question test leaves maintained, temporal, generated, and selection bytes unchanged.
- **SC-003**: At least 90% of pilot maintainers can answer the original workflow question correctly after using the surface.

## Assumptions

- The active coding agent can read installed guidance and explicitly requested maintained sources.
