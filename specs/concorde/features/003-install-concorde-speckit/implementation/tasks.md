---

description: "Dependency-ordered implementation tasks for the Concorde starter bundle"
---

# Tasks: Install Concorde Starter Bundle

**Input**: Historical installation delivery record now owned by `/specs/concorde/features/003-install-concorde-speckit/implementation/`

**Prerequisites**: `plan.md`, `../spec.md`, `research.md`, `data-model.md`, `../contracts/`, and any active validation guide

**Lifecycle**: Temporal implementation record. Completion state describes this delivery attempt, not
the continuing validity of the durable feature specification.

**Tests**: Required. Feature 001 defines lifecycle, portability, determinism, source-safety, and
contract-conformance acceptance criteria. Tests MUST be written first and observed failing before the
corresponding implementation task begins.

**Organization**: Tasks are grouped by user story so each story produces an independently testable
increment. Unified specification-hierarchy tasks precede implementation in accordance with the Concorde
constitution.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no dependency on an
  incomplete task in the same phase
- **[Story]**: Maps a task to `US1`, `US2`, `US3`, or `US4` from `spec.md`
- Every task names the exact file or directory it changes

## Phase 1: Setup and Architecture Alignment

**Purpose**: Establish the planned source layout and record the child-module intent required before
implementation starts.

- [X] T001 Create the planned Python package markers in `extensions/concorde/runtime/concorde/__init__.py`, `tests/__init__.py`, `tests/concorde/__init__.py`, `tests/concorde/unit/__init__.py`, `tests/concorde/contract/__init__.py`, `tests/concorde/integration/__init__.py`, `tests/concorde/acceptance/__init__.py`, and `tests/concorde/support/__init__.py`
- [X] T002 [P] Configure the Python 3.11 `uv` development and `unittest` discovery settings in `pyproject.toml`, `.python-version`, and `uv.lock`
- [X] T003 [P] Add generated release archives, temporary acceptance projects, caches, and virtual environments to `.gitignore`
- [X] T004 [P] Author the Distribution refinement with a textual outcome, adjacent parent link, representative scenario, and governing contracts in `specs/concorde/modules/distribution/features/001-package-starter-bundle/spec.md`
- [X] T005 [P] Author the Spec Kit Integration refinement with a textual outcome, adjacent parent link, representative scenario, and governing contracts in `specs/concorde/modules/spec-kit-integration/features/001-compose-starter-workflow/spec.md`
- [X] T006 [P] Author the Architecture Core refinement with a textual outcome, adjacent parent link, representative scenario, and governing contracts in `specs/concorde/modules/architecture-core/features/001-manage-bounded-sources/spec.md`
- [X] T007 [P] Define the bundle lifecycle and component package boundary contracts in `specs/concorde/modules/distribution/contracts/bundle-lifecycle/contract.md` and `specs/concorde/modules/distribution/contracts/component-packages/contract.md`
- [X] T008 [P] Define workflow composition, agent skill, Spec Kit platform, and architecture service boundary contracts in `specs/concorde/modules/spec-kit-integration/contracts/workflow-composition/contract.md`, `specs/concorde/modules/spec-kit-integration/contracts/agent-skills/contract.md`, `specs/concorde/modules/spec-kit-integration/contracts/spec-kit-platform/contract.md`, and `specs/concorde/modules/spec-kit-integration/contracts/architecture-services/contract.md`
- [X] T009 [P] Define the custom Architecture Service Protocol contract and link its normative schema and examples in `specs/concorde/modules/architecture-core/contracts/architecture-services/contract.md`
- [X] T010 Register the new features and canonical contract paths in `specs/concorde/modules/distribution/module.md`, `specs/concorde/modules/spec-kit-integration/module.md`, and `specs/concorde/modules/architecture-core/module.md`

**Checkpoint**: Feature ownership, adjacent-level refinement, boundary obligations, and source
authority are reviewable before implementation.

---

## Phase 2: Foundational Runtime and Test Infrastructure

**Purpose**: Build the shared deterministic source reader, result model, and clean-project harness
required by every user story.

**⚠️ CRITICAL**: No user story implementation begins until this phase is complete.

- [X] T011 Create shared test package markers and path constants in `tests/concorde/__init__.py` and `tests/concorde/support/paths.py`
- [X] T012 [P] Create a minimal valid Profile 1 `specification_root` with colocated module, contract, feature, and view sources in `tests/concorde/fixtures/valid-project/specs/example/` and `tests/concorde/fixtures/valid-project/.concorde/config.json`
- [X] T013 [P] Create a three-level unified specification hierarchy with externals, representative scenarios, and adjacent refinement links in `tests/concorde/fixtures/context-project/specs/example/`
- [X] T014 [P] Create seeded parse, duplicate-ID, broken-reference, cycle, contract, scenario, view-depth, and evidence fixtures in `tests/concorde/fixtures/invalid-projects/`
- [X] T015 [P] Write failing constrained-front-matter and unsupported-YAML tests in `tests/concorde/unit/test_frontmatter.py`
- [X] T016 [P] Write failing project-root safety, deterministic discovery, ID lookup, and source-digest tests in `tests/concorde/unit/test_repository.py`
- [X] T017 [P] Write failing canonical envelope, finding ordering, safe-path, and example-conformance tests in `tests/concorde/contract/test_structured_results.py`
- [X] T018 Define immutable module, feature, contract, scenario, view, operation, proposal, bounded-context, and finding entities in `extensions/concorde/runtime/concorde/model.py`
- [X] T019 Implement canonical JSON serialization, finding sort order, status-to-exit-code mapping, and source digests in `extensions/concorde/runtime/concorde/diagnostics.py`
- [X] T020 Implement the dependency-free Profile 1 YAML-front-matter subset parser in `extensions/concorde/runtime/concorde/frontmatter.py`
- [X] T021 Implement project-root confinement, `specification_root` configuration loading, recursive module/contract/feature/view traversal, relationship indexes, and safe staged writes in `extensions/concorde/runtime/concorde/repository.py`
- [X] T022 Define the stable operation dispatch and argument parser interfaces in `extensions/concorde/runtime/concorde/cli.py`
- [X] T023 Expose the package entry point and public version surface in `extensions/concorde/runtime/concorde/__main__.py` and `extensions/concorde/runtime/concorde/__init__.py`
- [X] T024 Run the foundational tests and document their passing commands in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: The standard-library runtime can safely read sources and emit schema-shaped,
deterministically ordered results; story work can begin.

---

## Phase 3: User Story 1 - Install and Verify Concorde (Priority: P1) 🎯 MVP

**Goal**: Validate, build, inspect, and install one native bundle containing exactly the
`concorde-core` preset and `concorde` extension, then discover all three commands in Codex skills
mode without modifying user-authored sources on repeat installation.

**Independent Test**: In a clean Spec Kit 0.16.4 project, compare `bundle info --json` with the
installed component record, verify one preset, one extension, and three Codex skills, then install
the same release three more times and confirm registry cardinality and user-source hashes do not
change.

### Tests for User Story 1

> Write these tests first and confirm they fail before creating the distributable artifacts.

- [X] T025 [P] [US1] Write manifest and exact-component-cardinality contract tests in `tests/concorde/contract/test_manifests.py`
- [X] T026 [P] [US1] Write canonical command name, arguments, effect, portability, and runtime-path contract tests in `tests/concorde/contract/test_agent_commands.py`
- [X] T027 [P] [US1] Write append-only spec, plan, and tasks template tests covering nested module-owned workspaces, primary textual feature outcomes, representative scenarios, contracts, and one canonical `spec.md` in `tests/concorde/integration/test_preset_composition.py`
- [X] T028 [P] [US1] Write reproducible archive, catalog-version, URL-policy, and digest tests in `tests/concorde/contract/test_release_artifacts.py`
- [X] T029 [US1] Write clean-project preview/install tests for bundle ID, directory, manifest, artifact, uninitialized-project, and three-repeat paths in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T030 [US1] Write command discovery and primary registration acceptance tests for Codex skills mode in `tests/concorde/acceptance/test_codex_skills.py`

### Implementation for User Story 1

- [X] T031 [P] [US1] Author the `concorde-core@0.1.0` append-only preset manifest and usage contract in `presets/concorde-core/preset.yml` and `presets/concorde-core/README.md`
- [X] T032 [P] [US1] Add nested workspace, textual feature outcome, representative scenario, stable-ID, ownership, refinement, contract, architecture-review, evidence, validation, and freshness guidance in `presets/concorde-core/templates/spec-template.md`, `presets/concorde-core/templates/plan-template.md`, and `presets/concorde-core/templates/tasks-template.md`
- [X] T033 [P] [US1] Author the `concorde@0.1.0` extension manifest and integration-neutral usage contract in `extensions/concorde/extension.yml` and `extensions/concorde/README.md`
- [X] T034 [P] [US1] Author thin orchestration definitions for all three canonical operations in `extensions/concorde/commands/speckit.concorde.init.md`, `extensions/concorde/commands/speckit.concorde.context.md`, and `extensions/concorde/commands/speckit.concorde.validate.md`
- [X] T035 [US1] Add portable runtime launchers with relative installed paths in `extensions/concorde/scripts/bash/concorde.sh`, `extensions/concorde/scripts/powershell/concorde.ps1`, and `extensions/concorde/scripts/python/concorde.py`
- [X] T036 [P] [US1] Author the schema-valid `concorde-starter@0.1.0` bundle manifest and catalog prerequisites in `bundles/concorde-starter/bundle.yml` and `bundles/concorde-starter/README.md`
- [X] T037 [US1] Publish matching install-allowed component and bundle metadata in `catalogs/extensions.json`, `catalogs/presets.json`, and `catalogs/bundles.json`
- [X] T038 [US1] Implement deterministic preset and extension archive construction in `scripts/release/build-components.py`
- [X] T039 [US1] Implement manifest, pin, cardinality, catalog, digest, HTTPS-release, and reproducibility verification in `scripts/release/verify-release.py`
- [X] T040 [P] [US1] Implement the localhost-only static catalog fixture server in `tests/concorde/support/catalog_server.py`
- [X] T041 [US1] Implement isolated Specify CLI project setup, trusted-catalog registration, subprocess capture, and source hashing helpers in `tests/concorde/support/specify_project.py`
- [X] T042 [US1] Make the source, built-artifact, catalog-ID, clean initialization, exact-plan, idempotency, and Codex discovery journeys pass in `tests/concorde/integration/test_bundle_lifecycle.py` and `tests/concorde/acceptance/test_codex_skills.py`
- [X] T043 [US1] Record Spec Kit version, artifact hashes, expanded-plan comparison, install forms, repeat-install evidence, and Codex registration results in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: User Story 1 is a releasable MVP: the native bundle can be inspected, installed, and
verified without a Concorde-specific installer.

---

## Phase 4: User Story 2 - Initialize a Root Specification Hierarchy (Priority: P2)

**Goal**: Make `speckit.concorde.init` produce a review-only root specification-hierarchy proposal and
apply exactly an explicitly accepted proposal with conflict detection, staged writes, and idempotent
repeat behavior.

**Independent Test**: Against an installed clean project with no Concorde specification hierarchy,
verify proposal mode writes nothing; apply the accepted proposal under `specs/<root-slug>/`; validate
stable IDs, explicit contracts, immediate children, and the one-level view; rerun and receive
`unchanged`; then prove changed or occupied target files return `conflict` without overwrites.

### Tests for User Story 2

- [X] T044 [P] [US2] Write init request, proposal, apply, unchanged, conflict, and safe-path schema tests in `tests/concorde/contract/test_structured_results.py`
- [X] T045 [P] [US2] Write proposal-only, deterministic default-ID, complete proposed-file, and zero-write tests in `tests/concorde/integration/test_initialize.py`
- [X] T046 [US2] Write accepted-apply, changed-target conflict, partial-package conflict, staged-promotion failure, and idempotent-rerun tests in `tests/concorde/integration/test_initialize.py`

### Implementation for User Story 2

- [X] T047 [P] [US2] Add proposal file records, content hashes, conflicts, and init result projections to `extensions/concorde/runtime/concorde/model.py`
- [X] T048 [US2] Implement deterministic root-ID derivation, unified `specs/<root-slug>/` hierarchy proposal generation, existing-hierarchy detection, and complete-file hashing in `extensions/concorde/runtime/concorde/initialize.py`
- [X] T049 [US2] Implement accepted-proposal verification, stage-then-promote writes, rollback diagnostics, and overwrite refusal in `extensions/concorde/runtime/concorde/initialize.py`
- [X] T050 [US2] Wire `init --propose` and `init --apply --proposal` with canonical JSON and exit behavior in `extensions/concorde/runtime/concorde/cli.py`
- [X] T051 [US2] Encode explicit agent-side proposal presentation and approval handoff in `extensions/concorde/commands/speckit.concorde.init.md`
- [X] T052 [US2] Add the installed proposal-review-apply-unchanged scenario to `tests/concorde/acceptance/test_starter_journey.py`
- [X] T053 [US2] Record proposal immutability, approved artifacts, conflict behavior, and repeat-init evidence in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: User Story 2 can establish maintained root intent safely and is independently
testable through the runtime or installed skill.

---

## Phase 5: User Story 3 - Retrieve and Validate Bounded Context (Priority: P3)

**Goal**: Make `speckit.concorde.context` return exactly one architectural level and make
`speckit.concorde.validate` deterministically report every required structural rule without changing
maintained sources.

**Independent Test**: Request the root module and a feature from the context fixture and prove the
same bounded projection contains current-level details, immediate-child I/O, permitted externals,
scenarios, refinement links, and deeper references but no child feature bodies or grandchildren;
then validate every seeded invalid fixture and compare three unchanged runs byte-for-byte.

### Tests for User Story 3

- [X] T054 [P] [US3] Write failing rule-order, finding-content, containment-cycle, refinement, contract, scenario, view-depth, and evidence tests in `tests/concorde/unit/test_rules.py`
- [X] T055 [P] [US3] Write module-ID, feature-ID, one-level inclusion, deeper-reference, unknown-ID, duplicate-ID, and read-only context tests in `tests/concorde/integration/test_context.py`
- [X] T056 [P] [US3] Write full-package, bounded-target, all-findings, no-mutation, explicit-unknown-evidence, and exit-code tests in `tests/concorde/integration/test_validation.py`
- [X] T057 [P] [US3] Add exact context and validation example-conformance assertions to `tests/concorde/contract/test_structured_results.py`
- [X] T058 [US3] Add three-run byte-equivalence, stable source-digest, path-portability, and source-immutability assertions to `tests/concorde/integration/test_validation.py`

### Implementation for User Story 3

- [X] T059 [US3] Implement module and feature target resolution plus one-level current-module features/I/O, all immediate-child organization and concise contract ID/role/flow/counterparty summaries, permitted externals, representative scenarios, adjacent refinements, and deeper navigation references in `extensions/concorde/runtime/concorde/context.py`
- [X] T060 [P] [US3] Implement source-profile and parse diagnostics in `extensions/concorde/runtime/concorde/validate.py`
- [X] T061 [US3] Implement stable-ID uniqueness, reference resolution, and project-relative path rules in `extensions/concorde/runtime/concorde/validate.py`
- [X] T062 [US3] Implement containment cycle, feature ownership, adjacent refinement, and refinement cycle rules in `extensions/concorde/runtime/concorde/validate.py`
- [X] T063 [US3] Implement module/feature contract-set, contract completeness, representation, evidence, and boundary-usage rules in `extensions/concorde/runtime/concorde/validate.py`
- [X] T064 [US3] Implement scenario participant, boundary-interaction, current-level view, non-leaf view, and explicit evidence-status rules in `extensions/concorde/runtime/concorde/validate.py`
- [X] T065 [US3] Assemble complete sorted findings, derived summaries, normalized source digests, and non-mutating bounded validation results in `extensions/concorde/runtime/concorde/validate.py`
- [X] T066 [US3] Wire `context` and `validate` arguments, canonical JSON output, and stable process exits in `extensions/concorde/runtime/concorde/cli.py`
- [X] T067 [P] [US3] Align agent result presentation and failure behavior with the normative envelope in `extensions/concorde/commands/speckit.concorde.context.md` and `extensions/concorde/commands/speckit.concorde.validate.md`
- [X] T068 [US3] Add installed bounded-context, successful-validation, seeded-failure, and three-run determinism scenarios to `tests/concorde/acceptance/test_starter_journey.py`
- [X] T069 [US3] Validate Concorde's own unified `specs/concorde/` hierarchy and save deterministic self-application assertions for artifact authority, one-level visibility, and adjacent feature refinement in `tests/concorde/integration/test_self_architecture.py`
- [X] T070 [US3] Record context-boundary counts, complete seeded-rule detection, three-run byte equivalence, no-write hashes, and self-validation results in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: User Story 3 provides an agent-independent architecture control surface with bounded
context and deterministic diagnostics.

---

## Phase 6: User Story 4 - Manage the Installation Lifecycle (Priority: P4)

**Goal**: Preview and apply a compatible update, inspect accurate status/provenance, recover honestly
from injected failures, and remove only bundle-owned components while retaining project-authored
specification sources and shared dependencies.

**Independent Test**: Install the initial fixture release, create and hash the project-authored
`.concorde/` and `specs/` hierarchy, preview and install the compatible fixture update, inject one
failed update, share one component with another bundle, and remove Concorde; verify accepted versions
and provenance throughout and compare project-source hashes before and after every operation.

### Tests for User Story 4

- [X] T071 [US4] Write compatible update-plan, accepted-version, configuration-preservation, and `.concorde/` plus `specs/` source-hash tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T072 [US4] Write failed install/update rollback, prior-record retention, and residual-partial-state tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T073 [US4] Write solely-owned removal, shared-component retention, modified-component safety, agent-artifact, and project-source preservation tests in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T074 [US4] Write bundle, preset, extension, source, version, ownership, and active/disabled provenance assertions in `tests/concorde/integration/test_bundle_lifecycle.py`

### Implementation for User Story 4

- [X] T075 [P] [US4] Create initial, compatible-update, shared-component, and injected-failure release inputs in `tests/concorde/fixtures/releases/`
- [X] T076 [US4] Extend deterministic component building and catalog generation for versioned fixture releases in `scripts/release/build-components.py`
- [X] T077 [US4] Add lifecycle fixture orchestration, failure injection, registry snapshots, and shared-owner setup to `tests/concorde/support/specify_project.py`
- [X] T078 [US4] Complete native preview/update/status/failure/remove acceptance assertions in `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T079 [US4] Add the installed update-and-safe-removal journey to `tests/concorde/acceptance/test_starter_journey.py`
- [X] T080 [US4] Record update-plan parity, rollback state, provenance, shared ownership, and byte-identical retained sources in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: User Story 4 proves that Concorde participates safely in the full native Spec Kit
bundle lifecycle and leaves project-owned intent intact.

---

## Phase 7: User Story 1 Extension - Understand the Spec Kit Ecosystem (Priority: P1)

**Goal**: Make the bundle, preset, extension, catalog, active integration, Architecture Core, and
unchanged Spec Kit lifecycle understandable through consistent prose and two validated supplemental
views without overloading the canonical root architecture.

**Independent Test**: Review the explanation for no more than five minutes, inspect both published
views, and verify the bundle is shown as a passive recipe, the preset and extension follow distinct
use-time paths, Spec Kit owns installation/lifecycle, and the supplemental views remain outside the
module-owned Architecture Core source profile.

### Tests for the User Story 1 Explanation

- [X] T081 [P] [US1] Add regression coverage for role consistency, diagram participants and paths, supplemental-view boundaries, and generated artifact presence in `tests/concorde/contract/test_ecosystem_explanation.py`
- [X] T082 [P] [US1] Add production-build assertions for both supplemental interactive routes in `docsite/tests/integration/production-build.test.ts`

### Implementation for the User Story 1 Explanation

- [X] T083 [US1] Align the plain-language role and authority model now owned by Feature 003 in `specs/concorde/features/003-install-concorde-speckit/spec.md`, `specs/concorde/features/003-install-concorde-speckit/implementation/quickstart.md`, `specs/concorde/module.md`, `specs/concorde/contracts/spec-kit-installation/contract.md`, and `specs/concorde/contracts/spec-kit-platform/contract.md`
- [X] T084 [P] [US1] Align Distribution and Spec Kit Integration refinements and module explanations in `specs/concorde/modules/distribution/features/001-package-starter-bundle/spec.md`, `specs/concorde/modules/distribution/module.md`, `specs/concorde/modules/spec-kit-integration/features/001-compose-starter-workflow/spec.md`, and `specs/concorde/modules/spec-kit-integration/module.md`
- [X] T085 [P] [US1] Maintain the structural and temporal supplemental sources now owned by the separated installation feature in `specs/concorde/features/003-install-concorde-speckit/spec-kit-component-model.json` and `specs/concorde/features/003-install-concorde-speckit/starter-installation-flow.json`
- [X] T086 [US1] Validate, deliver, visually review, and retain provenance evidence for both supplemental views under `generated/architecture/`
- [X] T087 [US1] Correct package-supply and command-registration semantics in `specs/concorde/architecture.json`, regenerate `generated/architecture/concorde-root.html`, and keep the root view bounded to immediate Concorde modules and permitted externals
- [X] T088 [US1] Record FR-029, FR-030, Archify, documentation publication, and pending SC-011 evidence in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

**Checkpoint**: User Story 1 includes an accessible, published, and regression-tested explanation of
how Concorde composes with Spec Kit, while its human comprehension outcome remains explicitly pending.

---

## Phase 8: Polish and Cross-Cutting Acceptance

**Purpose**: Prove portability, platform safety, self-application, documentation freshness, and the
complete quick-start outcome across the delivered stories.

- [X] T089 [P] Write and pass discovery plus primary-command portability acceptance for one supported slash-command integration in `tests/concorde/acceptance/test_slash_commands.py`
- [X] T090 [P] Verify a post-install Spec Kit specify/plan/tasks cycle targets a module-owned nested workspace, produces one canonical feature spec with composed Concorde gates, and creates no top-level `architecture/` source tree in `tests/concorde/acceptance/test_preset_workflow.py`
- [X] T091 [P] Add POSIX and PowerShell launcher path, quoting, exit-code, and Python 3.11 compatibility coverage in `tests/concorde/contract/test_agent_commands.py`
- [X] T092 [P] Add absolute path, traversal, backslash, symlink escape, malformed proposal, and unsupported-version security coverage in `tests/concorde/unit/test_repository.py` and `tests/concorde/integration/test_bundle_lifecycle.py`
- [X] T093 Execute every automated command in `specs/concorde/features/003-install-concorde-speckit/implementation/quickstart.md` from clean fixtures and correct any documented discrepancy in that file
- [X] T094 Update implementation status and runnable install examples in `README.md`
- [X] T095 Update delivered feature, contract, and evidence status in `specs/concorde/module.md`, `specs/concorde/modules/distribution/module.md`, `specs/concorde/modules/spec-kit-integration/module.md`, and `specs/concorde/modules/architecture-core/module.md`
- [X] T096 Run the installed Concorde validator against this repository and append the stable self-application result and any explicit bootstrap exception to `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [X] T097 Refresh and validate the root Archify projection from `specs/concorde/architecture.json` into `generated/architecture/concorde-root.html`
- [X] T098 Run the complete Docusaurus source, architecture, freshness, test, and production-build gate from `docsite/package.json` and record the result in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`
- [ ] T099 Conduct the timed first-use and comprehension pilot for SC-001, SC-009, and SC-011 and record participant count, completion times, assistance rate, five-prompt comprehension results, environment, and outcome in `specs/concorde/features/003-install-concorde-speckit/implementation/validation.md`

---

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 — Setup and Architecture Alignment**: Starts immediately; T010 depends on T004-T009.
- **Phase 2 — Foundational Runtime and Test Infrastructure**: Depends on Phase 1; tests T015-T017
  precede implementations T018-T023, and T024 closes the phase.
- **Phase 3 — US1**: Depends on Phase 2 and is the MVP. Tests T025-T030 precede distributable and
  release work T031-T042; T043 records only observed results.
- **Phase 4 — US2**: Depends on Phase 2 for direct runtime testing and on US1 only for installed-skill
  acceptance T052. Tests T044-T046 precede T047-T052.
- **Phase 5 — US3**: Depends on Phase 2 for direct runtime testing and on US1 only for installed-skill
  acceptance T068. Tests T054-T058 precede T059-T069.
- **Phase 6 — US4**: Depends on the installable US1 release. Tests T071-T074 precede fixtures and
  lifecycle completion T075-T079.
- **Phase 7 — US1 Explanation**: Depends on the installable US1 artifacts and the existing
  documentation publication pipeline. Regression tasks T081-T082 precede alignment and delivery
  tasks T083-T088.
- **Phase 8 — Polish**: Depends on every story included in the release. T099 is a human evidence gate
  and cannot be replaced by automation.

### User Story Dependency Graph

```text
Setup → Foundation → US1 (installable MVP) ───────────────→ US4 (lifecycle)
                      ├──→ US2 (initialization) ──┐
                      └──→ US3 (context/validate) ├──→ Cross-cutting acceptance
                                                 └──→ Quickstart + self-application
```

- **US1 (P1)** has no dependency on another story and delivers an inspectable, installable command
  surface.
- **US2 (P2)** is independently testable through the runtime after Foundation; its installed-agent
  acceptance consumes the US1 package.
- **US3 (P3)** is independently testable through the runtime after Foundation; it can be developed in
  parallel with US2 if edits to shared `model.py` and `cli.py` are coordinated.
- **US4 (P4)** intentionally consumes US1's release artifacts because update and removal are lifecycle
  operations on an installed bundle.

### Within Each User Story

- Write the listed tests and confirm the relevant tests fail for the intended missing behavior.
- Implement models and deterministic services before wiring agent command behavior.
- Exercise direct runtime integration before clean-project installed acceptance.
- Record evidence only from completed, reproducible commands; leave unavailable evidence `unknown`.
- Stop at each checkpoint and validate the story independently before moving to the next priority.

## Parallel Opportunities

### User Story 1

```text
T025 manifest contracts | T026 command contracts | T027 preset composition | T028 release contracts
T031 preset manifest    | T033 extension manifest | T034 command definitions | T036 bundle manifest
T081 explanation contracts | T082 published-route assertions
T084 child refinements      | T085 supplemental view sources
```

After those converge, complete T035 and T037-T043, then T083 and T086-T088, in dependency order.

### User Story 2

```text
T044 init envelope tests | T045 proposal/no-write tests
```

T046 then fixes the mutation boundary; T047 can proceed separately before T048-T052 integrate it.

### User Story 3

```text
T054 rule tests | T055 context tests | T056 validation tests | T057 result-contract tests
T059 context implementation | T060 initial parse-diagnostic implementation | T067 command definitions
```

Merge the ordered validation rule work T061-T065 before CLI and acceptance tasks T066-T070.

### User Story 4

```text
T071 update tests | T072 failure tests | T073 removal tests
```

These use separate test cases in the shared lifecycle file and require coordinated merges; T075 can
prepare versioned release inputs independently before T076-T080.

## Implementation Strategy

### MVP First

1. Complete Phase 1 so implementation has explicit ownership and contracts.
2. Complete Phase 2 so every operation shares deterministic, project-safe infrastructure.
3. Complete Phase 3 and stop for the US1 independent test.
4. Demonstrate native preview, install, exact component registration, and idempotency before adding
   architecture mutation behavior.

### Incremental Delivery

1. **US1**: Ship the inspectable bundle, append-only preset, extension, release tooling, and Codex
   command discovery.
2. **US2**: Add review-first root specification-hierarchy initialization without weakening source safety.
3. **US3**: Add bounded context and deterministic validation as read-only controls.
4. **US4**: Prove update, status, failure recovery, shared ownership, and removal against native Spec
   Kit behavior.
5. Add the text-backed ecosystem explanation and two supplemental views without changing the starter
   runtime surface.
6. Complete slash portability, self-application, generated-output freshness, and the human pilot.

## Notes

- `[P]` tasks touch distinct files or independently authored test areas; tasks sharing one file still
  require merge coordination even when their test cases can be designed concurrently.
- Spec Kit owns installation records, reference counting, rollback, update, and removal mechanics;
  Concorde supplies valid artifacts and acceptance evidence rather than reimplementing that lifecycle.
- `.concorde/`, `specs/`, and `docs/` are project-authored sources and MUST never be
  treated as extension-owned removal targets.
- The installed runtime remains Python 3.11 standard-library-only; `uv` is a contributor workflow and
  MUST NOT become a target-project runtime dependency.
- Archify HTML, Docusaurus output, release archives, and validation reports are reproducible evidence,
  not alternate maintained sources.
