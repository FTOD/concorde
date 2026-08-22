# Phase 0 Research: Concorde Core Workflow

**Feature**: `feature.concorde.core-workflow`  
**Date**: 2026-08-22  
**Scope**: One implementation attempt for the post-installation Concorde development workflow

This record resolves the implementation choices needed by the plan. Installation, catalogs,
component packaging, and removal belong to Feature 003 and are intentionally absent.

## Decision 1: Extend the Spec Kit lifecycle instead of introducing a second lifecycle

**Decision**: Keep Spec Kit authoritative for specify, clarify, plan, tasks, implement, analyze, and
converge. Concorde adds placement, architecture review, bounded context, deterministic validation,
and publication coordination around those phases.

**Rationale**: This preserves the constitution's composability requirement and gives every feature
one normal `spec.md`. Concorde can control architectural structure without taking ownership of
behavioral delivery mechanics.

**Alternatives considered**:

- A parallel Concorde lifecycle was rejected because it would duplicate Spec Kit authority.
- Generating architecture only after implementation was rejected because structure would no longer
  constrain the implementation plan.

## Decision 2: Use one recursive specification hierarchy

**Decision**: Resolve module packages recursively under one configured `specification_root`. A module
owns `module.md`, its current-level `architecture.json`, `contracts/`, `features/`, and optional
immediate `modules/` children.

**Rationale**: The filesystem then mirrors architectural ownership, while bounded readers can stop at
one level. Architecture remains part of the specification rather than a parallel top-level store.

**Alternatives considered**:

- A separate `architecture/` tree was rejected because it creates synchronization and ownership
  ambiguity.
- A flat project-wide feature directory was rejected because placement would no longer communicate
  the providing module.

## Decision 3: Separate durable feature intent from one temporal implementation attempt

**Decision**: Keep `spec.md`, `contracts/`, and `checklists/` at the feature root. Resolve plan,
tasks, research, technical models, runnable acceptance guidance, and evidence below
`implementation/`. Do not create root-level aliases or symlinks.

**Rationale**: A feature outlives any chosen implementation. The split lets a maintainer revise or
retire an implementation attempt without changing the feature identity or confusing delivery detail
with durable intent.

**Alternatives considered**:

- Keeping every artifact beside `spec.md` was rejected because temporal design appears canonical.
- Moving contracts into `implementation/` was rejected because boundary obligations survive an
  implementation attempt.
- Multiple simultaneously active implementation directories were deferred; the first release has
  one unambiguous `implementation/` workspace.

## Decision 4: Reuse Spec Kit's explicit feature-directory selection

**Decision**: Persist the selected nested feature root through Spec Kit's project selection record,
`.specify/feature.json`, using its `feature_directory` field. Concorde path resolution derives the
durable and temporal paths from that root. An explicit `SPECIFY_FEATURE_DIRECTORY` remains the
one-command override and read-only path inspection must not change selection.

**Rationale**: This is the existing supported selection mechanism in the checked-in Spec Kit
workflow. Reusing it avoids a second registry and already works without relying on Git branch names.

**Alternatives considered**:

- Inferring the feature only from the current branch was rejected because nested module paths and
  branch names are independent.
- A `.concorde/active-feature.json` registry was rejected as duplicate authority.
- Copying a nested feature into a flat `specs/` directory was rejected outright.

## Decision 5: Add two portable feature-workspace commands

**Decision**: Add `speckit.concorde.feature.create` and
`speckit.concorde.feature.select` as Spec Kit extension commands. Creation first retrieves bounded
module context, proposes the exact nested feature root and required architecture registrations, and
continues through the normal specify operation only after maintainer approval. The command surface,
not the Architecture Core runtime, coordinates behavioral spec authoring and the subsequent module
registration/validation steps. Selection validates an existing feature root and atomically updates
the standard Spec Kit selection record. Both return
the selected root plus derived specification and implementation paths.

**Rationale**: Users need a clear entry point for placement and selection, but the commands should
coordinate existing Spec Kit and Architecture Core responsibilities rather than implement a rival
specification system. Portable command Markdown keeps the same intent across agent integrations.

**Alternatives considered**:

- Making maintainers edit `.specify/feature.json` manually was retained only as a temporary fallback.
- Letting creation silently choose an owning module was rejected because module placement requires
  review.
- Having Architecture Core author the behavioral specification was rejected because that belongs to
  Spec Kit's specify phase.

## Decision 5A: Expose a distribution-neutral workspace handoff to Feature 003

**Decision**: Treat checked-in `.specify/scripts/` and `.agents/skills/` edits as self-hosting
prototypes, not installed-product evidence. Feature 001 owns a portable workspace adapter and
contract that return the selected feature root, `implementation/` root, and all phase paths. Feature
003 owns how the nine existing Spec Kit command surfaces are replaced/composed, registered, and
packaged for clean projects. Feature 001 acceptance proves the adapter and command semantics; Feature
003 acceptance proves release-installed Codex and slash-command materialization.

**Rationale**: Workflow semantics and distribution mechanics have different owners. The explicit
handoff keeps Feature 001 independent of agent presentation and package lifecycle while giving
Feature 003 one normative source for path behavior. Spec Kit 0.16.4 publicly supports command
replacement/composition, but preset script replacement is marked reserved for future use; therefore
Feature 001 must not assume that checkout-local core-script changes can ship.

**Alternatives considered**:

- Shipping direct overwrites of `.specify/scripts/` or installed core skills was rejected as an
  undocumented managed-infrastructure fork.
- Declaring the current repository edits sufficient was rejected because Feature 003 does not package
  them.
- Implementing preset registration and bundle acceptance inside Feature 001 was rejected because it
  duplicates Feature 003 ownership.
- Requiring a future Spec Kit version remains Feature 003's fallback if public command replacement
  cannot satisfy the handoff without core-script mutation.

## Decision 6: Treat placement as a reviewed proposal

**Decision**: Feature creation produces a deterministic proposal containing the providing module,
stable feature ID, nested root, canonical spec path, module registration changes, affected view, and
conflicts. No maintained architectural source is accepted without explicit human approval. The
accepted command orchestration keeps the proposal digest visible, lets the normal specify phase fill
the behavior, validates the resulting registration, and persists selection only after success.

**Rationale**: Placement changes durable intent and therefore needs a review-first boundary. Unlike
root initialization, it crosses the normal Spec Kit specify phase, so Concorde does not pretend that
one runtime file promotion can make the whole multi-command interaction atomic. A complete proposal
makes nearest-common-parent decisions reviewable, and withholding selection prevents false success.

**Alternatives considered**:

- Immediate directory creation was rejected because a wrong abstraction level would harden before
  review.
- An LLM-only placement answer was rejected because it would not be reproducible or safely
  applicable.

## Decision 7: Compose bounded implementation context from authoritative sources

**Decision**: For a feature target, return its root specification and contracts, active
`implementation/` artifacts, providing-module prose and current-level view, adjacent refinements,
relevant boundary contracts, declared evidence references, and navigation IDs. Do not inline child
feature bodies, grandchildren, unrelated implementation attempts, or generated page bodies.

**Rationale**: This is the smallest context that can support implementation while preserving the
one-level architecture rule and the durable/temporal distinction.

**Alternatives considered**:

- Returning the entire specification tree was rejected as unbounded and cognitively noisy.
- Returning architecture alone was rejected because implementation also needs active feature intent,
  design, and evidence expectations.

## Decision 8: Layer validation by artifact authority

**Decision**: Extend deterministic validation in ordered layers: source/profile parsing; identity and
paths; containment and refinement; feature workspace layout and selection; contract completeness and
custom example conformance; scenario/view boundaries; evidence state; and generated-output freshness
through the owning renderer/publication checks. Each finding names its rule, severity, source, and
remediation. Architecture success never implies implementation correctness.

Profile 1 uses an explicit adapter registry: standard-library JSON and TOML, the existing constrained
YAML reader, and a documented deterministic subset for checked-in JSON Schema/grammar constructs.
Unsupported serialization/schema combinations return an unsupported-adapter finding. Freshness reads
source-digest/provenance receipts produced by Archify and Documentation; it does not execute arbitrary
configured commands or reproduce renderer logic.

**Rationale**: Each artifact kind has one authority. Layered checks expose disagreement without
silently choosing a winner and keep failures reproducible without an AI model.

**Alternatives considered**:

- One monolithic pass was rejected because rule ownership and targeted tests would be unclear.
- Treating missing evidence as success was rejected because it overstates confidence.
- Reimplementing Archify or Docusaurus validation in Architecture Core was rejected; Concorde should
  coordinate those deterministic owners and normalize their results.

## Decision 9: Keep contract evolution additive in the current slice

**Decision**: Keep Concorde Architecture Service Protocol v1 for `init`, `context`, and `validate`.
Use the separate custom Feature Workspace Protocol v1, owned by Spec Kit Integration, for reviewed
`feature.create`, atomic `feature.select`, selected-root resolution, and phase-path results. The two
command presentations may orchestrate existing Architecture Core operations, but they do not add
create/select enum values to Architecture Service Protocol v1.

**Rationale**: The missing user workflow can be delivered without forcing existing runtime consumers
to adopt a new custom protocol version. It also preserves the boundary between agent orchestration
and deterministic architecture semantics.

**Alternatives considered**:

- Expanding the v1 operation enum immediately was rejected because strict schema consumers could
  treat new values as incompatible.
- Encoding selection only in prompt prose was rejected because Feature 003 needs a deterministic,
  versioned adapter result to package and test.

## Decision 10: Prove automation and human comprehension separately

**Decision**: Use Python `unittest` and subprocess tests for path resolution, portable commands,
workspace selection, context boundaries, validation determinism, source immutability, and
self-application. Use timed participant protocols only for SC-001 and SC-007; automated checks cannot
stand in for human placement speed or conceptual understanding.

**Rationale**: The success criteria mix deterministic product behavior with human comprehension.
Keeping evidence classes separate prevents passing tests from becoming an unsupported usability
claim.

**Alternatives considered**:

- Inferring human success from documentation and tests was rejected.
- Requiring a human pilot for deterministic byte/path outcomes was rejected as unnecessary and less
  reproducible.

## Decision 11: Give feature diagrams one declared source boundary

**Decision**: Store feature-owned Archify JSON directly below the feature's `diagrams/` directory and
declare every view in `spec.md`. Architecture Core includes declared JSON in source identity and
bounded feature context. Documentation resolves each declaration to a fresh generated artifact and
embeds it automatically on the canonical feature page.

**Rationale**: A dedicated directory keeps durable visual explanations discoverable without mixing
them with the feature specification, contracts, checklists, or temporal implementation artifacts.
Declaration-driven publication prevents manual Docusaurus markup from becoming a second registry.

**Alternatives considered**:

- Keeping JSON beside `spec.md` was rejected because multiple durable artifact kinds become harder to
  scan and enforce consistently.
- Hand-written iframe markup in each specification was rejected because it duplicates routing,
  provenance, sandboxing, and freshness behavior.

## Unknowns Resolved

- The selected workspace is the nested feature root, not its `implementation/` child.
- Spec Kit selection remains the single active-workspace authority.
- Contracts and checklists remain durable; plan-phase artifacts are temporal.
- Feature creation coordinates reviewed placement with the normal specify phase.
- Feature 001 proves the workspace adapter/command semantics; Feature 003 alone proves their public
  preset/extension delivery. Repository-local core edits are not product evidence.
- Spec Kit 0.16.4 command composition is public, while preset script replacement is not a supported
  delivery mechanism for this plan.
- Architecture Core retains three v1 operations unless implementation demonstrates a necessary new
  deterministic boundary.
- Feature 003 owns installation/package education; Feature 002 owns site implementation.
- Feature-owned Archify JSON lives under `diagrams/` and is published from `spec.md` declarations.
- All planning questions are resolved.
