---

description: "Dependency-ordered implementation tasks for the unified Concorde project docsite"
---

# Tasks: Create Unified Project Docsite

**Input**: Durable behavior from `../spec.md`, accepted realization from `../design.md`, feature contracts and diagrams at the root, and the current temporal attempt in `implementation/`

**Tests**: Required because this feature specifies deterministic discovery, link and route failures, source immutability, manifest repeatability, diagram publication, accessibility, and atomic build promotion.

**Organization**: Tasks retain the completed publication-engine history and append the current
reconciliation delta: an eight-page maintained Documentation baseline, progressive reader journey,
canonical-authority links, focused guide-contract evidence, and truthful participant status. The
accepted `../design.md` is not edited by these tasks.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it targets different files and has no dependency on an incomplete task
- **[Story]**: Maps the task to `US1` through `US5` from `../spec.md`
- Every task names exact maintained-source, implementation, test, or evidence paths

## Phase 1: Setup and Reconciliation Baseline

**Purpose**: Freeze the accepted design, resolve the feature-diagram decision, and migrate temporary review state before site changes begin.

- [X] T001 Verify that `specs/concorde/features/002-create-project-docsite/spec.md` records the bounded root `specs/concorde/architecture.json` as sufficient for the stable core component view and declares only `diagrams/project-docsite-publication-flow.json` as a `role: supplemental` Archify sequence
- [X] T002 Record the accepted-design digest, manifest v3 reconciliation scope, four source collections, three navigation families, and current evidence baseline in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T003 [P] Verify the locked Node.js, TypeScript, Docusaurus, Vitest, and Ajv toolchain in `docsite/package.json`, `docsite/package-lock.json`, `docsite/tsconfig.json`, and `docsite/vitest.config.ts`
- [X] T004 [P] Move `specs/concorde/features/002-create-project-docsite/checklists/requirements.md` to `specs/concorde/features/002-create-project-docsite/implementation/checklists/requirements.md` and retain no root checklist copy or symlink
- [X] T005 [P] Capture focused registry, feature-publication, manifest-schema, production-build, and source-immutability baseline results in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`

**Checkpoint**: Temporary checklist state is confined to `implementation/`, accepted design is unchanged, and the feature's no-core rationale plus supplemental sequence role are explicit.

---

## Phase 2: Foundational Architecture, Contracts, Types, and Fixtures

**Purpose**: Establish the unified source hierarchy, v3 publication contracts, shared types, and deterministic diagnostics that block all user stories.

- [X] T006 Reconcile the four maintained source collections and three navigation families in `specs/concorde/features/002-create-project-docsite/contracts/content-sources.md` and `specs/concorde/modules/documentation/contracts/project-content/contract.md`
- [X] T007 [P] Reconcile manifest v3 semantics, relative paths, feature spec/design pairing, exclusion records, routes, and freshness fields in `specs/concorde/features/002-create-project-docsite/contracts/build-manifest-contract.md` and `specs/concorde/modules/documentation/contracts/build-manifest/contract.md`
- [X] T008 [P] Update the normative manifest v3 schema and representative instance together in `specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json` and `specs/concorde/features/002-create-project-docsite/contracts/build-manifest.example.json`
- [X] T009 [P] Reconcile build failure, atomic promotion, provenance, feature-pair, and diagram publication obligations in `specs/concorde/features/002-create-project-docsite/contracts/build-interface.md` and `specs/concorde/features/002-create-project-docsite/contracts/published-site.md`
- [X] T010 Reconcile Documentation module ownership, boundary contracts, feature refinement, and publication evidence in `specs/concorde/modules/documentation/module.md` and `specs/concorde/modules/documentation/features/001-publish-project-docsite/spec.md`
- [X] T011 Reconcile the root and Documentation publication scenario IDs and governing contracts in `specs/concorde/architecture.json` and `specs/concorde/modules/documentation/architecture.json`
- [X] T012 [P] Define four-collection source, feature-specification, feature-design, pairing, page, navigation, diagram, exclusion, finding, and manifest-v3 types in `docsite/plugins/concorde-content/types.ts`
- [X] T013 [P] Seed paired specification/design, architecture, documentation, temporal implementation, and missing/duplicate design fixtures in `docsite/tests/fixtures/valid-project/` and `docsite/tests/fixtures/invalid-projects/`
- [X] T014 [P] Add Ajv schema/example, version, sorting, relative-path, route-inventory, feature-pair, exclusion, and repeatability contract tests in `docsite/tests/contract/build-manifest.test.ts`
- [X] T015 [P] Add source-classification, stable diagnostic, invalid-fixture, and project-root containment contract tests in `docsite/tests/contract/content-sources.test.ts`
- [X] T016 Implement stable error formatting, hierarchy, pairing, declared-view, route uniqueness, temporal exclusion, and sorted finding rules in `docsite/plugins/concorde-content/validation.ts`
- [X] T017 Implement clean architecture/features projection invariants for permanent specs and designs in `docsite/scripts/materialize-content.ts`
- [X] T018 Configure strict link, anchor, route, and Markdown failures plus Architecture, Documentation, and Features navigation shells in `docsite/docusaurus.config.ts`, `docsite/sidebars.architecture.ts`, `docsite/sidebars.docs.ts`, and `docsite/sidebars.features.ts`

**Checkpoint**: Contract examples validate as manifest v3, invalid source/pairing fixtures fail deterministically, and the site foundation recognizes four collections without writing maintained sources.

---

## Phase 3: User Story 1 - Browse the Whole Project in One Site (Priority: P1) 🎯 MVP

**Goal**: Publish Architecture, Documentation, and Features as three browsable/searchable families over four maintained source collections with canonical provenance and embedded declared diagrams.

**Independent Test**: Build a fixture containing module/contract Markdown, a delivered architecture view, nested docs, and two feature specification/design pairs; verify every eligible source appears exactly once, each pair is grouped, all three navigation families are searchable, and provenance points only to canonical `docs/` or `specs/` paths.

### Tests for User Story 1

- [X] T019 [P] [US1] Add four-collection registry, stable ordering, route uniqueness, feature-pair, hierarchy, and navigation completeness tests in `docsite/tests/unit/registry.test.ts`
- [X] T020 [P] [US1] Add architecture source identity, declared-view mapping, root-view sufficiency, and missing-delivery tests in `docsite/tests/unit/architecture-sources.test.ts`
- [X] T021 [P] [US1] Add landing-page, three-family navigation, four-collection provenance, feature-pair, diagram, route, and search smoke coverage in `docsite/tests/integration/production-build.test.ts`

### Implementation for User Story 1

- [X] T022 [US1] Implement deterministic module/contract, documentation, feature-specification, and feature-design discovery with canonical hashing and stable routes in `docsite/plugins/concorde-content/registry.ts`
- [X] T023 [US1] Implement clean Architecture and paired Features renderer projections while retaining canonical source paths in `docsite/scripts/materialize-content.ts`
- [X] T024 [US1] Configure projected Architecture, direct Documentation, paired projected Features, navigation entries, and all-family local search in `docsite/docusaurus.config.ts`, `docsite/sidebars.architecture.ts`, `docsite/sidebars.docs.ts`, and `docsite/sidebars.features.ts`
- [X] T025 [US1] Implement deterministic collection, page, feature-pair, architecture-view, lifecycle-status, navigation, exclusion, and route-inventory projection in `docsite/plugins/concorde-content/manifest.ts`
- [X] T026 [US1] Implement Docusaurus loading, global registry data, canonical source watches, rendered-route verification, and manifest v3 emission in `docsite/plugins/concorde-content/index.ts`
- [X] T027 [P] [US1] Present all three navigation families and four source-collection counts on the landing page in `docsite/src/pages/index.tsx` and `docsite/src/components/ProjectSummary.tsx`
- [X] T028 [P] [US1] Render canonical source kind, feature identity/status, specification/design relationship, and sandboxed Archify views in `docsite/src/components/ContentProvenance.tsx`, `docsite/src/components/ArchitectureView.tsx`, and `docsite/src/theme/DocItem/Layout/index.tsx`
- [X] T029 [P] [US1] Implement responsive navigation, feature-pair, status, provenance, and embedded-diagram styling in `docsite/src/css/custom.css`
- [X] T030 [US1] Run the User Story 1 registry and production checks and record inventory, pairing, search, provenance, and diagram results in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`

**Checkpoint**: The MVP publishes four canonical collections through three navigation families with one read-only page per source and no maintained copies in `docsite/`.

---

## Phase 4: User Story 2 - Author Documentation Outside the Site Project (Priority: P2)

**Goal**: Discover ordinary root `docs/` Markdown automatically with preserved hierarchy, formatting, and canonical link meaning.

**Independent Test**: Add, rename, link, and remove a nested fixture document without changing `docsite/`; rebuild and verify that navigation and cross-family links reflect only current canonical sources.

### Tests for User Story 2

- [X] T031 [P] [US2] Add documentation add, rename, remove, and hierarchy tests in `docsite/tests/integration/document-authoring.test.ts`
- [X] T032 [P] [US2] Add same-family, cross-family, specification/design, fragment, missing-target, excluded-target, and escaping-target link tests in `docsite/tests/unit/links.test.ts`
- [X] T033 [P] [US2] Add before/after SHA-256 immutability checks for canonical `docs/` and `specs/` sources in `docsite/tests/integration/source-immutability.test.ts`

### Implementation for User Story 2

- [X] T034 [US2] Implement canonical-path Markdown link classification, target validation, projection-to-canonical resolution, route rewriting, and fragment preservation in `docsite/plugins/concorde-content/links.ts`
- [X] T035 [US2] Integrate the shared link transformer and deterministic documentation hierarchy in `docsite/plugins/concorde-content/index.ts`, `docsite/docusaurus.config.ts`, and `docsite/sidebars.docs.ts`
- [X] T036 [P] [US2] Reconcile canonical project-documentation landing links with the published architecture and feature routes in `docs/index.md`
- [X] T037 [P] [US2] Document metadata, cross-family links, local preview, build projections, permanent design publication, temporal exclusions, and troubleshooting in `docs/contributing/docsite.md`
- [X] T038 [US2] Run the User Story 2 authoring, link, and immutability checks and append exact results to `specs/concorde/features/002-create-project-docsite/implementation/validation.md`

**Checkpoint**: A contributor changes only canonical `docs/`; the next build updates navigation and links without mutating either maintained source root.

---

## Phase 5: User Story 3 - Publish Canonical Feature Specifications and Designs (Priority: P3)

**Goal**: Publish every module-owned canonical `spec.md` with its paired permanent `design.md`, identity, ownership, status, provenance, and explicit exclusion of the temporal implementation workspace.

**Independent Test**: Change a nested fixture specification and design, add a child-module pair, and seed temporal checklists/plans/tasks; verify the next build updates only permanent feature pages, groups each pair, and records every `implementation/` Markdown source as excluded.

### Tests for User Story 3

- [X] T039 [P] [US3] Add root/nested feature ID, status, owner, specification/design pairing, hierarchy, missing-pair, and duplicate-ID cases in `docsite/tests/unit/feature-specifications.test.ts`
- [X] T040 [P] [US3] Add recursive permanent-pair inclusion plus complete `implementation/` and legacy-root-checklist exclusion tests in `docsite/tests/integration/feature-publication.test.ts`
- [X] T041 [P] [US3] Add manifest v3 `feature-specification` and `feature-design` source-kind, pairing, provenance, and exclusion assertions in `docsite/tests/contract/build-manifest.test.ts`

### Implementation for User Story 3

- [X] T042 [US3] Implement feature ID, module, title, lifecycle status, design title, pair identity, and canonical workspace extraction in `docsite/plugins/concorde-content/registry.ts`
- [X] T043 [US3] Implement recursive `**/spec.md` and paired `**/design.md` inclusion with stable grouped navigation in `docsite/sidebars.features.ts` and `docsite/docusaurus.config.ts`
- [X] T044 [P] [US3] Render stable ID, owning module, lifecycle status, source path, and paired-page relationship without implying implementation agreement in `docsite/src/components/ContentProvenance.tsx`
- [X] T045 [US3] Exclude every file under `implementation/` and record deterministic exclusion reasons in `docsite/plugins/concorde-content/registry.ts` and `docsite/plugins/concorde-content/manifest.ts`
- [X] T046 [US3] Update valid-project fixtures to use durable root `design.md` plus temporal `implementation/` artifacts in `docsite/tests/fixtures/valid-project/specs/`
- [X] T047 [US3] Run the User Story 3 unit, integration, and manifest tests and append pair counts, statuses, exclusions, and immutability evidence to `specs/concorde/features/002-create-project-docsite/implementation/validation.md`

**Checkpoint**: Every permanent feature specification/design pair is published once with traceable authority, while no temporal file is presented as durable feature content.

---

## Phase 6: User Story 4 - Verify a Reproducible Site Build (Priority: P4)

**Goal**: Supply inspect, validate, preview, test, and failure-safe production commands with verified routes, schema-valid manifest v3, deterministic projections, and atomic promotion.

**Independent Test**: Build unchanged sources twice and compare manifests; then inject broken links, invalid metadata, missing pairs, route collisions, stale diagrams, and candidate failures and verify each non-zero result preserves the previous successful `docsite/build/`.

### Tests for User Story 4

- [X] T048 [P] [US4] Add stable npm command, non-zero status, and actionable diagnostic contract tests in `docsite/tests/contract/build-interface.test.ts`
- [X] T049 [P] [US4] Add candidate failure, successful promotion, rollback, and stale-candidate tests in `docsite/tests/integration/atomic-promotion.test.ts`
- [X] T050 [P] [US4] Add real-repository route inventory, four-collection manifest, projection freshness, search asset, and repeatability tests in `docsite/tests/integration/production-build.test.ts`

### Implementation for User Story 4

- [X] T051 [US4] Implement canonical source inspection and validation entry points in `docsite/scripts/inspect.ts` and `docsite/scripts/validate.ts`
- [X] T052 [US4] Implement validation, projection recreation, clean candidate rendering, manifest-v3 verification, atomic promotion, rollback, and cleanup in `docsite/scripts/build.ts`
- [X] T053 [US4] Implement actual-route verification and successful manifest-v3 emission in `docsite/plugins/concorde-content/index.ts` and `docsite/plugins/concorde-content/manifest.ts`
- [X] T054 [US4] Wire `inspect`, `validate`, `prepare-content`, `start`, `test`, `build`, `typecheck`, and `check` interfaces in `docsite/package.json`
- [X] T055 [US4] Run the User Story 4 contract and integration suite twice and record atomicity, freshness, and identical-manifest evidence in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`

**Checkpoint**: Every command meets its contract, identical inputs yield identical manifests, and a failed candidate never replaces the last successful site.

---

## Phase 7: Supplemental Diagram, Accessibility, Scale, and Final Quality Gates

**Purpose**: Complete diagram source-to-page delivery and prove accessibility, scale, self-hosting, and source/projection agreement.

- [X] T056 [P] Add semantic landmark, keyboard navigation, responsive layout, provenance, feature-pair, and sandboxed-view accessibility assertions in `docsite/tests/integration/accessibility.test.ts`
- [X] T057 [P] Add a generated 1,000-document and 250-feature-pair discovery/validation performance fixture in `docsite/tests/integration/performance.test.ts`
- [X] T058 [P] Align the publication invocation, boundary information, candidate failure, and generated-output prose with durable contracts in `specs/concorde/features/002-create-project-docsite/spec.md` and `specs/concorde/features/002-create-project-docsite/contracts/`
- [X] T059 [P] Maintain the supplemental call-order source with complete scenario and contract traceability in `specs/concorde/features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json` without editing generated HTML as intent
- [X] T060 Validate the supplemental sequence with all Archify showcase checks and deliver fresh provenance-bearing output to `generated/architecture/project-docsite-publication-flow.html`
- [X] T061 Record truthful light/dark, containment, and browser perceptual-review status in `generated/architecture/project-docsite-publication-flow.visual-check.json` and `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T062 Verify automatic canonical Feature 002 page embedding, standalone-view linkage, provenance, and source/output freshness in `docsite/tests/integration/production-build.test.ts`
- [X] T063 Run every scenario in `specs/concorde/features/002-create-project-docsite/implementation/quickstart.md` and record commands, timings, source hashes, pair counts, exclusions, routes, and manifest digest in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T064 Run `npm run check`, Ajv schema/example validation, root and Documentation Archify checks, and `git diff --check`, then record exact automated evidence in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T065 Verify that `git status` contains no copied canonical content, generated site, cache, renderer projection, root checklist, or unexpected source mutation and record the audit in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [ ] T066 Conduct the SC-006 participant navigation exercise and record participants, timings, outcomes, and any unmet threshold in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T067 Reconcile automated and human status without inferring browser or participant evidence in `specs/concorde/features/002-create-project-docsite/spec.md` and `specs/concorde/features/002-create-project-docsite/implementation/validation.md`

**Checkpoint**: All deterministic checks pass, the supplemental sequence is fresh and embedded, canonical sources remain unchanged, and human evidence is reported truthfully.

---

## Phase 8: User Story 5 - Learn and Adopt Concorde from Maintained Guides (Priority: P2)

**Goal**: Publish a progressive eight-page Documentation baseline that teaches Concorde, directs
readers to the correct source authority and workflow operation, and remains ordinary recursively
discovered project documentation.

**Independent Test**: Starting from `docs/index.md`, verify that all six learning guides are directly
reachable, all eight baseline documents are published exactly once below `/docs`, normative summaries
link to included Architecture or Features authorities, and no temporal implementation artifact is
presented as permanent authority.

### Tests for User Story 5

- [X] T068 [P] [US5] Add eight-page inventory, stable routes, landing-page journey, canonical-authority-link, and temporal-authority assertions in `docsite/tests/integration/framework-guides.test.ts`

### Implementation for User Story 5

- [X] T069 [US5] Expand the Documentation view summary, progressive reading path, source-of-truth rule, and canonical Feature 001-003 links in `docs/index.md`
- [X] T070 [P] [US5] Add project-site preview, verified local bundle installation, first-feature commands, validation, and hardening boundaries in `docs/quick-start.md`
- [X] T071 [P] [US5] Explain Concorde's problem, spec-driven and Architecture-as-Code influences, bounded hierarchy, human/agent boundary, and adjacent-tool non-goals in `docs/framework-overview.md`
- [X] T072 [P] [US5] Explain module packages, durable feature specification/design, temporal attempts, hardening, contracts, and core-versus-supplemental diagrams in `docs/specification-model.md`
- [X] T073 [P] [US5] Map workflow control, installed payload, durable intent, temporary work, code/tests, generated projections, and correct edit locations in `docs/project-structure.md`
- [X] T074 [P] [US5] Document the end-to-end root, ownership, feature, specification, architecture-review, implementation, validation, hardening, and publication lifecycle in `docs/core-workflow.md`
- [X] T075 [P] [US5] Distinguish nine normal Spec Kit phases, six Concorde operations, integration presentation, workspace adapters, launchers, and deterministic runtime in `docs/commands.md`
- [X] T076 [P] [US5] Point repository readers to the maintained Documentation overview and quick start from `README.md`
- [X] T077 [US5] Reconcile framework-guide input and published-site guarantees across `specs/concorde/features/002-create-project-docsite/contracts/content-sources.md`, `specs/concorde/features/002-create-project-docsite/contracts/published-site.md`, `specs/concorde/modules/documentation/contracts/project-content/contract.md`, and `specs/concorde/modules/documentation/contracts/architecture-site/contract.md`
- [X] T078 [US5] Run the focused guide contract, registry validation, and production route checks and record the eight-page inventory and canonical-link results in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [ ] T079 [US5] Conduct the SC-011 and SC-012 participant artifact-classification and correct-edit/workflow exercises and record participant counts, outcomes, and thresholds in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T080 [US5] Reconcile automated and participant-dependent status without inferring human comprehension from build success in `specs/concorde/features/002-create-project-docsite/spec.md` and `specs/concorde/features/002-create-project-docsite/implementation/validation.md`

**Checkpoint**: The maintained guide baseline is complete and deterministically published; human
outcomes are either directly recorded or remain explicitly pending.

---

## Phase 9: Documentation Delta Final Quality Gates

**Purpose**: Verify the revised specification, plan, contracts, guide set, diagram strategy, and
generated read model agree without changing the accepted design.

- [X] T081 Verify the core-view sufficiency rationale, supplemental sequence role, aligned prose, declaration, fresh generated delivery, automatic embedding, and truthful visual status across `specs/concorde/features/002-create-project-docsite/spec.md`, `specs/concorde/features/002-create-project-docsite/diagrams/project-docsite-publication-flow.json`, `generated/architecture/project-docsite-publication-flow.html`, and `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T082 Run `npm run check` from `docsite/` and record test, page, exclusion, link, route, manifest, and production-build results in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T083 Run targeted Concorde validation for `feature.concorde.publish-project-docsite` and `git diff --check`, then record zero-finding or actionable failure evidence in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`
- [X] T084 Verify the accepted `specs/concorde/features/002-create-project-docsite/design.md` digest is unchanged and audit `git status` for generated-site, cache, projection, copied-source, or unexpected mutations in `specs/concorde/features/002-create-project-docsite/implementation/validation.md`

**Checkpoint**: All automatable Feature 002 documentation work and deterministic gates are complete;
only directly observed participant evidence may remain open.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and resolves checklist and diagram-role debt.
- **Foundation (Phase 2)**: Depends on Setup and blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundation and delivers the four-collection/three-family MVP.
- **US2 (Phase 4)**: Depends on US1's registry and routing foundation.
- **US3 (Phase 5)**: Depends on US1's registry/projection foundation and may proceed in parallel with US2.
- **US4 (Phase 6)**: Command and atomic-build work may begin after US1; final all-content verification depends on US2 and US3.
- **Quality gates (Phase 7)**: Depend on all desired story checkpoints.
- **US5 reconciliation (Phase 8)**: Uses the completed US1/US2 publication and authoring foundation;
  its guide files and focused test can be authored in parallel before contract/evidence reconciliation.
- **Documentation delta gates (Phase 9)**: Depend on the US5 automated work and truthful manual status.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 (MVP) -> US2 --------|
                              |-> US3 ---------|-> US4 -> Quality gates
                              `-> US4 command -'
Completed publication baseline -> US5 guide delta -> Documentation delta gates
```

### Parallel Opportunities

- T003-T005, T007-T009, T012-T015, T019-T021, T027-T029, T031-T033, T036-T037, T039-T041, T048-T050, and T056-T059 target independent files or fixtures.
- After US1, documentation authoring work in US2 and feature-pair publication work in US3 may proceed in parallel.
- T068 and T070-T076 target separate test/documentation files and may proceed in parallel before
  T077-T080 reconcile contracts and evidence.

## Parallel Example: User Story 3

```text
Task T039: feature identity and pair tests in docsite/tests/unit/feature-specifications.test.ts
Task T040: permanent inclusion and temporal exclusion tests in docsite/tests/integration/feature-publication.test.ts
Task T041: manifest v3 feature-kind and pairing tests in docsite/tests/contract/build-manifest.test.ts
```

## Parallel Example: User Story 5

```text
Task T068: framework-guide contract tests in docsite/tests/integration/framework-guides.test.ts
Task T070: quick start in docs/quick-start.md
Task T071: framework overview in docs/framework-overview.md
Task T072: specification model in docs/specification-model.md
Task T073: project structure in docs/project-structure.md
Task T074: core workflow in docs/core-workflow.md
Task T075: command reference in docs/commands.md
Task T076: repository entry points in README.md
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 through T030.
3. Stop and demonstrate Architecture, Documentation, and paired Features with provenance, search, and embedded views.

### Incremental Delivery

1. Add US2 copy-free documentation authoring and cross-family links.
2. Add US3 permanent specification/design pairing and temporal exclusion.
3. Add US4 deterministic, failure-safe maintainer commands and manifest v3.
4. Complete the supplemental diagram lifecycle, accessibility, scale, self-hosting, and human evidence gates.
5. Add the US5 framework-guide baseline and rerun the documentation delta quality gates.

## Notes

- `../design.md` is the immutable accepted baseline for this attempt.
- Module/contract Markdown, feature `spec.md`, feature `design.md`, Archify JSON, code, tests, and generated projections retain distinct authority.
- `docsite/.generated/`, `docsite/build/`, and generated diagram HTML are disposable outputs and never maintained intent.
- Browser perceptual and participant-navigation outcomes remain pending until directly observed.
- Automated guide publication is not evidence that SC-006, SC-011, or SC-012 participant thresholds
  have been met.
