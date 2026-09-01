---
id: feature.concorde.workflow.accept-milestone
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
canonical_design: specs/concorde/features/001-concorde-workflow/subfeatures/009-accept-milestone/design.md
---

# Feature Design: Deliver Milestone

**Created**: 2026-08-26
**Revised**: 2026-09-01
**Status**: Revised for the `deliver` command and single-authorization delivery flow. The existing
approval-gated realization remains the accepted baseline until this revision is delivered.
**Input**: Rename the `impl-accept` command to `deliver`. When a user asks for delivery, that
invocation is sufficient authorization: do not pause for a second explicit approval. Update the
related specifications and complete the normal specify, plan, tasks, implement, and delivery loop.

## Outcome

A maintainer can invoke `deliver` once to promote one completed implementation attempt as the
selected feature or sub-feature's durable realization in `implementation.md`, carry
attempt-developed rationale into the level's module `design.md` when warranted, and atomically
remove exactly that milestone's temporal attempt without a second approval interaction.

## Parent Context and Boundary

The parent owns the durable/temporal authority model, the document model, and the lifecycle
placement of milestone delivery. This child owns eligibility, candidate synthesis, invocation-bound
authorization, failure-safe apply, and result reporting. It does not execute incomplete work, change
behavior requirements, or touch the abstract or specification. The stable ID and title use the
historical `accept-milestone` identity and current Deliver Milestone vocabulary respectively;
the accepted implementation artifact is the feature `implementation.md`. The parent diagram already depicts the
agent/runtime authorization split and the artifact transition.

## User Scenarios & Testing

### User Story 1 - Deliver one completed realization (Priority: P1)

A maintainer invokes the delivery command for a completed attempt and receives the applied durable
realization, any warranted module `design.md` amendment, and the exact cleanup result without being
asked to approve a generated proposal in a second interaction.

**Independent Test**: Exercise eligible, incomplete, malformed, stale, unsafe, interrupted, first-time,
repeat, parent, and child attempts, with and without a module-reference amendment, while
snapshotting all related roots, abstracts, specifications, module summaries, and module references.

**Acceptance Scenarios**:
1. **Given** incomplete tasks or unresolved checklist items, **When** delivery is invoked, **Then**
   it is ineligible and changes nothing.
2. **Given** an eligible attempt, **When** delivery is invoked, **Then** the invocation authorizes
   candidate synthesis and immediate apply, and the workflow does not stop to request approval of
   the generated candidate.
3. **Given** the invocation-authorized proposal remains current, **When** apply completes, **Then** the selected
   feature `implementation.md` matches the generated candidate, the level's module `design.md` matches the
   generated amendment when one was proposed, only the selected attempt is absent, and `abstract.md` and
   `design.md` are byte-identical.
4. **Given** a first delivery of a root whose `implementation.md` holds only the not-yet-accepted state,
   **When** apply completes, **Then** the feature `implementation.md` is written in full; **Given** a later
   delivery, **Then** it is completed and updated rather than duplicated.
5. **Given** a stale or interrupted apply, **When** the operation fails, **Then** the previous feature
   `implementation.md`, the previous module `design.md`, and the complete attempt remain recoverable.

### Edge Cases

- No recognizable task exists; task or checklist Markdown is malformed.
- Proposal paths escape the selected root or use symlinks.
- The proposal names a `module.md`, a `abstract.md`, a `design.md`, a module `design.md` at a level other
  than the one at which the feature is specified, or a legacy filename.
- Parent, child, sibling, selection, or source digest changes after review.
- A caller submits the superseded command, operation name, proposal shape, status, diagnostic code,
  or a compatibility alias.

## Requirements

- **FR-001**: Eligibility MUST require at least one recognizable task, every task complete, and
  every existing checklist item complete and well formed.
- **FR-002**: Proposal mode MUST be read-only and return the runtime-resolved candidate location,
  task/checklist summaries, selected target, optional module-reference amendment target, cleanup
  target, and source digest. It is an internal safety phase of delivery rather than a separate
  user-approval phase.
- **FR-003**: The candidate feature `implementation.md` MUST capture accepted collaboration, flows,
  decisions, evidence, limitations, and the implementation detail a coder needs under the parent's
  six fixed sections, without copying the temporal task log. Delivery MUST present attributed
  reflection entries transiently from `reflections.md`, MUST keep that log as their sole persisted
  authority, and MUST reject an `R-NNN` identifier in candidate feature `implementation.md` or module
  `design.md` content with `CONCORDE-DELIVER-012`.
- **FR-004**: A user's invocation of `deliver` MUST be the sole authorization required for an
  eligible delivery. After producing a valid current proposal, the command MUST apply it without
  displaying a second approval question or waiting for another user response.
- **FR-005**: Apply MUST accept only the selected root's `implementation.md`, its complete `attempt/`
  directory, and — when the proposal includes it — the module `design.md` of the level at which the
  feature is specified as mutation targets, and MUST reject any `module.md`, `abstract.md`, `design.md`,
  any other level's `implementation.md`, and any legacy filename.
- **FR-006**: Realization replacement, reference amendment, and attempt removal MUST complete
  atomically or restore every prior state.
- **FR-007**: Child milestone delivery MUST preserve parent and siblings; parent milestone delivery MUST preserve every
  child root.
- **FR-008**: A success result MUST report prior/resulting feature `implementation.md` digests,
  prior/resulting module `design.md` digests when amended, removed artifacts, selected feature, and
  retained authorities.
- **FR-009**: A candidate module `design.md` amendment MUST contain only implementation detail and
  rationale developed during the attempt, organized under the reference's stable headings, and MUST
  NOT restate or alter facts owned by `module.md`, contracts, or the level view.
- **FR-010**: Milestone delivery MUST write the feature `implementation.md` in full on the first delivered milestone
  and complete or update it on later ones, never leaving the not-yet-accepted placeholder beside
  accepted content.
- **FR-011**: Current commands, agent surfaces, runtime operations, statuses, diagnostics, contracts,
  schemas, examples, tests, documentation, and specifications MUST use the Deliver Milestone
  vocabulary consistently, MUST reject the superseded interface, and MUST provide no compatibility
  alias or transition period.
- **FR-012**: Delivery MUST preserve the digest binding, path constraints, candidate validation,
  atomic staging, rollback, and complete result reporting of the existing realization even though
  the user interaction no longer pauses between proposal creation and apply.

## Success Criteria

- **SC-001**: Every incomplete, malformed, unsafe, or stale fixture produces zero durable or temporal
  changes.
- **SC-002**: Every eligible invoked fixture leaves a feature `implementation.md` byte-identical to the generated
  candidate, a module `design.md` byte-identical to the generated amendment when one was proposed,
  removes exactly one attempt, and persists zero reflection identifiers outside `reflections.md`.
- **SC-003**: Every injected interruption restores the prior feature `implementation.md`, the prior module
  `implementation.md`, and the complete attempt.
- **SC-004**: All parent, child, and sibling roots, every `abstract.md` and `design.md`, and every
  `module.md` outside the selected mutation targets remain byte-identical.
- **SC-005**: Repository validation finds zero current command, documentation, code, contract,
  schema, example, test, or specification references to the superseded terminology or interface,
  apart from immutable version-control history; matching maintained reflection entries are rewritten
  with their stable `R-NNN` identifiers and valid structure preserved.

## Assumptions

- Requirements changes occur through specification review, not through milestone delivery; the
  abstract is never refreshed by milestone delivery.
- The level at which the feature is specified is the level whose module `design.md` an acceptance
  proposal may amend; a feature realized across several modules records lower-level detail in those
  modules' references through their own feature milestones.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Milestone delivery`<br />Aliases: `Delivery` | The invocation-authorized operation that promotes a complete attempt into durable accepted realization and does not request a second approval. | `applies` → `Delivery proposal`; `writes` → `Feature implementation` |
| `Delivery candidate` | The full proposed replacement content and exact removal set generated after delivery is invoked and before atomic apply. | `forms` → `Delivery proposal`; `contains` → `Removal set` |
| `Removal set` | The exact complete attempt artifacts deleted only after the delivered replacements are safely committed. | `contains` → `Temporal artifact` |
| `Retained authority` | A maintained source explicitly proven byte-identical across delivery, such as feature specification, abstract, module summary, contracts, or reflection log. | `is a` → `Durable artifact` |
