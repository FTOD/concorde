---

description: "Dependency-ordered implementation tasks for the unified Concorde project docsite"
---

# Tasks: Create Unified Project Docsite

**Input**: Design documents from `/specs/concorde/features/002-create-project-docsite/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`

**Tests**: Required. Feature 002 specifies deterministic discovery, link and route failures,
source immutability, manifest repeatability, architecture publication, accessibility, and build
atomicity. Tests precede the implementation behavior they verify.

**Organization**: Tasks are grouped by user story. Completed checkboxes reflect the implemented
repository state after architecture and feature specifications were consolidated under `specs/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it targets different files and has no dependency on an
  incomplete task in the same group
- **[Story]**: Maps the task to `US1`, `US2`, `US3`, or `US4` from `spec.md`
- Every task names the exact implementation, maintained-source, test, or evidence path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the independent Node/TypeScript site project and safe repository boundaries.

- [X] T001 Add Node, Docusaurus, generated-site, projection, environment, editor, and OS exclusions to `.gitignore`
- [X] T002 Create private locked Docusaurus 3.10.2 project metadata and install the planned runtime/dev dependencies in `docsite/package.json` and `docsite/package-lock.json`
- [X] T003 [P] Configure strict TypeScript and Vitest environments in `docsite/tsconfig.json` and `docsite/vitest.config.ts`
- [X] T004 [P] Create the site, plugin, script, component, and test skeleton in `docsite/plugins/concorde-content/index.ts`, `docsite/scripts/validate.ts`, and `docsite/tests/setup.ts`
- [X] T005 Verify the independent package boundary and document prerequisite versions in `docsite/README.md`

**Checkpoint**: `cd docsite && npm ci` succeeds from the lockfile and produces no maintained-source changes.

---

## Phase 2: Foundational Architecture, Contracts, and Source Boundaries

**Purpose**: Establish the unified specification hierarchy, ownership, contracts, bounded views,
shared types, and deterministic diagnostics before user-facing behavior.

**Critical**: No user-story implementation begins until this phase passes its architecture and
contract checkpoint.

- [X] T006 Consolidate root module, contract, feature, and child-module specifications under `specs/concorde/` and remove the obsolete top-level `architecture/` source hierarchy
- [X] T007 [P] Register `feature.concorde.publish-project-docsite`, its canonical nested workspace, and its provided publication contract in `specs/concorde/module.md`
- [X] T008 [P] Add `feature.documentation.publish-project-docsite` with its textual outcome, adjacent refinement, representative scenario, contracts, and narrower requirements in `specs/concorde/modules/documentation/features/001-publish-project-docsite/spec.md`
- [X] T009 Reconcile module-owned source, build, manifest, and published-site contract identities with the feature-local normative representations in `specs/concorde/modules/documentation/contracts/project-content/contract.md`, `specs/concorde/modules/documentation/contracts/build-interface/contract.md`, `specs/concorde/modules/documentation/contracts/build-manifest/contract.md`, and `specs/concorde/modules/documentation/contracts/architecture-site/contract.md`
- [X] T010 Update Documentation feature, contract, responsibility, boundary, and evidence declarations in `specs/concorde/modules/documentation/module.md`
- [X] T011 Add the bounded Documentation publication scenario and governing contract references in `specs/concorde/modules/documentation/architecture.json`, then reconcile the root publication trace in `specs/concorde/architecture.json`
- [X] T012 Validate and render both maintained Archify views with delivery receipts in `generated/architecture/concorde-root.html`, `generated/architecture/concorde-root.visual-check.json`, `generated/architecture/documentation.html`, and `generated/architecture/documentation.visual-check.json`
- [X] T013 [P] Define source, feature, architecture, page, navigation, exclusion, finding, and manifest types plus renderer-projection invariants in `docsite/plugins/concorde-content/types.ts` and `docsite/scripts/materialize-content.ts`
- [X] T014 [P] Seed unified valid and invalid documentation, module, contract, and nested feature fixtures in `docsite/tests/fixtures/valid-project/` and `docsite/tests/fixtures/invalid-projects/`
- [X] T015 [P] Add normative example/schema validation plus emitted-manifest sorting, relative-path, route-inventory, and repeatability tests for `specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json` in `docsite/tests/contract/build-manifest.test.ts`
- [X] T016 [P] Add stable diagnostic formatting, finding ordering, invalid-fixture, and project-root containment contract tests in `docsite/tests/contract/content-sources.test.ts`
- [X] T017 Implement stable error formatting, hierarchy and declared-view checks, route uniqueness, and sorted findings in `docsite/plugins/concorde-content/validation.ts`
- [X] T018 Configure strict link, anchor, and route failures, disabled blog/update timestamps, and Architecture/Documentation/Features sidebar shells in `docsite/docusaurus.config.ts`, `docsite/sidebars.architecture.ts`, `docsite/sidebars.docs.ts`, and `docsite/sidebars.features.ts`

**Checkpoint**: The unified hierarchy is reviewable, both Archify views validate, contract examples
pass their schema, and deliberately invalid fixtures fail with stable rule/source/remediation diagnostics.

---

## Phase 3: User Story 1 — Browse the Whole Project in One Site (Priority: P1) — MVP

**Goal**: Publish Architecture, Documentation, and Features as three navigable, searchable views over
two maintained source roots with canonical provenance and embedded one-level diagrams.

**Independent Test**: Build the valid fixture containing module and contract Markdown, a declared
Archify view, nested project docs, and root/child feature specs; verify every eligible source appears
once in the correct route space, all three views are searchable, and provenance points only to `docs/`
or `specs/`.

### Tests for User Story 1

- [X] T019 [P] [US1] Write failing three-collection registry, route uniqueness, stable ordering, hierarchy, and navigation completeness tests in `docsite/tests/unit/registry.test.ts`
- [X] T020 [P] [US1] Write failing module/contract discovery, stable identity, declared-view mapping, and missing-delivery tests in `docsite/tests/unit/architecture-sources.test.ts`
- [X] T021 [P] [US1] Write a failing landing-page, three-view navigation, provenance, diagram, route, and local-search production smoke test in `docsite/tests/integration/production-build.test.ts`

### Implementation for User Story 1

- [X] T022 [US1] Implement deterministic Architecture/Documentation/Features discovery, Markdown/front-matter parsing, SHA-256 hashing, title extraction, canonical route derivation, and stable sorting in `docsite/plugins/concorde-content/registry.ts`
- [X] T023 [US1] Implement registry-driven clean materialization of Architecture and Features renderer inputs while preserving canonical `specs/` paths in `docsite/scripts/materialize-content.ts`
- [X] T024 [US1] Configure projected Architecture, direct Documentation, projected Features, three sidebars/navbar entries, and all-view local search in `docsite/docusaurus.config.ts`, `docsite/sidebars.architecture.ts`, `docsite/sidebars.docs.ts`, and `docsite/sidebars.features.ts`
- [X] T025 [US1] Implement deterministic collection, page, architecture-view, feature-status, navigation, exclusion, and route-inventory projection in `docsite/plugins/concorde-content/manifest.ts`
- [X] T026 [US1] Implement Docusaurus content loading, global registry data, canonical source watches, rendered-route verification, and manifest emission in `docsite/plugins/concorde-content/index.ts`
- [X] T027 [P] [US1] Build the three-view project landing page and collection summary in `docsite/src/pages/index.tsx` and `docsite/src/components/ProjectSummary.tsx`
- [X] T028 [P] [US1] Render canonical provenance, architecture identity, feature identity/status, and sandboxed Archify views in `docsite/src/components/ContentProvenance.tsx`, `docsite/src/components/ArchitectureView.tsx`, and `docsite/src/theme/DocItem/Layout/index.tsx`
- [X] T029 [P] [US1] Implement responsive three-view navigation, content-kind, status, provenance, and embedded-diagram styling in `docsite/src/css/custom.css`
- [X] T030 [US1] Run the User Story 1 unit and production checks and record three-view inventory, search, provenance, and diagram results in `specs/concorde/features/002-create-project-docsite/validation.md`

**Checkpoint**: The MVP publishes all three logical collections with one canonical source per page,
bounded architecture views, project-wide search, and no maintained copies in `docsite/`.

---

## Phase 4: User Story 2 — Author Documentation Outside the Site Project (Priority: P2)

**Goal**: Make ordinary root `docs/` Markdown automatically discoverable with preserved hierarchy,
formatting, and repository-relative links, without copies or manual registration.

**Independent Test**: Add, rename, link, and remove a nested fixture document without changing
`docsite/`; rebuild and verify that navigation and cross-view links reflect only current canonical sources.

### Tests for User Story 2

- [X] T031 [P] [US2] Write failing add, rename, remove, and hierarchical navigation tests for root documentation in `docsite/tests/integration/document-authoring.test.ts`
- [X] T032 [P] [US2] Write failing same-view, cross-view, fragment, missing-target, excluded-target, and escaping-target tests in `docsite/tests/unit/links.test.ts`
- [X] T033 [P] [US2] Write a failing before/after SHA-256 source-immutability test for registry validation over `docs/` and `specs/` in `docsite/tests/integration/source-immutability.test.ts`

### Implementation for User Story 2

- [X] T034 [US2] Implement canonical-path Markdown link classification, validation, staged-to-canonical resolution, route rewriting, and fragment preservation in `docsite/plugins/concorde-content/links.ts`
- [X] T035 [US2] Integrate the shared link transformer and deterministic documentation hierarchy in `docsite/plugins/concorde-content/index.ts`, `docsite/docusaurus.config.ts`, and `docsite/sidebars.docs.ts`
- [X] T036 [P] [US2] Create canonical project-documentation landing content with source-relative specification links in `docs/index.md`
- [X] T037 [P] [US2] Document Markdown metadata, cross-view links, local preview, build, projections, and troubleshooting in `docs/contributing/docsite.md`
- [X] T038 [US2] Run the User Story 2 authoring, link, and immutability tests and append results to `specs/concorde/features/002-create-project-docsite/validation.md`

**Checkpoint**: A contributor changes only `docs/`; the next build updates the Documentation view and
cross-view links while leaving both maintained source roots unchanged.

---

## Phase 5: User Story 3 — Publish Canonical Feature Specifications (Priority: P3)

**Goal**: Publish every module-owned canonical `spec.md` with current title, stable ID, owner, status,
provenance, and explicit exclusion of supporting Spec Kit artifacts.

**Independent Test**: Change a nested fixture feature title/status/requirement and add a child-module
feature workspace; verify the next build updates only canonical feature pages and records plans,
tasks, checklists, and other supporting Markdown as excluded.

### Tests for User Story 3

- [X] T039 [P] [US3] Write failing root and nested feature discovery, identity/status extraction, workspace hierarchy, and duplicate-ID tests in `docsite/tests/unit/feature-specifications.test.ts`
- [X] T040 [P] [US3] Write failing recursive canonical-only inclusion and supporting-artifact exclusion-manifest tests in `docsite/tests/integration/feature-publication.test.ts`

### Implementation for User Story 3

- [X] T041 [US3] Implement feature ID, kind, module, title, lifecycle status, and module-owned workspace extraction in `docsite/plugins/concorde-content/registry.ts`
- [X] T042 [US3] Implement recursive canonical `**/spec.md` inclusion, stable feature labels, and nested feature navigation in `docsite/sidebars.features.ts` and `docsite/docusaurus.config.ts`
- [X] T043 [P] [US3] Render stable ID, owning module, lifecycle status, and canonical source path without implying approval or implementation agreement in `docsite/src/components/ContentProvenance.tsx`
- [X] T044 [US3] Add deterministic supporting-artifact exclusion discovery and manifest records in `docsite/plugins/concorde-content/registry.ts` and `docsite/plugins/concorde-content/manifest.ts`
- [X] T045 [US3] Run the User Story 3 unit and integration tests and append root/child feature counts, statuses, exclusions, and immutability results to `specs/concorde/features/002-create-project-docsite/validation.md`

**Checkpoint**: Every root or child canonical feature spec is published once with identity, status,
module ownership, and provenance; no plan, task list, checklist, or evidence file is labeled as a feature.

---

## Phase 6: User Story 4 — Verify a Reproducible Site Build (Priority: P4)

**Goal**: Supply inspect, validate, preview, test, and failure-safe production commands with verified
routes, schema-valid manifests, deterministic projections, and atomic promotion.

**Independent Test**: Build unchanged sources twice and compare manifests, then inject each invalid
fixture and verify a non-zero actionable failure leaves the last successful `docsite/build/` intact.

### Tests for User Story 4

- [X] T046 [P] [US4] Write failing stable npm command, non-zero exit-status, and actionable-diagnostic contract tests in `docsite/tests/contract/build-interface.test.ts`
- [X] T047 [P] [US4] Write failing candidate failure, successful promotion, rollback, and stale-candidate tests in `docsite/tests/integration/atomic-promotion.test.ts`
- [X] T048 [P] [US4] Extend runtime manifest schema, sorting, route-inventory, canonical relative-path, and repeatability tests in `docsite/tests/contract/build-manifest.test.ts`

### Implementation for User Story 4

- [X] T049 [US4] Implement source inspection and validation command entry points in `docsite/scripts/inspect.ts` and `docsite/scripts/validate.ts`
- [X] T050 [US4] Implement canonical validation, projection materialization, clean candidate rendering, manifest-schema verification, atomic promotion, rollback, and failure cleanup in `docsite/scripts/build.ts`
- [X] T051 [US4] Implement actual-route verification and successful manifest emission in `docsite/plugins/concorde-content/index.ts` and `docsite/plugins/concorde-content/manifest.ts`
- [X] T052 [US4] Wire `inspect`, `validate`, `prepare-content`, `start`, `test`, `build`, `typecheck`, and `check` interfaces in `docsite/package.json`
- [X] T053 [US4] Add real-repository three-view build, route inventory, search asset, manifest, projection, and repeatability coverage in `docsite/tests/integration/production-build.test.ts`
- [X] T054 [US4] Run the User Story 4 contract/integration suite twice and append atomicity, projection freshness, and manifest comparison results to `specs/concorde/features/002-create-project-docsite/validation.md`

**Checkpoint**: All build-interface commands meet their contract, unchanged builds yield identical
manifests, and every failed candidate preserves the previous successful output.

---

## Phase 7: Polish and Cross-Cutting Quality Gates

**Purpose**: Prove accessibility, scale, self-hosting, architecture freshness, and complete agreement
among maintained sources, implementation, tests, and generated projections.

- [X] T055 [P] Add semantic landmark, keyboard navigation, responsive layout, provenance, and sandboxed-view accessibility assertions in `docsite/tests/integration/accessibility.test.ts`
- [X] T056 [P] Add a generated 1,000-document and 250-feature discovery/validation performance fixture test in `docsite/tests/integration/performance.test.ts`
- [X] T057 Reconcile contributor commands, projection behavior, and observed outputs with the build-interface contract in `docsite/README.md` and `docs/contributing/docsite.md`
- [X] T058 Run every scenario in `specs/concorde/features/002-create-project-docsite/quickstart.md` and record command results, timings, source immutability, feature statuses, and manifest hashes in `specs/concorde/features/002-create-project-docsite/validation.md`
- [X] T059 Re-run root and Documentation Archify validation, regenerate site/diagram projections, and update evidence status in `specs/concorde/module.md` and `specs/concorde/modules/documentation/module.md`
- [X] T060 Run `npm run check`, verify all 32 functional requirements and 8 success criteria, and record the requirement-to-evidence matrix in `specs/concorde/features/002-create-project-docsite/validation.md`
- [X] T061 Verify `git status` contains no generated site, cache, renderer projection, copied canonical content, or unexpected source mutation and record the audit in `specs/concorde/features/002-create-project-docsite/validation.md`
- [ ] T062 Conduct the browser visual review for both delivered Archify views and the SC-006 participant exercise requiring at least 90% of participants to locate a named document or feature within 60 seconds, then record participants, timings, outcomes, and reviewed receipts in `specs/concorde/features/002-create-project-docsite/validation.md`
  - **Progress**: Both Archify views pass required-viewport containment and perceptual light/dark review; the timed participant exercise remains outstanding.

**Checkpoint**: All deterministic tests and builds pass, architecture and documentation projections
are fresh, canonical sources remain authoritative, and every requirement maps to evidence.

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: Starts immediately.
- **Phase 2 — Foundation**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 — US1**: Depends on Phase 2 and delivers the complete three-view MVP.
- **Phase 4 — US2**: Depends on US1's registry, plugin, and routing foundation.
- **Phase 5 — US3**: Depends on US1's registry and projection foundation and may proceed in parallel with US2.
- **Phase 6 — US4**: Command and atomic-build work may begin after US1; final production verification depends on US2 and US3.
- **Phase 7 — Polish**: Depends on all four stories.

### User Story Dependency Graph

```text
Setup -> Unified hierarchy/contracts -> US1 (three-view MVP)
                                       |-> US2 docs authoring -----|
                                       |-> US3 feature publishing -|-> US4 final build -> Polish
                                       `-> US4 command/atomic work -'
```

- **US1 (P1)** has no dependency on another story after Foundation and delivers the complete browsable read model.
- **US2 (P2)** is independently testable by changing only fixture/root `docs/` after US1.
- **US3 (P3)** is independently testable with root and child feature workspaces after US1.
- **US4 (P4)** reuses US1's pipeline; its failure-safe command layer is independently testable before final all-content verification.

### Within Each User Story

1. Add the named failing tests and confirm the intended missing behavior.
2. Implement the smallest registry, projection, presentation, or command behavior required.
3. Run the story's independent fixture or production checkpoint.
4. Record only observed evidence in `validation.md`.

## Parallel Opportunities

- Setup tasks T003-T004 target independent configuration and skeleton files.
- Foundation tasks T007-T008 and T013-T016 target separate hierarchy, type, fixture, and contract-test files.
- US1 tests T019-T021 run together; presentation tasks T027-T029 run together after global registry data exists.
- US2 tests T031-T033 run together; canonical documentation tasks T036-T037 target different files.
- US3 tests T039-T040 run together; provenance task T043 is independent after registry metadata exists.
- US4 tests T046-T048 run together.
- Polish tests T055-T056 run together before the serial full-system gates; T062 remains a manual release-evidence gate.
- After US1, US2 and US3 may run in parallel while US4's command/atomic layer is developed.

## Parallel Example: User Story 1

```text
T019: Three-collection registry and navigation tests in docsite/tests/unit/registry.test.ts
T020: Architecture source and declared-view tests in docsite/tests/unit/architecture-sources.test.ts
T021: Three-view production smoke test in docsite/tests/integration/production-build.test.ts

After T026:
T027: Landing page and three-view summary
T028: Provenance and sandboxed architecture view components
T029: Shared responsive styling
```

## Parallel Example: User Story 2

```text
T031: Documentation add/rename/remove tests in docsite/tests/integration/document-authoring.test.ts
T032: Cross-view link tests in docsite/tests/unit/links.test.ts
T033: Source-immutability tests in docsite/tests/integration/source-immutability.test.ts

After T035:
T036: Canonical documentation landing content
T037: Contributor authoring and projection guide
```

## Parallel Example: User Story 3

```text
T039: Root and nested feature identity tests in docsite/tests/unit/feature-specifications.test.ts
T040: Canonical inclusion and exclusion tests in docsite/tests/integration/feature-publication.test.ts

After T042:
T043: Feature provenance and lifecycle-status presentation
```

## Parallel Example: User Story 4

```text
T046: Build-interface contract tests in docsite/tests/contract/build-interface.test.ts
T047: Atomic-promotion tests in docsite/tests/integration/atomic-promotion.test.ts
T048: Runtime manifest contract tests in docsite/tests/contract/build-manifest.test.ts
```

## Implementation Strategy

### MVP First

1. Complete Setup and the unified hierarchy/contract foundation.
2. Complete US1 through T030.
3. Stop and demonstrate Architecture, Documentation, and Features with provenance, search, and embedded views.
4. Continue only after the three-view MVP checkpoint passes.

### Incremental Delivery

1. **US1**: Three-view browsable read model over `specs/` and `docs/`.
2. **US2**: Copy-free documentation authoring and cross-view links.
3. **US3**: Exact root/child feature authority and lifecycle status.
4. **US4**: Deterministic, failure-safe maintainer workflow.
5. **Polish**: Full evidence, performance, accessibility, self-hosting, and freshness gates.

## Notes

- Module and contract Markdown, feature `spec.md`, Archify JSON, code, tests, and generated projections retain distinct authority.
- Architecture and Features share canonical `specs/` but use separate ignored renderer inputs under `docsite/.generated/content/`.
- `specs/concorde/features/002-create-project-docsite/contracts/build-manifest.schema.json` is the normative custom manifest schema; module contract prose registers and links it without copying its semantics.
- `docsite/` is private project tooling in this feature, not yet a distributable Concorde extension.
- Mark a task complete only after its named source change and validation evidence exist.
