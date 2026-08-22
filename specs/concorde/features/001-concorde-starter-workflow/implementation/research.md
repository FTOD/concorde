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
continues through the normal specify operation only after maintainer approval. Selection validates
an existing feature root and atomically updates the standard Spec Kit selection record. Both return
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

## Decision 5A: Deliver phase-specific routing through public preset command composition

**Decision**: Treat the checked-in `.specify/scripts/` and `.agents/skills/` edits as the
self-hosting prototype, not as proof that installed projects receive the behavior. Package supported
`concorde-core` preset command wrappers/overrides for the affected core phases. Those commands invoke
a project-local workspace adapter from the installed Concorde extension and use its returned root and
`implementation/` paths while preserving the underlying Spec Kit phase semantics. The first
implementation checkpoint must install the real preset/extension into clean Codex and slash-command
fixtures and prove the path matrix. If Spec Kit 0.16.4 cannot compose the required command/script
surface through its public preset APIs, stop and pursue an upstream Spec Kit change rather than
patching managed core infrastructure during installation.

**Rationale**: Spec Kit 0.16.4 publicly supports preset command replacement/composition, and its
resolver models scripts as a supported artifact type. Core-command overrides are therefore the
narrowest public mechanism to prototype. A stop condition prevents a self-host-only patch from being
misrepresented as composable product behavior.

**Alternatives considered**:

- Shipping direct overwrites of `.specify/scripts/` or installed core skills was rejected as an
  undocumented managed-infrastructure fork.
- Declaring the current repository edits sufficient was rejected because Feature 003 does not package
  them.
- Requiring a future Spec Kit version is the explicit fallback if the supported 0.16.4 prototype
  fails; any new range belongs to Feature 003 compatibility metadata.

## Decision 6: Treat placement as a reviewed proposal

**Decision**: Feature creation produces a deterministic proposal containing the providing module,
stable feature ID, nested root, canonical spec path, module registration changes, affected view, and
conflicts. No maintained architectural source is accepted without explicit human approval. Applying
the accepted placement is all-or-nothing and the normal specify phase fills the behavior.

**Rationale**: Placement changes durable intent and therefore needs the same proposal/apply safety as
root initialization. A complete proposal also makes nearest-common-parent decisions reviewable.

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
The two feature-workspace commands use standard Spec Kit command and selection contracts and may
orchestrate existing Architecture Core operations. Do not add new Architecture Service enum values
unless implementation proves a deterministic core operation is necessary; that would require an
explicit compatibility review.

**Rationale**: The missing user workflow can be delivered without forcing existing runtime consumers
to adopt a new custom protocol version. It also preserves the boundary between agent orchestration
and deterministic architecture semantics.

**Alternatives considered**:

- Expanding the v1 operation enum immediately was rejected because strict schema consumers could
  treat new values as incompatible.
- Creating a second custom workspace protocol was rejected until a real external boundary requires
  one.

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

## Unknowns Resolved

- The selected workspace is the nested feature root, not its `implementation/` child.
- Spec Kit selection remains the single active-workspace authority.
- Contracts and checklists remain durable; plan-phase artifacts are temporal.
- Feature creation coordinates reviewed placement with the normal specify phase.
- Installed routing must be proven through public preset/extension mechanisms; repository-local core
  edits alone are not delivery evidence.
- Architecture Core retains three v1 operations unless implementation demonstrates a necessary new
  deterministic boundary.
- Feature 003 owns installation/package education; Feature 002 owns site implementation.
- No unresolved `NEEDS CLARIFICATION` items remain for planning.
