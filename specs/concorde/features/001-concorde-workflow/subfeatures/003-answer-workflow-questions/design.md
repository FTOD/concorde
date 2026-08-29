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
evidence_status: partial
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/003-answer-workflow-questions/design.md
---

# Feature Design: Answer Workflow Questions

**Created**: 2026-08-26
**Revised**: 2026-08-28
**Status**: Specified and revised for the parent's three-tier feature document model; existing
realization has not been hardened into this sub-feature's `implementation.md`
**Input**: Answer grounded Concorde questions through `speckit.concorde.ask` from installed guidance,
module summaries, and feature abstracts first, opening specifications and design references only on
demand, without becoming a new authority.

## Outcome

A maintainer receives a concise, source-grounded answer about Concorde concepts, commands, artifact
placement, or current-project application without any workspace mutation and without the answer
silently reading more of the project than the question needs.

## Parent Context and Boundary

The parent defines the workflow being explained and which document holds which kind of fact. This
child owns question interpretation, minimal source selection, attribution, uncertainty, and
read-only behavior. It does not execute a runtime operation merely because one might help. The
parent diagram already distinguishes the agent-only question path from runtime operations, so no
child diagram is needed.

## User Scenarios & Testing

### User Story 1 - Ask a grounded question (Priority: P1)

A maintainer asks what a concept means, when to use a command, where an artifact belongs, how the
workflow applies to a selected project context, what a feature does, or why a level is built the way
it is.

**Independent Test**: Ask representative conceptual, procedural, project-specific, feature-level,
rationale-seeking, ambiguous, and unsupported questions and verify source use, attribution,
uncertainty, reference opening, and zero mutations.

**Acceptance Scenarios**:
1. **Given** an answer supported by installed guidance, **When** the question is asked, **Then** the
   answer identifies its authoritative basis and separates fact from inference.
2. **Given** project context is necessary, **When** the question concerns a child feature, **Then**
   only the child's abstract, the parent's abstract, the level's `module.md`, and concise sibling summary
   fields are considered, and the child's `design.md` is opened only when a requirement's exact
   wording is needed.
3. **Given** a question about why or how a level is built, **When** its `module.md` does not answer
   it, **Then** the answer opens that level's `implementation.md`, cites it, and says that it did.
4. **Given** a question about how a feature is realized, **When** its `abstract.md` does not answer it,
   **Then** the answer opens that feature's `implementation.md`, cites it, and says that it did.
5. **Given** ambiguity or conflicting evidence, **When** no safe answer exists, **Then** the response
   states uncertainty or asks one focused clarification.

### Edge Cases

- Installed guidance is missing, stale, or conflicts with maintained project sources.
- The question implicitly requests a mutation or unrelated implementation detail.
- The answer lives only in a specification's exact wording, a design reference, or an accepted
  realization that the question did not explicitly ask to open.
- A feature's abstract and specification disagree on the point asked about.

## Requirements

- **FR-001**: Answers MUST use installed Concorde guidance as the primary workflow authority.
- **FR-002**: Project-specific answers MUST use only the smallest relevant maintained context,
  starting from module summaries and feature abstracts.
- **FR-003**: Answers MUST identify their source basis and label inference, uncertainty, or conflict,
  including a abstract that disagrees with its specification.
- **FR-004**: The question surface MUST distinguish module summary, feature abstract, required behavior
  (`design.md`), module and feature design references, temporal attempt, generated evidence,
  containment, and refinement.
- **FR-005**: The question surface MUST NOT invoke another operation or mutate any source or control
  state.
- **FR-006**: Unsupported or materially ambiguous questions MUST receive an honest limitation or
  focused clarification.
- **FR-007**: The question surface MUST NOT open a feature `design.md` unless a requirement's exact
  wording is needed, MUST NOT open a module or feature `implementation.md` unless the question asks for
  implementation detail, rationale, or accepted realization, and MUST cite each document it opens.

## Success Criteria

- **SC-001**: Every acceptance answer identifies all authoritative source categories it relies on.
- **SC-002**: Every question test leaves maintained, temporal, generated, and selection bytes
  unchanged.
- **SC-003**: At least 90% of pilot maintainers can answer the original workflow question correctly
  after using the surface.
- **SC-004**: In all fixture questions answerable from module summaries and feature abstracts, zero
  specifications, references, or accepted realizations are opened; in all fixtures that require one,
  it is opened and cited.

## Assumptions

- The active coding agent can read installed guidance and explicitly requested maintained sources.
