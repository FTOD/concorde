# Implementation Plan: Relax Fast-Loop Eligibility

**Branch**: `main` | **Date**: 2026-08-30 | **Spec**: [design.md](../design.md)

**Input**: Permit a bounded fast loop to reconcile multiple related existing features and
inter-module contract/format detail while keeping module responsibilities, dependency direction, and
whole-project user compatibility/migration policy outside the fast boundary.

## Summary

Replace the former one-feature/non-contract eligibility rule with an anchor-plus-affected-set model.
The standard Feature Workspace Protocol selection remains the canonical anchor. The agent discovers
related affected roots from bounded evidence and resolves each root independently through the same
adapter before mutation. Every affected feature must have an accepted realization and no active
attempt. Contract, format, diagram, and related module-reference updates are allowed when they keep
module responsibilities and dependencies stable; AI-authored architecture sources remain pending
exact maintainer review under constitution A.V. Compatibility and migration gating applies only to
durable promises made to users of the whole project.

## Technical Context

**Language/Version**: Agent-followed Markdown; Python 3.11 for existing workspace and validation
helpers; Python/TypeScript repository tests

**Primary Dependencies**: Spec Kit 0.16.4 preset composition, Feature Workspace Protocol v8,
Concorde deterministic validation, development self-hosting

**Storage**: Version-controlled Markdown/JSON/YAML plus installed Codex and Claude skill projections

**Testing**: Python `unittest`, Spec Kit component build/verification, Concorde validation, docsite
TypeScript/Vitest/source/build checks

**Target Platform**: Supported Spec Kit projects using an installed Concorde preset and extension

**Project Type**: Agent-guided development framework and distributable preset/extension bundle

**Performance Goals**: No new runtime or protocol operation; fast-loop preflight remains bounded to
the anchor, discovered affected roots, and directly relevant evidence

**Constraints**: No hidden attempt/acceptance lifecycle; preserve unrelated work; no module
responsibility or dependency change; no project-level user compatibility/migration policy change;
architecture-source edits require exact maintainer review

**Scale/Scope**: One canonical command, two installed skill projections, one selected child feature
and its parent aggregate workflow, public command/workflow guides, focused command/distribution tests

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1.*

- **A.I / A.II**: The abstract, detailed design, command contract, canonical surface, installed
  projections, and guides remain synchronized and navigable.
- **A.III**: The change preserves every module responsibility and dependency direction. It changes
  workflow eligibility and documentation scope, not architectural ownership.
- **A.IV**: Contract-format changes must reconcile provider/consumer promises, affected features,
  examples, and evidence together. They are reviewed for feature impact and potential project-level
  compatibility impact rather than rejected categorically.
- **A.V**: Deterministic checks remain mandatory. Any AI-authored contract, maintained diagram, or
  other architecture authority ends `review_pending` until the maintainer reviews its exact diff;
  therefore eligibility does not bypass human architecture review.
- **B.I / B.II**: Canonical preset sources, installed Codex/Claude surfaces, self-host status, release
  packaging, and project documentation are reconciled and validated in this checkout.
- **Governance**: No constitutional amendment is required. R-041 records and resolves the initially
  omitted architecture-review timing within this attempt.

## Project Structure

### Documentation (this feature)

```text
specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/
├── abstract.md
├── design.md
├── implementation.md
├── contracts/fast-loop-command.md
└── attempt/
    ├── checklists/requirements.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md
    └── validation.md
```

### Source Code (repository root)

```text
presets/concorde/commands/speckit.fast-loop.md       # canonical policy surface
.specify/presets/concorde/commands/                  # self-hosted preset projection
.agents/skills/speckit-fast-loop/SKILL.md            # installed Codex projection
.claude/skills/speckit-fast-loop/SKILL.md            # installed Claude projection
extensions/concorde/scripts/python/workspace.py       # unchanged anchor resolver
extensions/concorde/runtime/concorde/feature_workspace.py # unchanged Protocol v8 routing
specs/concorde/features/001-concorde-workflow/        # parent aggregate authority/contracts/view
specs/concorde/architecture/contracts/                # project workflow boundary contract
specs/concorde/architecture/diagrams/                 # project skill/workspace flow wording
docs/ and README.md                                   # public workflow guidance
tests/concorde/contract/                              # command and installed-surface contract tests
scripts/development/self-host-concorde.py             # existing projection refresh/verification
scripts/release/build-components.py                   # existing package verification
```

**Structure Decision**: Keep policy semantics in the agent-followed command and durable workflow
documents. Protocol v8 continues to resolve one canonical root per invocation; fast-loop uses the
first result as the anchor and may invoke the same adapter explicitly for each discovered affected
root. No multi-selection registry, new protocol field, or mutation runtime is introduced.

## Feature Diagram Strategy

No child-owned diagram is needed. The parent core architecture view already shows the maintainer,
fast-loop command, workspace adapter, feature intent/realization, architecture sources, code, tests,
and evidence. The change adds no component, responsibility, or dependency, so topology stays stable;
however, its notes and flow labels must distinguish one-root normal phases from fast-loop's repeated
anchor/affected-root resolution. Update `../../diagrams/concorde-workflow-components.json` and the
project-level `../../../../architecture/diagrams/skill-workspace-file-flow.json` wording, preserve
their linked textual counterparts and `meta.legend.mode: hidden`, regenerate their automatic HTML
deliveries, and run Archify showcase/freshness validation. The exact JSON diffs require maintainer
review before acceptance under A.V.

## Concorde Architecture Gate

- **Providing module**: `module.concorde`; its responsibility and five-child dependency structure
  remain unchanged.
- **Affected realization modules**: `module.concorde.skills` owns the command guidance;
  `module.concorde.scripts` continues to provide root-by-root canonical workspace resolution;
  `module.concorde.distribution` and Feature 004 self-hosting continue to package and materialize the
  canonical command without policy-specific runtime logic.
- **Contracts**: Update the feature-owned `contracts/fast-loop-command.md`, parent
  `contracts/architecture-sources.md` phase-authority mapping, parent `contracts/agent-commands.md`
  distribution handoff, and project `architecture/contracts/concorde-workflow/contract.md`. No
  protocol schema changes; the contracts explain repeated explicit-root resolution, affected-source
  authority, architecture review, and project-level compatibility policy.
- **Views**: Parent and project diagrams remain topologically stable but need their fast-loop notes
  and authority cards reconciled.
- **Related feature authority**: Reconcile parent `feature.concorde.workflow` aggregate design and
  abstract because they duplicate the fast-loop boundary. No sibling feature behavior changes.
- **Public guidance**: Reconcile `README.md`, `docs/commands.md`, `docs/concorde-workflow.md`,
  and `docs/quick-start.md`. Preset/bundle READMEs describe packaging rather than eligibility and
  remain byte-identical.
- **Reflection**: R-041 records the planning-discovered human-review omission.

### Accepted Realization Delta

Remain unchanged:

- fast-loop stays an additive agent-followed preset command with no mutation runtime;
- Protocol v8 supplies one root-scoped canonical workspace per adapter call;
- no first accepted realization, active attempt, hidden plan/tasks/acceptance, unsafe worktree
  overlap, or material ambiguity is allowed;
- proportional tests, deterministic validation, hooks, reflection behavior, and truthful reporting
  remain mandatory.

Replace or extend:

- replace one-feature ownership with a selected anchor plus complete affected feature set;
- resolve and inspect every affected feature independently and require an accepted/no-attempt
  baseline for each;
- allow bounded cross-feature behavior and contract/format/diagram/module-reference reconciliation;
- narrow architecture rejection to changed module responsibilities or dependency direction;
- narrow compatibility/migration rejection to project-level promises for users of the whole project;
- add `not_required` / `review_pending` / `reviewed` architecture review reporting;
- report all affected feature IDs/roots and per-feature durable-document impact.

## Complexity Tracking

No constitutional violations or additional architectural components are introduced.
