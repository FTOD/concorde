# Tasks: Create Unified Project Docsite

**Input**: `specs/concorde/features/002-auto-docsite.md`, `specs/concorde/architecture.md`, source
code and executable tests, and this attempt's plan/research/data model/quickstart.

**Tests**: Test-first for every runtime, packaging, and adapter change.

## Phase 1: Setup and Protected Baseline

- [X] T001 Record protected feature/architecture/related-summary digests and initial inventory in `.concorde/attempts/feature.concorde.publish-project-docsite/validation.md` [Plan:Risk Controls]
- [X] T002 [P] Seed Concorde's site identity `docsite/site.json` and the generic workflow template `docsite/scaffold/deploy-docsite.yml` [FR-008]

## Phase 2: Foundational Work

**Goal**: One template inventory rule and one identity loader that every later slice uses.

- [X] T003 [P] Write failing tests in `tests/concorde/unit/test_docsite_template.py` for the inventory rule, scaffold-only directory, symlink rejection, and digest determinism [FR-006, NFR-001]
- [X] T004 Implement `src/concorde/docsite_template.py` [FR-006]
- [X] T005 [P] Write failing tests in `docsite/tests/unit/site-identity.test.ts` for site identity schema 1 loading and diagnostics [FR-008]
- [X] T006 Implement `docsite/plugins/concorde-content/site-identity.ts` and make `docsite/docusaurus.config.ts` read identity, render the repository link only when present, and register the Documentation collection only when `docs/` exists [FR-008, FR-009]
- [X] T007 Run focused Python and docsite unit checks and record evidence in `.concorde/attempts/feature.concorde.publish-project-docsite/validation.md` [plan gate]

## Phase 3: User Story 1 — The package ships the template (P1)

**Goal**: Checkout, archive, and installed framework carry identical docsite template bytes.

**Independent Test**: `installer.desired_outputs` lists `.concorde/framework/docsite/docusaurus.config.ts` and no `site.json`, `node_modules`, or `tests/repository` member; the release archive contains `concorde/docsite/package.json`.

- [X] T008 [P] [US1] Extend `tests/concorde/unit/test_install_concorde.py`, `tests/concorde/contract/test_release_artifacts.py`, and `tests/concorde/unit/test_capability_validation.py` for the `docsite` package root [FR-006]
- [X] T009 [US1] Update `concorde.json`, `scripts/install-concorde.py`, `scripts/release/build-release.py`, and `scripts/release/verify-release.py` to package the docsite template through `src/concorde/docsite_template.py` [FR-006]
- [X] T010 [US1] Move Concorde-repository evidence into `docsite/tests/repository/`, keep portable tests under `docsite/tests/{unit,contract,integration}`, and make `.github/workflows/deploy-docsite.yml` byte-identical to `docsite/scaffold/deploy-docsite.yml` [FR-006, FR-009]
- [X] T011 [US1] Run the Python suite and `npm run check` in `docsite/`; record evidence in `.concorde/attempts/feature.concorde.publish-project-docsite/validation.md` [FR-006]

## Phase 4: User Story 2 — Scaffold Tool (P1)

**Goal**: `concorde.py docsite --propose/--apply` previews and atomically applies Docsite Scaffold Proposal 1.

**Independent Test**: In a temp project holding only Initialization Proposal 3 outputs, propose returns a deterministic proposal with `docsite/site.json` and `README.md`; apply creates exactly those files; a second apply is `unchanged`; an edited proposal or existing target is rejected.

- [X] T012 [P] [US2] Write failing tests in `tests/concorde/integration/test_docsite_scaffold.py` for unconfigured projects, determinism, identity defaults, GitHub Pages derivation, README-when-absent, `--github-pages`, conflicts, exact apply, stale proposals, and prerequisite findings [FR-007, FR-010, NFR-001, NFR-002]
- [X] T013 [US2] Implement `src/concorde/docsite_scaffold.py` and the `docsite` subcommand in `src/concorde/cli.py` [FR-007, FR-010]
- [X] T014 [US2] Run focused checks and record evidence in `.concorde/attempts/feature.concorde.publish-project-docsite/validation.md` [FR-007]

## Phase 5: User Story 3 — `concorde-init` offers the step and a fresh project publishes (P2)

**Goal**: A maintainer reaches the scaffold from the initialization Skill and a scaffolded project passes the adapter's checks.

**Independent Test**: The fresh-project repository test initializes a temp project, scaffolds the docsite, and runs the adapter's validate and build successfully.

- [X] T015 [US3] Add the docsite step to `skills/concorde-init/SKILL.md` and refresh `.claude/skills/concorde-init/SKILL.md` and `.agents/skills/concorde-init/SKILL.md` through `scripts/development/sync-agent-surfaces.py apply` [interface.concorde.scaffold-docsite]
- [X] T016 [US3] Add `docsite/tests/repository/fresh-project-scaffold.test.ts` that runs init, docsite propose/apply, validate, and build in a temp project [FR-009]
- [X] T017 [US3] Run the fresh-project evidence and record it in `.concorde/attempts/feature.concorde.publish-project-docsite/validation.md` [FR-009]

## Final Phase: Cross-Cutting Reconciliation and Delivery Readiness

- [X] T018 Reconcile `specs/concorde/architecture.md` (entity definitions, relationship, interaction) and `specs/concorde/diagrams/system-overview.json` (connection `distribution -> autodocs`), then validate with `npm run render-diagrams` [Architecture Zoom]
- [X] T019 [P] Reconcile `specs/concorde/modules/runtime/architecture.md` and `specs/concorde/modules/runtime/features/001-run-lifecycle-tools.md` [contract.runtime.tools]
- [X] T020 [P] Reconcile `specs/concorde/modules/distribution/architecture.md` and `specs/concorde/modules/distribution/features/001-package-concorde.md` [contract.distribution.standalone-package]
- [X] T021 [P] Reconcile `specs/concorde/modules/auto-docs/architecture.md` and `specs/concorde/modules/auto-docs/features/001-publish-project-docsite.md` [contract.auto-docs.build-interface]
- [X] T022 Reconcile `specs/concorde/features/002-auto-docsite.md` outputs, example, and `evidence_status` with the implemented Tool [FR-006, FR-007, FR-008, FR-009, FR-010]
- [X] T023 [P] Update `docs/quick-start.md`, `docs/skills.md`, `docs/concorde-workflow.md`, `docs/project-structure.md`, `docs/framework-overview.md`, `docs/contributing/docsite.md`, `README.md`, and `docsite/README.md` [interface.concorde.scaffold-docsite]
- [X] T024 Run `python3 scripts/concorde.py --project-root . validate`, the full Python suite, `npm run check`, and `sync-agent-surfaces.py status`; record final digests, completeness, limitations, and the exact delivery remove path in `.concorde/attempts/feature.concorde.publish-project-docsite/validation.md` [SC]

## Dependencies and Parallel Opportunities

- T001–T002 precede everything. T003–T004 and T005–T006 are independent streams.
- US1 (T008–T011) depends on T004; US2 (T012–T014) depends on T004 and T002.
- US3 depends on US1 and US2. Final phase follows all stories.
