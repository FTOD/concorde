# Implementation Plan: [FEATURE]

**Branch**: `[branch-or-worktree]` | **Date**: [DATE] | **Feature**: [direct feature-file link]

**Input**: The selected direct feature file, the providing module's `architecture.md`, current source code,
executable tests/checks, Constitution, bounded related-feature summaries, exact required-interface
owner feature specifications when needed, and reflection log.

## Summary

[State the requested feature/interface outcome and the technical delta against current code/tests.]

## Technical Context

**Language/Version**: [declared project/runtime versions]

**Primary Dependencies**: [frameworks/tools/external systems]

**Storage/State**: [persistent/shared state or N/A]

**Testing**: [repository-declared test frameworks and commands]

**Target Platform**: [platform/runtime/install target]

**Project Type**: [library/CLI/service/site/etc.]

**Performance Goals**: [measurable relevant goals]

**Constraints**: [safety, compatibility, authority, environment]

**Scale/Scope**: [affected modules/features/entities/files/tests]

## Constitution Check

*GATE: pass before research and re-check after technical design.*

| Principle | Plan evidence | Status |
|---|---|---|
| [Constitution principle] | [How the plan satisfies it or explicit justified exception] | [Pass/Exception] |

## Concorde Architecture Gate

Plan from four authorities: selected direct feature file, providing module architecture, current source
code, and executable evidence. The workspace resolver supplies bounded module ancestry and related-
feature summaries. A trusted context resolver may open another feature body only when it uniquely
owns an `interfaces.required` ID and must record that ID as the reason; dependency architecture,
source, tests, descendants, and attempts remain excluded.

1. Resolve every architecture entity named by the feature's interfaces and Architecture Zoom.
2. Identify every affected entity, directed relationship, interaction, embedded interface, source
   path, test surface, projection, package, and public guide.
3. Compare requested behavior directly with code/tests. Do not create a prose realization baseline.
4. Name an explicit task to reconcile each affected module architecture or feature-file authority.
   Planning itself writes only under the returned `attempt_dir`, plus the centralized reflection log
   when required.
5. Keep executable schemas/examples with code/tests; readable promises remain in feature files.
6. For every affected architecture-owned diagram, plan its textual counterpart, maintained JSON,
   deterministic validation, generated freshness, publication, and truthful visual-review status.
   Require one normalized unique output below `generated/` and `meta.legend.mode: hidden`.
7. Record conflicts, workarounds, assumptions, and provisional prototype choices in the returned
   `.concorde/reflections/log.md` authority.
8. When the feature changes an Operation, plan explicit public/internal exposure, leaf-owned effects,
   exact ordered capability/binding parity, nested-cycle rejection, concrete path-policy resolution,
   native/outer enforcement, receipt evidence, and Codex/Claude effective-set parity. LangGraph and
   prompt instructions never count as filesystem enforcement.

## Source Structure

```text
[real project source directories and architecture-significant files]

tests/
└── [real test/evidence paths]
```

**Structure Decision**: [Why this existing/new organization fits the module entity graph.]

## Attempt Artifacts

```text
<project>/
├── <providing-module>/features/<NNN-name>.md
└── .concorde/attempts/<stable-feature-id>/
    ├── checklists/
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md
    └── validation.md
```

No attempt file is stored in the specification hierarchy or mirrored beside the direct feature file.
Feature interfaces are embedded there; module entities/relationships/interactions stay in
architecture; implementation is source code.

## Research Decisions

For each material unknown, record:

- **Decision**: [chosen approach]
- **Rationale**: [evidence/tradeoff]
- **Alternatives considered**: [rejected options and why]

## Implementation Phases

1. Test/fixture setup that establishes the intended failing behavior.
2. Foundational shared entity/interface/runtime changes.
3. Independently testable user-story slices in priority order.
4. Cross-cutting architecture/feature/docs/projection reconciliation.
5. Focused, full, package, publication, freshness, and cleanup-only delivery evidence.

## Risk Controls

| Risk | Control | Verification |
|---|---|---|
| [risk] | [bounded plan/task/rollback control] | [exact command/check] |
| Ambient or unioned agent authority | [one narrowing policy/config/receipt per leaf occurrence] | [negative no-launch and native-parity checks] |

## Post-Design Constitution Re-check

[Confirm gates after research/data/interface/task structure is concrete.]
