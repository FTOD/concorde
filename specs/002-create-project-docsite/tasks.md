---
description: "Dependency-ordered implementation tasks for the unified Concorde project docsite"
---

# Tasks: Create Unified Project Docsite

**Input**: Design documents from `specs/002-create-project-docsite/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and
`quickstart.md`

**Tests**: Test-first tasks are required by the plan, publication contracts, success criteria, and
Concorde constitution. Run each named test before its corresponding implementation and confirm that a
new behavior test fails for the expected reason.

**Organization**: Setup and architecture foundations block all stories. Story phases then deliver the
P1–P4 user journeys in priority order while retaining independent acceptance checkpoints.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: May run in parallel because it targets different files and has no dependency on another
  incomplete task in the same group.
- **[Story]**: Maps the task to a user story in `spec.md`.
- Every task names its implementation or evidence path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the independent Node/TypeScript site project and safe repository boundaries.

- [X] T001 Add Node, Docusaurus, generated-site, environment, editor, and OS exclusions to `.gitignore`
- [X] T002 Create private locked Docusaurus 3.10.2 project metadata and install the planned runtime/dev dependencies in `docsite/package.json` and `docsite/package-lock.json`
- [X] T003 [P] Configure strict TypeScript and Vitest environments in `docsite/tsconfig.json` and `docsite/vitest.config.ts`
- [X] T004 [P] Create the site/plugin/test directory skeleton with exported placeholder modules in `docsite/plugins/concorde-content/index.ts` and `docsite/tests/setup.ts`
- [X] T005 Verify the independent package boundary and document prerequisite versions in `docsite/README.md`

**Checkpoint**: `cd docsite && npm ci` succeeds from the lockfile and produces no tracked output.

---

## Phase 2: Foundational Architecture and Contracts

**Purpose**: Resolve ownership, contracts, bounded views, shared types, and contract fixtures before
user-facing implementation.

**Critical**: No user-story implementation begins until this phase passes its architecture and test
checkpoint.

- [X] T006 [P] Register `feature.concorde.publish-project-docsite`, its canonical spec, and the publication contract at the root level in `architecture/concorde/module.md`
- [X] T007 [P] Add the adjacent Documentation refinement and link it only to the root feature in `architecture/concorde/modules/documentation/features/publish-project-docsite.md`
- [X] T008 Split and reconcile the Documentation source, build, manifest, and published-site boundaries from the design contracts into `architecture/concorde/modules/documentation/contracts/project-content/contract.md`, `architecture/concorde/modules/documentation/contracts/build-interface/contract.md`, `architecture/concorde/modules/documentation/contracts/build-manifest/contract.md`, and `architecture/concorde/modules/documentation/contracts/architecture-site/contract.md`
- [X] T009 Update Documentation feature/contract declarations and evidence links in `architecture/concorde/modules/documentation/module.md`
- [X] T010 Add the bounded Documentation publication scenario and governing contract references in `architecture/concorde/modules/documentation/architecture.json`, then reconcile the root publication trace in `architecture/concorde/architecture.json`
- [X] T011 Validate and render both maintained architecture views with Archify, writing generated output and receipts to `generated/architecture/documentation.html`, `generated/architecture/documentation.visual-check.json`, and `generated/architecture/concorde-root.html`
- [X] T012 [P] Define SourceCollection, SourceDocument, ProjectDocument, FeatureSpecification, LinkReference, ContentPage, NavigationEntry, ExcludedSource, ValidationFinding, and BuildManifest types in `docsite/plugins/concorde-content/types.ts`
- [X] T013 [P] Seed valid and invalid documentation/specification contract fixtures in `docsite/tests/fixtures/valid-project/` and `docsite/tests/fixtures/invalid-projects/`
- [X] T014 [P] Add a schema/example conformance test for `specs/002-create-project-docsite/contracts/build-manifest.schema.json` in `docsite/tests/contract/build-manifest.test.ts`
- [X] T015 [P] Add source-format, path-containment, identity, and diagnostic-shape contract tests in `docsite/tests/contract/content-sources.test.ts`
- [X] T016 Implement stable error formatting and sorted validation findings in `docsite/plugins/concorde-content/validation.ts`
- [X] T017 Configure two external-path docs instances, strict link/route failures, disabled blog/update timestamps, and local search in `docsite/docusaurus.config.ts`, `docsite/sidebars.docs.ts`, and `docsite/sidebars.features.ts`

**Checkpoint**: Architecture views validate, contract examples pass their schema, and deliberately
invalid fixtures fail with stable rule/source/remediation diagnostics.

---

## Phase 3: User Story 1 — Browse the Whole Project in One Site (Priority: P1) — MVP

**Goal**: Build one coherent site with distinct Documentation and Features sections, project-wide
discovery, source provenance, and a useful landing page.

**Independent Test**: Build the valid fixture containing nested docs and two feature specs; verify all
eligible pages are reachable once through `/docs` or `/features`, searchable, and visibly traceable to
their sources.

### Tests for User Story 1

- [X] T018 [P] [US1] Write failing registry, route uniqueness, stable ordering, and navigation completeness tests in `docsite/tests/unit/registry.test.ts`
- [X] T019 [P] [US1] Write a failing landing-page, dual-navigation, provenance, and local-search production smoke test in `docsite/tests/integration/production-build.test.ts`

### Implementation for User Story 1

- [X] T020 [US1] Implement deterministic discovery, Markdown/front-matter parsing, SHA-256 hashing, title extraction, route derivation, and stable sorting in `docsite/plugins/concorde-content/registry.ts`
- [X] T021 [US1] Implement duplicate identity, missing metadata, outside-root path, and route-collision validation in `docsite/plugins/concorde-content/validation.ts`
- [X] T022 [US1] Implement deterministic collection/page/navigation projection against the normative schema in `docsite/plugins/concorde-content/manifest.ts`
- [X] T023 [US1] Implement Docusaurus `loadContent`, `contentLoaded`, global registry data, and source-watch integration in `docsite/plugins/concorde-content/index.ts`
- [X] T024 [P] [US1] Build the project landing page and collection summary in `docsite/src/pages/index.tsx` and `docsite/src/components/ProjectSummary.tsx`
- [X] T025 [P] [US1] Add the shared project-document/feature provenance banner and DocItem wrapper in `docsite/src/components/ContentProvenance.tsx` and `docsite/src/theme/DocItem/Layout/index.tsx`
- [X] T026 [P] [US1] Implement responsive project branding, navigation, content-kind, status, and provenance styling in `docsite/src/css/custom.css`
- [X] T027 [US1] Run the User Story 1 unit and production smoke tests and record the MVP results in `specs/002-create-project-docsite/validation.md`

**Checkpoint**: The fixture site presents both collections from one landing page, every included page
has one navigation entry and provenance banner, and local search returns both content kinds.

---

## Phase 4: User Story 2 — Author Documentation Outside the Site Project (Priority: P2)

**Goal**: Make ordinary root `docs/` Markdown automatically discoverable with preserved hierarchy,
formatting, and repository-relative links, without copies or manual registration.

**Independent Test**: Add, rename, link, and remove a nested fixture document without changing
`docsite/`; rebuild and verify that navigation and links reflect only the current canonical sources.

### Tests for User Story 2

- [X] T028 [P] [US2] Write failing add/rename/remove and hierarchical navigation tests for root documentation in `docsite/tests/integration/document-authoring.test.ts`
- [X] T029 [P] [US2] Write failing same-collection, cross-collection, fragment, missing-target, excluded-target, and escaping-target tests in `docsite/tests/unit/links.test.ts`
- [X] T030 [P] [US2] Write a failing validation/build source-immutability test for root documentation in `docsite/tests/integration/source-immutability.test.ts`

### Implementation for User Story 2

- [X] T031 [US2] Implement registry-backed Markdown link classification, validation, cross-instance route rewriting, and fragment preservation in `docsite/plugins/concorde-content/links.ts`
- [X] T032 [US2] Integrate the shared link transformer and deterministic documentation hierarchy into `docsite/plugins/concorde-content/index.ts` and `docsite/sidebars.docs.ts`
- [X] T033 [P] [US2] Create the canonical project-documentation landing content with a source-relative feature link in `docs/index.md`
- [X] T034 [P] [US2] Document Markdown metadata, links, local preview, build, and troubleshooting for contributors in `docs/contributing/docsite.md`
- [X] T035 [US2] Run the User Story 2 authoring, link, and immutability tests and append results to `specs/002-create-project-docsite/validation.md`

**Checkpoint**: A contributor changes only `docs/`; the next build adds/removes the corresponding page
and links while leaving both canonical source trees unchanged.

---

## Phase 5: User Story 3 — Publish Canonical Feature Specifications (Priority: P3)

**Goal**: Publish every canonical `spec.md` with current title, stable ID, owner, status, provenance,
and explicit exclusion of other Spec Kit artifacts.

**Independent Test**: Change a fixture feature title/status/requirement and add a new feature directory;
verify the next build updates only canonical feature pages and records plans/tasks/checklists as
excluded.

### Tests for User Story 3

- [X] T036 [P] [US3] Write failing feature discovery, identity/status extraction, recursive feature-directory, and duplicate-ID tests in `docsite/tests/unit/feature-specifications.test.ts`
- [X] T037 [P] [US3] Write failing canonical-only inclusion, exclusion-manifest, and no-source-write integration tests in `docsite/tests/integration/feature-publication.test.ts`

### Implementation for User Story 3

- [X] T038 [US3] Implement feature ID, kind, module, title, lifecycle-status, and feature-directory extraction in `docsite/plugins/concorde-content/registry.ts`
- [X] T039 [US3] Implement canonical `**/spec.md` inclusion, stable feature labels, and nested feature navigation in `docsite/sidebars.features.ts` and `docsite/docusaurus.config.ts`
- [X] T040 [P] [US3] Render stable ID, owning module, draft/final status, and source path without implying approval in `docsite/src/components/ContentProvenance.tsx`
- [X] T041 [US3] Add deterministic `not-canonical-feature-artifact` discovery and excluded-source manifest records in `docsite/plugins/concorde-content/registry.ts` and `docsite/plugins/concorde-content/manifest.ts`
- [X] T042 [US3] Run the User Story 3 unit and integration tests and append results to `specs/002-create-project-docsite/validation.md`

**Checkpoint**: Every canonical feature spec is published once with identity/status/provenance, and no
plan, task list, or checklist is represented as a feature specification.

---

## Phase 6: User Story 4 — Verify a Reproducible Site Build (Priority: P4)

**Goal**: Supply inspect, validate, preview, test, and failure-safe production commands with verified
routes, schema-valid manifests, deterministic outcomes, and atomic promotion.

**Independent Test**: Build unchanged sources twice and compare manifests, then inject each invalid
fixture and verify a non-zero actionable failure leaves the last successful `docsite/build/` intact.

### Tests for User Story 4

- [X] T043 [P] [US4] Write failing npm command/exit-status and actionable-diagnostic contract tests in `docsite/tests/contract/build-interface.test.ts`
- [X] T044 [P] [US4] Write failing candidate failure, successful promotion, rollback, and stale-candidate tests in `docsite/tests/integration/atomic-promotion.test.ts`
- [X] T045 [P] [US4] Extend runtime manifest schema, sorting, route-inventory, relative-path, and repeatability tests in `docsite/tests/contract/build-manifest.test.ts`

### Implementation for User Story 4

- [X] T046 [US4] Implement source inspection and validation command entry points in `docsite/scripts/inspect.ts` and `docsite/scripts/validate.ts`
- [X] T047 [US4] Implement clean candidate rendering, post-build verification, atomic promotion, previous-output preservation, and failure cleanup in `docsite/scripts/build.ts`
- [X] T048 [US4] Implement actual-route verification and successful manifest emission in `docsite/plugins/concorde-content/index.ts` and `docsite/plugins/concorde-content/manifest.ts`
- [X] T049 [US4] Wire `inspect`, `validate`, `start`, `test`, `build`, `typecheck`, and `check` interfaces in `docsite/package.json`
- [X] T050 [US4] Add real-repository build, route inventory, search asset, manifest, and repeatability coverage in `docsite/tests/integration/production-build.test.ts`
- [X] T051 [US4] Run the User Story 4 contract/integration suite twice and append atomicity and manifest comparison results to `specs/002-create-project-docsite/validation.md`

**Checkpoint**: All build-interface commands meet their contract, unchanged builds yield identical
manifests, and every failed candidate preserves the previous successful output.

---

## Phase 7: Polish and Cross-Cutting Quality Gates

**Purpose**: Prove accessibility, scale, self-hosting, architecture freshness, and full-spec agreement.

- [X] T052 [P] Add semantic landmark, keyboard navigation, responsive layout, and provenance accessibility assertions in `docsite/tests/integration/accessibility.test.ts`
- [X] T053 [P] Add a generated 1,000-document/250-feature discovery and validation performance fixture test in `docsite/tests/integration/performance.test.ts`
- [X] T054 Reconcile contributor commands and observed outputs with the build-interface contract in `docsite/README.md` and `docs/contributing/docsite.md`
- [X] T055 Run every scenario in `specs/002-create-project-docsite/quickstart.md` and record command results, timing, source-immutability, and manifest hashes in `specs/002-create-project-docsite/validation.md`
- [X] T056 Re-run root and Documentation Archify validation, regenerate site/diagram projections, and update architecture evidence status in `architecture/concorde/module.md` and `architecture/concorde/modules/documentation/module.md`
- [X] T057 Run `npm run check`, verify all 26 functional requirements and 8 success criteria, and record the final requirement-to-evidence matrix in `specs/002-create-project-docsite/validation.md`
- [X] T058 Verify `git status` contains no generated site, cache, copied canonical content, or unexpected source mutation and record the clean-output audit in `specs/002-create-project-docsite/validation.md`

**Checkpoint**: All deterministic tests and builds pass, architecture/documentation projections are
fresh, canonical sources remain authoritative, and the validation record maps every requirement to
evidence.

---

## Phase 8: Architecture Publication Extension

**Purpose**: Publish Concorde's maintained architecture as the third canonical site collection.

- [X] T059 Add Architecture collection types, recursive discovery, stable-ID validation, route mapping,
  manifest projection, and watch paths in `docsite/plugins/concorde-content/`
- [X] T060 Add the third Docusaurus docs instance, architecture sidebar/navbar/search configuration,
  and landing summary in `docsite/`
- [X] T061 Add sandboxed declared-view embedding and architecture provenance in
  `docsite/src/components/` and the shared DocItem wrapper
- [X] T062 Upgrade the content, published-site, and build-manifest contracts to version 2 and update
  the normative schema and representative example under `specs/002-create-project-docsite/contracts/`
- [X] T063 Reconcile root and Documentation architecture prose and views, then validate and deliver
  both Archify artifacts with showcase quality
- [X] T064 Extend registry, accessibility, immutability, manifest, and production-build evidence for
  Architecture and rerun `npm run check`

**Checkpoint**: Architecture Markdown is directly browsable and searchable, each declared structural
view is embedded from its delivered projection, all three authorities retain provenance, and the
complete Docusaurus gate passes.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: Starts immediately.
- **Phase 2 — Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 — US1**: Depends on Phase 2 and delivers the MVP site shell and shared content pipeline.
- **Phase 4 — US2**: Depends on US1's shared registry/plugin; independently tests the `docs/` journey.
- **Phase 5 — US3**: Depends on US1's shared registry/plugin; may run in parallel with US2.
- **Phase 6 — US4**: Depends on the US1 pipeline. Command/atomic work may run beside US2/US3, but its
  final production test depends on both content collections being complete.
- **Phase 7 — Polish**: Depends on all selected stories.
- **Phase 8 — Architecture Publication**: Extends the completed publication boundary and depends on
  the delivered root and Documentation Archify views.

### User Story Dependency Graph

```text
Setup -> Architecture/Foundation -> US1 (MVP)
                                  ├-> US2 ─┐
                                  ├-> US3 ─┼-> US4 final verification -> Polish
                                  └-> US4 ─┘
```

### Within Each User Story

1. Add the named failing tests and confirm the expected failure.
2. Implement the smallest model/registry behavior required by those tests.
3. Add Docusaurus/plugin/presentation integration.
4. Run the independent story checkpoint and update `validation.md`.

## Parallel Opportunities

- Setup T003 and T004 may run together after T002 establishes package metadata.
- Architecture T006 and T007 target different levels; T012–T015 target independent type, fixture, and
  contract-test files.
- US1 tests T018–T019 run together; presentation tasks T024–T026 run together after plugin global data
  exists.
- US2 tests T028–T030 run together; canonical docs T033–T034 target different files.
- US3 tests T036–T037 run together; T040 is independent after registry metadata exists.
- US4 tests T043–T045 run together.
- Polish tests T052–T053 run together before the serial full-system gates.
- After the US1 MVP, US2 and US3 can be assigned in parallel; US4's command layer can also begin while
  their final content behavior is being completed.

## Parallel Example: User Story 1

```text
T018: Registry, route, ordering, and navigation tests in docsite/tests/unit/registry.test.ts
T019: Production landing/navigation/search smoke test in docsite/tests/integration/production-build.test.ts

After T023:
T024: Landing page and summary components
T025: Provenance banner and DocItem wrapper
T026: Shared responsive styling
```

## Parallel Example: User Stories 2 and 3

```text
Contributor A: T028-T035 for root docs authoring and link behavior
Contributor B: T036-T042 for canonical feature publication and exclusion behavior
Contributor C: T043-T049 for build-interface and atomic-promotion behavior
```

## Implementation Strategy

### MVP First

1. Complete Setup and architecture/contract foundations.
2. Complete US1 through T027.
3. Stop and demonstrate one site containing fixture docs and two feature specs with navigation,
   provenance, and search.
4. Continue only after the MVP checkpoint passes.

### Incremental Delivery

1. **US1**: Unified browsable read model.
2. **US2**: Copy-free documentation authoring and cross-source links.
3. **US3**: Exact Spec Kit feature authority and lifecycle status.
4. **US4**: Deterministic, failure-safe maintainer workflow.
5. **Polish**: Full evidence, performance, accessibility, and self-hosting gate.

## Notes

- Architecture JSON is maintained intent; generated Archify HTML and Docusaurus output are never
  edited directly.
- `specs/002-create-project-docsite/contracts/build-manifest.schema.json` remains the normative custom
  manifest schema; architecture contract prose links to it rather than copying it.
- `docsite/` is private project tooling in this feature, not yet a distributable Concorde extension.
- Mark each task complete only after its named file change and validation succeed.
