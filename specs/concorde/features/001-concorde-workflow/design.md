# Feature Design: Concorde Workflow

**Feature**: `feature.concorde.workflow`

**Design status**: Accepted realization of the architecture-aware Spec Kit workflow, including exactly two feature-containment levels, durable feature design, root-local temporal implementation attempts, bounded architecture services, deterministic validation, review-first hardening, generated documentation, and a distributed read-only question surface.

## Realization Overview

Concorde preserves Spec Kit as the owner of specification, clarification, planning, tasks, implementation, analysis, convergence, and task-to-issue conversion. Around that lifecycle it adds reviewed module ownership, feature placement, one optional level of first-class sub-features, selected-workspace routing, bounded context, deterministic architecture validation, feature-owned diagrams, approval-gated design hardening, and source-grounded workflow help.

A lifecycle root is either a top-level feature at `features/<number-name>/` or one immediate sub-feature at `features/<number-name>/subfeatures/<number-name>/`. Both use `kind: feature`, a stable `feature.*` ID, their own `spec.md`, `design.md`, optional contracts and diagrams, and at most one `implementation/` attempt. A parent registers ordered `subfeatures`; each child declares `parent_feature`, inherits the parent module, owns one focused `## Outcome`, and cannot contain another child. This containment model is independent of adjacent-module `refines` links.

The parent specification owns the aggregate outcome, shared vocabulary and invariants, cross-child relationships, and decomposition rationale. A child specification owns only its focused behavior. When a child is selected, its own durable and temporal paths are authoritative for the phase; the parent spec/design is read-only aggregate context and siblings are concise summaries rather than opened bodies or attempts.

The project keeps one standard selection pointer in `.specify/feature.json`. Feature Workspace Protocol v3 derives the selected ID, level, providing module, durable/temporal paths, nullable parent context, and bounded sibling summaries from validated maintained sources. No parallel registry or second feature lifecycle exists.

## Module and Feature Collaboration

- `module.concorde.spec-kit-integration` provides `contract.integration.feature-workspace`, normal-command composition, installed agent surfaces, Protocol v3 resolution and routing of the standard Spec Kit feature selection, and the read-only question procedure. Its lower-module feature `feature.integration.manage-feature-workspace` continues to refine the root workflow architecturally; that refinement is not feature containment.
- `module.concorde.architecture-core` owns source discovery, safe path classification, bounded context, readiness, and deterministic validation through `contract.core.architecture-services`. It validates module containment, feature refinement, and feature containment as separate acyclic graphs.
- `module.concorde.documentation` consumes validated durable sources through the Documentation contracts. Build Manifest v4 records parent/child relationships, and the generated site renders ordered child summaries plus parent/sibling navigation without copying requirements or publishing attempts.
- `module.concorde.distribution` packages the unchanged inventory of four preset templates, nine normal phase replacements, five Concorde surfaces, and four portable scripts. It owns archive/catalog mechanics, while Feature 001 owns the workflow semantics they carry.

The `concorde-core` preset routes all nine path-sensitive Spec Kit phases through the installed workspace adapter before artifact access. Every phase writes only beneath the selected root. For a sub-feature, commands may read the Protocol v3 parent durable paths as aggregate context but never implicitly read or write parent/sibling attempts.

The `concorde` extension retains five command surfaces. Four—`init`, `context`, `validate`, and `feature-harden`—reach the standard-library Python runtime through project-relative launchers. `ask` remains agent-followed and read-only. Feature creation and selection are standard Spec Kit behavior rather than Concorde commands; hardening accepts either valid lifecycle level.

## Scenario Realization

### Establish and navigate bounded architecture

Initialization, context, and validation load `.concorde/config.json` and the recursive specification package. Module context still exposes only the current module, immediate submodules, current-level features and contracts, permitted externals, scenarios, and stable deeper references. Feature containment is projected separately: a parent returns immediate child summaries in authored order, while a requested child returns its parent and concise siblings. No sibling body, third feature level, lower-module feature body, grandchild module, or unrelated attempt is expanded.

### Place, decompose, select, and specify work

A new top-level feature or immediate sub-feature is created by the normal Spec Kit specify phase with `SPECIFY_FEATURE_DIRECTORY` set to `<module directory>/features/NNN-<short-name>` or `<parent feature root>/subfeatures/NNN-<short-name>`; the preset's specify addendum seeds `spec.md` and the adjacent `design.md` (stating that no realization is hardened yet) and persists the root to `.specify/feature.json`. The author records `id`, `module`, and, for a child, `parent_feature` in the spec front matter and registers the root in the module's or parent's feature list. No Concorde creation command exists: child-as-parent registration, invalid depth, duplicate identity, module disagreement, and unsafe or non-canonical paths are rejected by deterministic validation and by workspace resolution rather than by a proposal step.

Selection is the standard Spec Kit `.specify/feature.json` `feature_directory` record, written by specify or set through `SPECIFY_FEATURE_DIRECTORY`; Concorde adds no selection command and no second store. Before every normal phase the workspace adapter resolves that root, validates its exact path grammar and real spec/design pair, checks module registration for a top-level feature or bidirectional parent registration/module inheritance for a child, and reports a non-empty attempt as `implementation_state: active`. The workspace adapter returns Protocol v3 fields and routes durable phases to the selected root and implementation phases to that root's `implementation/`.

### Review, implement, validate, and publish

Architecture readiness reports selected level, parent/sub-feature relationships, providing module, refinements, contracts, participating children, affected views, dependency direction, and expected evidence without conflating containment with refinement. Planning treats the selected `design.md` as the accepted baseline and, for a child, the parent durable pair as read-only aggregate context.

Repository discovery accepts only canonical top-level and immediate-sub-feature specifications and reports malformed feature-like paths instead of silently ignoring them. Deterministic `CONCORDE-CONTAIN-*` and layout rules cover metadata shape, identity, bidirectional registration, module inheritance, canonical depth, cycles, required child outcomes, top-level/child module registration, selection safety, symlinks, and forbidden descendants.

The documentation registry resolves relationships after parsing all sources. The canonical parent page lists each child once in authored order with stable ID, title, source-owned outcome, status, and route. Child specification and paired design pages link to their parent and siblings. Build Manifest v4 carries the same relationship metadata; all `implementation/**` artifacts remain excluded.

### Ask about Concorde

The installed `ask` surface grounds answers in installed extension/preset guidance first and then the smallest relevant maintained project context. It distinguishes two-level containment from adjacent-module refinement. For a sub-feature question it may read the selected child and parent durable pair plus sibling summaries, but it does not read sibling bodies or parent/sibling attempts merely because they exist. Answers cite their basis, label inference and uncertainty, and never invoke a runtime operation or mutate the workspace.

### Harden one selected lifecycle root

Proposal mode resolves the selected parent or child, requires at least one recognizable task, requires every task and existing checklist item to be complete and well formed, and returns the exact proposal path, source digest, selected design target, and whole-attempt removal target. Eligibility never grants approval.

Apply re-resolves classification, parent relationships, task/checklist state, symlinks, target confinement, and digest. It accepts only the selected root's `design.md` and complete `implementation/`, stages a recoverable design replacement and attempt move, and commits both or restores both. Child hardening retains parent and sibling durable authorities; parent hardening does not rewrite or remove any child attempt.

## Durable Implementation Decisions

- Feature containment is exactly two levels and uses the existing feature source kind with `subfeatures` and `parent_feature` metadata.
- Parent/child containment and adjacent-module refinement are distinct relationships with separate projections and diagnostics.
- One `.specify/feature.json` pointer selects exactly one feature-shaped lifecycle root; relationship context is derived rather than duplicated into control state.
- Feature Workspace Protocol v3 is a closed schema containing selected kind/ID/module, nullable parent durable context, bounded sibling summaries, and selected-root paths.
- Every lifecycle root independently owns its durable spec/design and at most one temporal attempt. Parent and sibling attempt paths are never implicit child inputs.
- Semantic simplicity and non-duplication between parent and child prose remain human requirements-quality judgments; deterministic validation enforces reproducible structural facts only.
- The normal command inventory remains nine Spec Kit phase surfaces plus five Concorde surfaces; no `subfeature.create` namespace, Concorde creation/selection command, or second orchestrator is introduced.
- The documentation contract uses Build Manifest v4 and page-level relationship navigation; generated pages link canonical sources instead of copying their normative text.
- Hardening eligibility and authorization remain separate. Normal phases never update `design.md` or remove `implementation/`.
- Installed preset/extension sources are primary; self-hosted `.specify/` and `.agents/skills/` materializations are verified mirrors. The custom replace-owned design template remains resolved from the preset under Spec Kit 0.16.4.
- The single Feature 001 core diagram remains an Archify `architecture` view. Its Archify 2.16 migration groups project-relative launchers with the Python runtime as one readable execution boundary without merging their implementation responsibilities. Generated HTML, catalogs, receipts, and manifests are reproducible evidence/read models, not maintained intent.

## Traceability and Evidence

Behavior and acceptance criteria remain in `specs/concorde/features/001-concorde-workflow/spec.md`. Root ownership and current-level interactions remain in `specs/concorde/module.md` and `specs/concorde/architecture.json`. Command behavior is governed by `contracts/agent-commands.md`; maintained-source semantics by `contracts/architecture-sources.md`; Protocol v3 by `contracts/feature-workspace.schema.json` and its examples.

Runtime realization is centered in:

- `extensions/concorde/runtime/concorde/repository.py` for canonical two-level discovery and path classification;
- `feature_workspace.py` and `cli.py` for Protocol v3 resolution of the standard selection, relationship context, and phase paths;
- `context.py`, `readiness.py`, `validate.py`, and `validation/layout.py` for bounded projections and deterministic containment diagnostics;
- `feature_hardening.py` for classified-root eligibility, atomic apply, and retained parent/sibling authorities; and
- `diagnostics.py` plus `scripts/python/workspace.py` for versioned canonical envelopes.

Publication realization is in `docsite/plugins/concorde-content/`, `FeatureRelations.tsx`, provenance/layout integration, and Build Manifest v4 contracts. Parent/child fixtures cover relationship ordering, navigation, invalid registration, and attempt exclusion.

Executable evidence includes 134 passing Python unit, contract, integration, acceptance, clean-install, self-hosting, and release tests. Tests cover exact two-level discovery, third-level rejection, child selection, all nine selected-child phase routes, bounded parent/sibling context, containment diagnostics, parent/sibling-preserving child hardening, Codex/slash installed parity, checkout independence, and deterministic release catalogs.

The documentation gate passed TypeScript compilation, 18 Vitest files with 49 tests, validation of 66 pages with 21 temporal/noncanonical sources excluded and zero errors, and an optimized production build. Concorde validation completed with zero findings; its aggregate source digest remains execution evidence rather than self-referential maintained prose.

The Feature 001 core diagram passed all nine Archify 2.16 showcase checks with zero composition errors or warnings. Its maintained specification digest is `1cf5638e85132f5fb4c8d3c00cca61f0689b515c0ef797b52958384ff16bb12d`; the delivered HTML digest is `84c83070935d3e5074c32c13c8c67fb18d17e51f972d062a5cd7ea29b8befeb3`.

Self-host status is current with source, installed bytes, registries, and declared surfaces matching. Verified release archives are:

- `concorde-0.1.0.zip`: `sha256:271e20191d090251c9272798cec404929acd167cf7f3d3d97940d7f3dea3b4da`
- `concorde-core-0.1.0.zip`: `sha256:08df5ad9d49d2af557b786dc30504f9666d3b09d7cce23f077f1fbdda6ffe94d`
- `concorde-bundle-0.1.0.zip`: `sha256:ae0079f5e78b89bbb30eaa46279f036553395f1be1c94f9af8de962ab0670608`

## Known Limitations

- First-time-maintainer studies for module placement, parent-versus-child authority, containment-versus-refinement comprehension, workflow mental models, Q&A usability, and hardening comprehension remain pending; automated tests do not substitute for human evidence.
- Browser containment captures and light/dark perceptual review of the updated Feature 001 diagram remain pending because Chrome/Chromium was unavailable. Showcase validation does not establish visual polish.
- Compatibility is intentionally bounded to Spec Kit 0.16.4. Supporting another host version requires renewed review of all replaced commands, templates, registration behavior, Protocol v3 consumers, and installed-project matrices.
- Deterministic validation cannot prove that parent and child prose are semantically simple or non-duplicative; that remains a reviewed requirements-quality responsibility.
- Architecture validity, publication success, installed-surface parity, and passing workflow tests do not prove arbitrary application implementation correctness. Missing or conflicting code/test evidence remains unknown or disagreement.
- Feature 002 and Feature 003 accepted designs were not rewritten by this Feature 001 attempt. Their durable realization narratives require their own completed attempts and explicit hardening when reconciliation is desired.
