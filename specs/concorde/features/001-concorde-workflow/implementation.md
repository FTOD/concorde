# Feature Implementation: Concorde Workflow

**Feature**: `feature.concorde.workflow`

**Realization status**: Accepted realization of the architecture-aware Spec Kit workflow under the
feature-root `abstract.md` / `design.md` / `implementation.md` model, module `module.md` / `design.md`
pair, Architecture Source Profile 4, Feature Workspace Protocol v8, acceptance proposal v6, and Build
Manifest v8. Revised 2026-08-29 for the canonical naming model and again for the module
`architecture/` directory, and migrated across this repository.

## Realization Overview

Concorde preserves Spec Kit as the owner of specification, clarification, planning, tasks, implementation, analysis, convergence, and task-to-issue conversion. Around that lifecycle it adds reviewed module ownership, feature placement, one optional level of first-class sub-features, selected-workspace routing, bounded context built from module summaries and feature abstracts, deterministic validation (structure, contracts, scenarios, evidence, freshness, summary shape and budget, abstract shape and budget, reference presence, and the feature-root durable trio), feature-owned diagrams, approval-gated acceptance, and a source-grounded read-only question surface.

Every level separates what is read from what is consulted. A module owns `module.md` (the
eight-section summary), `design.md` (implementation notes, rationale, alternatives, and decisions),
and, under `architecture/`, its diagrams (`diagrams/`, at least one level view for a non-leaf),
boundary contracts (`contracts/`), and submodules (`modules/`). A feature root owns durable `abstract.md` (read-first
orientation), `design.md` (self-contained required behavior), and `implementation.md` (accepted
realization), optional `contracts/` and `diagrams/`, and at most one temporal `attempt/`. New feature
implementations begin as the `implementation-template` placeholder and are replaced only by approved
acceptance. No alias or symlink stands in for any canonical name.

Selection remains the standard Spec Kit `.specify/feature.json` pointer (or
`SPECIFY_FEATURE_DIRECTORY`). Protocol v8 derives the selected kind, ID, providing module,
`feature_abstract`, `feature_design`, `feature_implementation`, `module_summary`, `module_design`,
`attempt_dir`, `attempt_state`, nullable parent context, and bounded sibling summaries with
`abstract`, `design`, and `implementation` paths but never bodies.

## Module and Feature Collaboration

- `module.concorde.skills` owns the nine normal-phase command overrides, six templates (`spec`,
  `abstract`, `implementation`, `reflections`, `plan`, `tasks`), and the extension's five
  user-visible command surfaces.
- `module.concorde.scripts` owns selected-workspace routing, Profile 4 discovery, bounded context,
  readiness, validation, reflection diagnostics, and implementation-acceptance operations.
- `module.concorde.workspace-files` owns Protocol v8 paths and lifetimes for the durable feature
  trio, module summaries and references, selection state, reflections, and temporal `attempt/`
  evidence.
- `module.concorde.auto-docs` publishes Build Manifest v8 collections `architecture`, `docs`,
  `feature-abstracts`, `features`, and `feature-implementations`; routes are the abstract landing page,
  `/design`, and `/implementation`, and `attempt/**` is excluded.
- `module.concorde.distribution` packages the six templates, nine normal-phase replacements, five
  Concorde surfaces, and four portable scripts at version 0.4.0.

Across `contract.concorde.spec-kit-platform`, `abstract-template` and `implementation-template` are
resolved through the public preset stack. The tracked local helpers export `FEATURE_ABSTRACT`,
`FEATURE_DESIGN`, `FEATURE_IMPLEMENTATION`, and `ATTEMPT_DIR`; composed templates show the same
canonical tree.

## Scenario Realization

### Establish and navigate bounded architecture

`speckit.concorde.init` creates module `module.md`, module `design.md`, the level view
`architecture/diagrams/level-view.json`, and config after approval. `context` builds one level from
summaries, every diagram of the level, contracts, and feature summary paths;
parent and sibling feature bodies and attempts remain unexpanded.

### Place, decompose, select, and specify work

A new root is created by specify at its canonical path. The command writes feature `design.md`, authors
`abstract.md`, seeds `implementation.md` only when absent, persists selection, and writes review state
under `attempt/checklists/`. Legacy `tldr.md`/`spec.md` names and `implementation/` directories are
rejected. Validation uses `CONCORDE-ABSTRACT-001..004` plus layout rules `005`, `007`, `008`, and `009`.

### Review, implement, validate, and publish

Planning reads feature `design.md` and `implementation.md`, uses the abstract for orientation and module
`module.md` as bounded context, and consults module `design.md` only deliberately. Normal phases write
only the active `attempt/` and reflection log. Publication opens on the abstract and provides Design
and Implementation companions while excluding every attempt.

### Ask about Concorde

The installed `ask` surface opens feature `design.md` for exact requirements, module `design.md` for
module rationale, and feature `implementation.md` for accepted realization, citing every file and
remaining read-only.

### Accept one selected lifecycle root

Proposal mode requires complete tasks and checklists and returns the Protocol v8 workspace and digest.
Proposal v4 uses `implementation.path == feature_implementation`, optional `module_design`, and a
single `remove == [attempt_dir]`. Apply stages feature `implementation.md` and optional module
`design.md`, moves the attempt aside, promotes atomically, restores on failure, and reports
`implementation_digest_before/after` plus module-design digests.

## Durable Implementation Decisions

- Feature `design.md` and `implementation.md` have distinct meanings; module `design.md` remains the
  module design reference. No compatibility alias or transition period exists.
- The feature abstract is an authored, self-contained document with exactly the five sections in order, a structure link (declared diagram, level view, delivered `/architecture/*.html` route) or a fenced text sketch, `Logic` citations resolving to `**FR-NNN**` definitions in the adjacent `design.md`, and a 3,000-word budget reported as a warning; it is written by specification and clarification only and never by acceptance, and where it disagrees with `design.md` the specification prevails and analysis reports the disagreement.
- `CONCORDE-ABSTRACT-003` fires on an unknown citation, or on no citation when the design defines at
  least one `**FR-NNN**`.
- Feature Workspace Protocol v8 is a closed schema with `feature_abstract`, `feature_design`,
  `feature_implementation`, `attempt_dir`, and `attempt_state`; acceptance proposals are v4 and Build
  Manifest is v7.
- The accepted realization is seeded as a placeholder at specification, written in full by the first acceptance, completed by later ones, keeps the six required headings first, and rejects the placeholder marker as candidate content.
- Acceptance promotes an ordered set of staged files and the attempt removal atomically with full rollback; the source digest binds `abstract.md` and both design references so a manual edit between review and apply is a `conflict`.
- The preset carries six templates; `abstract-template` and `implementation-template` resolve through
  the public preset stack; local helpers export `FEATURE_ABSTRACT`, `FEATURE_DESIGN`,
  `FEATURE_IMPLEMENTATION`, and `ATTEMPT_DIR`.
- Auto-Docs routes are registry-owned: abstract landing, `…/design`, and `…/implementation`.
- Self-hosted mirrors are regenerated through feature 004's codex-only tooling by setting both host integration records to codex (skills mode), running `propose` → `apply --proposal .specify/self-hosting-proposal.json` → `status --require-current`, backing up the regenerated codex skills, restoring the `claude` records, re-materializing the `claude` skills through `preset remove` + `preset add --dev` and `extension add --dev --force`, and restoring the codex skills; `.claude/skills` contains symlinks into `.agents/skills`, so it is regenerated rather than copied.
- The single core diagram remains an Archify `architecture` view whose intent node reads
  `abstract.md + design.md` and whose realization node reads `Feature Implementation / implementation.md`.
- Preset, extension, and bundle sources are 0.4.0; the private docsite generator remains 0.3.0.
  Release fixtures follow their own scenarios, and published catalogs are regenerated only from a
  complete component build.

## Traceability and Evidence

Behavior and acceptance criteria are in `design.md` and its nine sub-feature designs; the feature
abstract is adjacent. Project-level ownership and interactions are in `specs/concorde/module.md` and the
level view under `specs/concorde/architecture/diagrams/`; module rationale is in `specs/concorde/design.md`. Command behavior is governed
by `contracts/agent-commands.md`; Protocol v8/proposal v6 by `feature-workspace.schema.json`; the
documentation read model by the Auto-Docs contracts and Build Manifest v8.

Runtime realization is centered in `repository.py`, `feature_workspace.py`, `context.py`,
`implementation_acceptance.py`, `diagnostics.py`, and `validation/{abstract,diagrams,layout}.py`. Protocol and workspace
adapters emit schema version 8. Publication realization is in `docsite/plugins/concorde-content/`
and its Abstract · Design · Implementation companion navigation.

Executable evidence on 2026-08-29: 234 Python tests pass across unit, contract, integration, and
acceptance suites, including Protocol v8 routing, proposal v6 acceptance, legacy-name findings,
rollback, resume, installed surfaces, and all migrated fixtures. TypeScript compilation and all 77
Vitest tests pass, including an optimized production build. Content validation publishes 100 pages
with zero errors and 24 deliberate exclusions; Build Manifest v8 contains 21 feature abstracts, 21
feature designs, 21 feature implementations, 5 module designs, 21 architecture sources, and 10
project documents. All ten declared views pass the build-owned Archify gate.
`speckit.concorde.validate` returns `success` with zero findings.
The self-host apply refreshed Codex and Claude projections; status remains `unknown` while Claude is
the active integration because the self-host status protocol currently validates Codex only.

## Known Limitations

- The first-time-maintainer comprehension pilot (SC-005) and the human placement, mental-model, and acceptance-comprehension studies remain pending; automated evidence does not substitute for them.
- Browser containment and light/dark perceptual review of the delivered views remain pending because Chrome/Chromium is unavailable; showcase validation does not establish visual polish.
- The self-hosting tooling (feature 004) recognizes only the codex integration; under this checkout's active `claude` integration its `status` reports `unknown`.
- The three leaf modules record a `Structure` rationale instead of a level view; authoring their views is deferred.
- Feature 003's diagrams still label the 0.1.0 published inventory, and several module-level feature
  designs number requirements without `**FR-NNN**` identifiers, so their abstracts cite by section.
- The documentation site does not publish feature-root contract documents (`contracts/<name>.md`, schemas); widening that set is feature 002 scope.
- Compatibility is bounded to Spec Kit 0.16.4; deterministic validation cannot prove that a abstract or summary is well written or faithful, and the reading-budget proxies are advisory.
- The constitution's A.III relaxation of one providing module per feature remains a separately tracked follow-up; Protocol v8 still reports one `providing_module`.

## Implementation Detail

### Runtime

- `repository.py` discovers feature `design.md` authorities, feature `abstract.md` and
  `implementation.md` auxiliaries, module `design.md` references, and attempt files under `attempt/`.
- `feature_workspace.py` exposes `feature_abstract`, `feature_design`, `feature_implementation`,
  `attempt_dir`, and `attempt_state`; parent and sibling projections carry the same durable meanings.
- `validation/abstract.py` owns `REQUIRED_ABSTRACT_SECTIONS`, the 3,000-word budget, structure links,
  and FR citations; `validation/layout.py` owns trio, legacy-name, and selection findings.
- `implementation_acceptance.py` accepts proposal v6 `implementation`, updates only
  `feature_implementation`, optionally amends `module_design`, and removes only `attempt_dir`.
- `diagnostics.py` and `scripts/python/workspace.py` emit feature protocol schema version 8.

### Preset, extension, and helpers

- `preset.yml` lists `spec-template`, `abstract-template`, `implementation-template`,
  `reflections-template`, `plan-template`, `tasks-template`, and nine command replacements.
- `speckit.specify.md` resolves the three templates, authors the abstract after the specification, seeds `implementation.md` when absent, and adds three abstract checklist items; `speckit.clarify.md` updates the abstract after each integrated answer; `speckit.checklist.md` names the abstract as in scope; `speckit.plan.md`, `speckit.tasks.md`, `speckit.implement.md`, `speckit.converge.md`, and `speckit.taskstoissues.md` read the feature `implementation.md` as baseline and never write the trio; `speckit.analyze.md` adds the "abstract Disagreement" detection pass.
- Extension commands document proposal v6 and the `CONCORDE-ABSTRACT-*` / layout inventory.
- Local helpers export `FEATURE_ABSTRACT`, `FEATURE_DESIGN`, `FEATURE_IMPLEMENTATION`, and
  `ATTEMPT_DIR`.

### Auto-Docs site

- `registry.ts` declares `feature-abstracts`, `features`, and `feature-implementations`, pairs them by
  root, and excludes `attempt/**`; `manifest.ts` emits schema version 7.
- `CompanionLinks.tsx` renders Abstract · Design · Implementation with the current page unlinked.
- Fixtures model missing implementation, legacy names, missing/unpaired abstracts, unpaired
  implementations, and core-diagram embedding.

### Test map

- Unit and integration suites cover abstract rules, Protocol v8 paths, layout migration findings,
  proposal v6 acceptance, rollback, resume, and publication pairing.
- Contract and acceptance suites cover installed Codex/Claude surfaces, six templates, protocol
  examples, and clean-project installation.
- Docsite: `tests/unit/{registry,feature-designs,links}.test.ts`, `tests/contract/{build-manifest,content-sources}.test.ts`, `tests/integration/{feature-publication,production-build,performance,framework-guides}.test.ts`.
