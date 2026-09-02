# Tasks: Permission-Bounded Planning Operations

**Input**: selected feature, Operations architecture, `plan.md`, `research.md`, `data-model.md`,
`quickstart.md`, current source/tests, and the Protocol 13 attempt paths.

## Phase 1: Setup and Protected Baseline

- [ ] T001 Record current feature/architecture/constitution/related-summary digests, branch/worktree identity, capability inventory, and checklist 28/28 state in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [Plan:Risk Controls]
- [ ] T002 [P] Add failing capability metadata/exposure/nested-operation/cycle tests in `tests/concorde/unit/test_skill_assets.py`, `tests/concorde/unit/test_capability_validation.py`, and `tests/concorde/unit/test_capability_rules.py` [FR-001, FR-008, FR-013, FR-014]
- [ ] T003 [P] Add failing normalized-policy and Codex/Claude parity tests in `tests/concorde/unit/test_operation_permissions.py` [FR-002–FR-007, SC-001, SC-003]
- [ ] T004 [P] Add a two-module sentinel fixture and failing bounded planning-context tests in `tests/concorde/fixtures/permission-planning-project/` and `tests/concorde/unit/test_planning_context.py` [FR-003, FR-009, FR-010, SC-002]
- [ ] T005 [P] Add failing injectable process-launch/enforcement-receipt tests in `tests/concorde/unit/test_operation_executor.py` [FR-002, FR-005–FR-007]
- [ ] T006 [P] Add failing real-LangGraph context→author tests in `tests/concorde/integration/test_plan_operation.py` [FR-008, FR-011, SC-004]
- [ ] T007 [P] Revise outer graph tests to fail on flattened planning, stage-wide permission unions, unconditional reflection routes, and missing enforcement in `tests/concorde/integration/test_standard_dev_loop_operation.py` and `tests/concorde/integration/test_reflections_triage_operation.py` [FR-004, FR-012, FR-014, SC-006]

## Phase 2: Foundational Capability and Graph Model

**Goal**: Make capability authority, exposure, nesting, and per-leaf handoff deterministic before native policy work.

- [ ] T008 Extend canonical capability parsing with `exposure`, ordered `capabilities`, and leaf-owned `effects` in `src/concorde/skill_assets.py` [FR-001, FR-004, FR-008, FR-013]
- [ ] T009 Declare machine-readable effects on Operation-composed public leaves in `skills/concorde-analyze/SKILL.md`, `skills/concorde-deliver/SKILL.md`, `skills/concorde-fast-loop/SKILL.md`, `skills/concorde-implement/SKILL.md`, `skills/concorde-specify/SKILL.md`, `skills/concorde-tasks/SKILL.md`, and `skills/concorde-validate/SKILL.md` [FR-001, FR-004]
- [ ] T010 Implement mixed Skill/Operation topology validation, internal-exposure rules, exact literal/Markdown parity, and direct/indirect cycle diagnostics in `src/concorde/validation/capabilities.py` [FR-001, FR-008, FR-013, FR-014]
- [ ] T011 Refactor `src/concorde/operation_runtime.py` to ordered capability occurrences, one immutable per-leaf executor handoff/result, nested public Operation dispatch, exact prior-result propagation, and fail-fast stage ordering [FR-002, FR-004, FR-014]
- [ ] T012 Run the Phase 2 unit/integration subset and append passed evidence for T002/T008–T011 to `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [SC-001, SC-006]

## Phase 3: User Story 1 — Enforce Every Operation Launch (P1)

**Goal**: Resolve exact paths, render native least-privilege configurations, and prove an enforcement receipt before execution.

**Independent Test**: Every shipped direct leaf occurrence produces a distinct policy/config digest; unsafe, widened, or unenforceable policies invoke no subprocess or later node.

- [ ] T013 [US1] Implement trusted Protocol-13 role-to-path resolution, providing-module owned locators, required-interface owner specs, task-authorized paths, and symlink/escape rejection in `src/concorde/planning_context.py` and `src/concorde/feature_workspace.py` [FR-003, FR-009, FR-010]
- [ ] T014 [US1] Implement frozen effect/binding/policy/config/receipt models, subset validation, canonical digesting, Codex permission-profile rendering, Claude rules/strict-sandbox rendering, network/credential denial, and native parity comparison in `src/concorde/operation_permissions.py` [FR-001–FR-007, NFR-001–NFR-003]
- [ ] T015 [US1] Implement version/enforcement preflight plus injectable `codex exec`/`claude -p` process execution and structured receipts in `src/concorde/operation_executor.py` [FR-002, FR-005–FR-007]
- [ ] T016 [US1] Integrate describe-policy and execute host modes without eager LangGraph import into `src/concorde/operation_runtime.py` and both existing `operations/concorde-standard-dev-loop/operation.py` and `operations/concorde-reflections-triage/operation.py` [FR-002, FR-005–FR-007, NFR-001]
- [ ] T017 [US1] Run `tests.concorde.unit.test_operation_permissions`, `tests.concorde.unit.test_operation_executor`, and `tests.concorde.unit.test_planning_context`; record passed policy/path/parity/fail-closed evidence in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [SC-001–SC-003]

## Phase 4: User Story 2 — Plan Through Published Feature Boundaries (P1)

**Goal**: Keep `concorde-plan` public while hiding its context/author implementation and denying provider internals.

**Independent Test**: The real plan graph runs context→author; the author sees exact required provider feature specs/reasons and own-module locators, writes only the selected attempt/reflection path, and cannot read provider internals.

- [ ] T018 [US2] Replace `skills/concorde-plan/SKILL.md` with internal effect-declared `skills/concorde-plan-context/SKILL.md` and `skills/concorde-plan-author/SKILL.md`, preserving the former planning semantics only in the author leaf [FR-008–FR-011, FR-013]
- [ ] T019 [US2] Add the public paired `operations/concorde-plan/SKILL.md` and `operations/concorde-plan/operation.py` with exact context→author topology, policies, CLI modes, state, and failure propagation [FR-008, FR-011, FR-014, SC-004]
- [ ] T020 [US2] Migrate `operations/concorde-standard-dev-loop/SKILL.md` and `operations/concorde-standard-dev-loop/operation.py` to the nested public `concorde-plan` identity while retaining its public four-stage contract [FR-012, FR-014, SC-006]
- [ ] T021 [US2] Make `operations/concorde-reflections-triage/SKILL.md` and `operations/concorde-reflections-triage/operation.py` action/route conditional, retain nested public planning only on its planning branch, and keep investigators read-only plus implementers worktree-scoped [FR-012, FR-014]
- [ ] T022 [US2] Run the plan/standard/reflection Operation integration tests and sentinel context test; record passed graph order, nesting, branch, denial, and durable-hash evidence in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [SC-002, SC-004, SC-006]

## Phase 5: User Story 3 — Preserve Codex and Claude Parity (P2)

**Goal**: Package three Operations and two internal planner leaves while exposing the same bounded public capability in both agents.

**Independent Test**: A clean Codex and Claude installation contains 17 packaged leaves plus three pairs but projects 15 public leaves plus three Operations; `concorde-plan` is an Operation in both and native policy effective sets match.

- [ ] T023 [US3] Update `concorde.json` to Concorde 2.1.0 with 17 leaves/three Operations and update exact package validation in `scripts/install-concorde.py`, `scripts/release/build-release.py`, `scripts/release/verify-release.py`, and `scripts/release/publish-release.py` [FR-013]
- [ ] T024 [US3] Filter internal leaves from agent surfaces and preserve owned role transitions in `src/concorde/skill_assets.py`, `src/concorde/agent_assets.py`, `scripts/development/sync-agent-surfaces.py`, and `scripts/render-capability-surfaces.py` [FR-005, FR-006, FR-013]
- [ ] T025 [US3] Update manifest/install/projection/release/source-checkout unit, contract, integration, and acceptance expectations under `tests/concorde/` for 17 packaged leaves, three Operations, 18 public projections, `concorde-plan` kind transition, rollback/conflict safety, and policy provenance [FR-005, FR-006, FR-013, SC-003, SC-005]
- [ ] T026 [US3] Run `python3 scripts/development/sync-agent-surfaces.py apply --format json` to regenerate `.agents/skills/`, `.claude/skills/`, `.codex/agents/`, and `.claude/agents/`, then verify status is current and record exact output paths/digests in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [FR-005, FR-006, FR-013]
- [ ] T027 [US3] Run focused installation/projection/release/agent-surface tests and record passed Codex/Claude effective-boundary and public-surface parity evidence in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [SC-003, SC-005]

## Phase 6: Integration — Reconcile Architecture, Feature Authorities, and Projections

- [ ] T028 Amend `.concorde/constitution.md` to 7.1.0 and reconcile nested/internal/effect-controlled capabilities in `specs/concorde/features/007-project-ontology.md` and `templates/feature-template.md` without adding a compatibility reader [FR-001, FR-008, FR-013, FR-014]
- [ ] T029 Reconcile permission/compiler/launcher/planner entities, relationships, interactions, decisions, feature inventory, standard-loop contract, and selected feature details in `specs/concorde/modules/operations/architecture.md`, `specs/concorde/modules/operations/features/001-standard-development-loop.md`, and `specs/concorde/modules/operations/features/002-permission-bounded-planning.md` [contract.operations.permission-bounded-execution, contract.operations.plan]
- [ ] T030 Update the Operations system overview source in `specs/concorde/modules/operations/diagrams/system-overview.json` with principal policy, launcher, nested planner, and enforcement relationships while retaining `meta.quality_profile: showcase`, `meta.legend.mode: hidden`, and unique output `generated/architecture/concorde-operations-system-overview.html` [entity.operations.*, FR-014]
- [ ] T031 Reconcile only changed peer/root boundaries and feature promises in `specs/concorde/architecture.md`, `specs/concorde/modules/skills/architecture.md`, `specs/concorde/modules/skills/features/001-project-workflow.md`, `specs/concorde/modules/runtime/architecture.md`, `specs/concorde/modules/runtime/features/001-run-lifecycle-tools.md`, `specs/concorde/modules/workspace/architecture.md`, `specs/concorde/modules/workspace/features/001-manage-feature-workspace.md`, `specs/concorde/modules/distribution/architecture.md`, and `specs/concorde/modules/distribution/features/001-package-concorde.md`; update their system-overview JSON only where the principal entity graph changed [FR-003, FR-005, FR-006, FR-009, FR-013, FR-014]
- [ ] T032 Reconcile public workflow/planning/reflection/install/agent/release behavior in `specs/concorde/features/001-concorde-workflow.md`, `specs/concorde/features/003-installation.md`, `specs/concorde/features/004-agent-surfaces.md`, `specs/concorde/features/005-auto-reflections.md`, `specs/concorde/features/013-plan-delivery.md`, `specs/concorde/features/018-publish-release.md`, and `specs/concorde/features/019-one-command-install.md` [FR-008–FR-014]
- [ ] T033 Update planning/Operation/install guidance and exact public/package counts in `templates/plan-template.md`, `README.md`, `docs/concorde-workflow.md`, `docs/skills.md`, `docs/ontology.md`, `docs/agent-surfaces.md`, `docs/framework-overview.md`, `docs/project-structure.md`, and `docs/quick-start.md` [FR-005, FR-006, FR-008, FR-013, FR-014]
- [ ] T034 Validate every changed architecture diagram with all nine showcase checks, deliver its normalized unique HTML, run freshness/publication checks, and run `visual-check`; record zero errors/warnings and truthful inspected/skipped visual status in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [SC-005]

## Final Phase: Cross-Cutting Validation and Delivery Readiness

- [ ] T035 Run the complete Python suite with `uv run python -m unittest discover -s tests/concorde -t . -p 'test_*.py'` and record passed count/scope in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [SC-005]
- [ ] T036 Run `uv run python scripts/concorde.py validate --format json`, every declared Archify showcase validation, agent-surface freshness, installer/package verification, and `npm run check` in `docsite/`; record each result and limitation in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [SC-005]
- [ ] T037 Scan maintained sources/tests for stale `16 leaf`, `two Operation`, `skills/concorde-plan`, `OPERATION_SKILLS`, leaf-only composition, legacy Codex sandbox/profile mixing, and permissive Claude fallback references; reconcile only task-authorized occurrences [FR-005, FR-006, FR-008, FR-013, FR-014]
- [ ] T038 Record final protected/related-summary digests, changed-path/task authorization, 38/38 task and 28/28 checklist completion, enforcement limitations, clean tracked worktree status, and exact cleanup-only remove path in `.concorde/attempts/feature.operations.permission-bounded-planning/validation.md` [delivery readiness]

## Dependencies and Parallel Opportunities

- T002–T007 are parallel failing-test ownership lanes after T001.
- T008–T011 are sequential foundations; T012 gates all stories.
- T013–T016 are ordered by context → policy → executor → integration; T017 gates planning migration.
- T018–T021 have disjoint pairs after the shared runtime is stable, but T020/T021 depend on T019's public identity; T022 gates packaging.
- T023–T025 may proceed on disjoint implementation/test files; T026 follows all projection inputs and T027 follows sync.
- T028–T033 may be split by non-overlapping authority files after implementation behavior is fixed; T034 follows every diagram/text change.
- T035–T038 are sequential release/delivery gates.

## Implementation Strategy

Deliver the enforceable per-leaf policy/receipt foundation first, then the bounded public planner,
then integration parity and durable authority reconciliation. Implementation occurs on an explicit
isolated Git worktree. No task may mark complete without a matching passed evidence record.
