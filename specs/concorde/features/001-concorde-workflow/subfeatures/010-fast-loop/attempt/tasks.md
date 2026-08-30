# Tasks: Relax Fast-Loop Eligibility

**Input**: `attempt/plan.md`, `design.md`, `implementation.md`, `attempt/research.md`,
`attempt/data-model.md`, `attempt/quickstart.md`, and `contracts/fast-loop-command.md`

**Tests**: Required by FR-011, SC-006, SC-007, and SC-008.

**Organization**: Tasks are grouped by the three user stories in `design.md`. Parent/project durable
authority paths are explicit coordinated edits authorized by the maintainer's all-related-sources
request and tracked by R-027/R-035; no parent or sibling attempt is read or written.

## Phase 1: Setup (Shared Evidence)

**Purpose**: Record the accepted baseline, current worktree, canonical policy source, installed
projections, and validation surfaces before implementation.

- [X] T001 Record pre-existing worktree paths, hashes for the child/parent durable authorities and canonical command, and current self-host status in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md`
- [X] T002 [P] Verify every planned source and test path exists and record obsolete policy occurrences from `rg` in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md`

---

## Phase 2: Foundational (Policy Contract Tests)

**Purpose**: Encode the relaxed eligibility matrix before changing the canonical instruction.

**⚠️ CRITICAL**: Complete this phase before command and documentation reconciliation.

- [X] T003 [P] Add canonical command/contract assertions for anchor-plus-affected-set resolution, all-root accepted/no-attempt baselines, allowed cross-feature/contract detail, stable module boundaries, project-level compatibility policy, and architecture review state in `tests/concorde/contract/test_agent_commands.py`
- [X] T004 [P] Add installed Codex fast-loop semantic parity assertions in `tests/concorde/contract/test_installed_command_surfaces.py`
- [X] T005 [P] Add installed Gemini slash-command semantic parity assertions in `tests/concorde/acceptance/test_installed_slash_workflow.py`
- [X] T006 [P] Add self-hosted Codex/Claude fast-loop semantic parity assertions in `tests/concorde/acceptance/test_self_hosted_checkout.py`
- [X] T007 Add read-only repeated explicit-root resolution evidence that leaves the standard selection unchanged in `tests/concorde/unit/test_feature_workspace.py`

**Checkpoint**: Policy tests fail only because maintained/materialized command wording is still old.

---

## Phase 3: User Story 1 - Complete a Small Coordinated Change Directly (Priority: P1) 🎯 MVP

**Goal**: Permit a bounded change to reconcile every related existing feature and inter-module
contract/format/diagram detail without changing module responsibilities or dependencies.

**Independent Test**: The canonical and installed commands treat the selected root as an anchor,
resolve every affected root independently, require accepted/no-attempt baselines for all, allow
bounded cross-feature and contract-detail reconciliation, and update every related authority.

### Tests for User Story 1

- [X] T008 [US1] Run the new US1 policy assertions in `tests/concorde/contract/test_agent_commands.py` and confirm they fail against the old command surface

### Implementation for User Story 1

- [X] T009 [US1] Replace one-feature eligibility with anchor discovery, repeated affected-root workspace resolution, all-root baselines/hashes, and complete affected-source reconciliation in `presets/concorde/commands/speckit.fast-loop.md`
- [X] T010 [P] [US1] Reconcile durable-write and repeated-root phase authority in `specs/concorde/features/001-concorde-workflow/contracts/architecture-sources.md`
- [X] T011 [P] [US1] Add the additive fast-loop distribution obligation to `specs/concorde/features/001-concorde-workflow/contracts/agent-commands.md`
- [X] T012 [P] [US1] Reconcile the project workflow boundary obligation for one anchor plus related affected roots in `specs/concorde/architecture/contracts/concorde-workflow/contract.md`
- [X] T013 [US1] Reconcile parent aggregate fast-loop behavior and requirements without changing normal one-root phase selection in `specs/concorde/features/001-concorde-workflow/design.md` and `specs/concorde/features/001-concorde-workflow/abstract.md`
- [X] T014 [US1] Draft the root module design-reference amendment for repeated fast-loop root resolution and related authority writes in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md` for acceptance to apply to `specs/concorde/design.md`
- [X] T015 [US1] Update anchor/affected-set and architecture-authority wording while preserving topology and hidden legend policy in `specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json` and `specs/concorde/architecture/diagrams/skill-workspace-file-flow.json`

**Checkpoint**: Canonical behavior, parent/project authorities, and architecture views agree; module
responsibility and dependency declarations remain byte-identical.

---

## Phase 4: User Story 2 - Escalate Only Boundary or Project-Policy Work (Priority: P1)

**Goal**: Reject significant architecture and whole-project user compatibility/migration changes,
while no longer rejecting internal contract/format or cross-feature coordination categorically.

**Independent Test**: Policy tests distinguish allowed internal contract/format changes from rejected
module responsibility, dependency-direction, and whole-project user policy changes; all prior
baseline, active-attempt, worktree, clarity, and new-structure stops remain.

### Tests for User Story 2

- [X] T016 [US2] Run the US2 rejection matrix in `tests/concorde/contract/test_agent_commands.py` and verify obsolete blanket-rejection phrases are absent

### Implementation for User Story 2

- [X] T017 [P] [US2] Update the command reference and command-choice table for boundary/project-policy eligibility in `docs/commands.md`
- [X] T018 [P] [US2] Update fast-path explanation and architecture review timing in `docs/concorde-workflow.md`
- [X] T019 [P] [US2] Update concise command summaries and eligibility examples in `README.md` and `docs/quick-start.md`

**Checkpoint**: Public guidance matches the canonical eligibility matrix without changing project
compatibility policy itself.

---

## Phase 5: User Story 3 - Finish With Complete Evidence and Architecture Review State (Priority: P2)

**Goal**: Report the anchor, complete affected set, per-feature documentation impact, checks, and an
explicit architecture review state; a maintained architecture edit cannot be final while pending.

**Independent Test**: Canonical, Codex, Claude, and Gemini presentations all require the same report,
and an architecture-source edit transitions from `review_pending` to `reviewed` only after exact
maintainer confirmation without creating an attempt or acceptance proposal.

### Tests for User Story 3

- [X] T020 [US3] Run the US3 completion/report assertions across `tests/concorde/contract/test_agent_commands.py`, `tests/concorde/contract/test_installed_command_surfaces.py`, `tests/concorde/acceptance/test_installed_slash_workflow.py`, and `tests/concorde/acceptance/test_self_hosted_checkout.py`

### Implementation for User Story 3

- [X] T021 [US3] Ensure completion, failure, hook, and reflection sections preserve prior safeguards and add per-feature hashes/impact plus `not_required`/`review_pending`/`reviewed` reporting in `presets/concorde/commands/speckit.fast-loop.md`
- [X] T022 [US3] Record the proposed child and parent accepted-realization deltas, architecture sources requiring review, and exact validation results in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md`

**Checkpoint**: All three user stories are independently represented and testable in every supported
presentation.

---

## Phase 6: Materialization, Validation, and Review

**Purpose**: Refresh generated/installed projections through existing scripts, prove script/runtime
stability, and prepare an acceptance-quality evidence record.

- [X] T023 Refresh canonical preset and installed Codex/Claude fast-loop projections through `scripts/development/self-host-concorde.py` and verify `.specify/presets/concorde/commands/speckit.fast-loop.md`, `.agents/skills/speckit-fast-loop/SKILL.md`, and `.claude/skills/speckit-fast-loop/SKILL.md`
- [X] T024 [P] Run focused command, workspace, installed-surface, and self-host tests and record results in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md`
- [X] T025 [P] Run component build/release verification to exercise unchanged packaging scripts and record results in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md`
- [X] T026 Validate and deliver both maintained Archify JSON sources, verify generated freshness/automatic publication, and record visual-review status in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md`
- [X] T027 Run deterministic Concorde validation, the full Python suite, and the docsite check and record results in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md`
- [X] T028 Review final `git diff`, obsolete-policy search, unrelated worktree preservation, checklist completion, and task state in `specs/concorde/features/001-concorde-workflow/subfeatures/010-fast-loop/attempt/validation.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup; blocks user-story implementation.
- **User Story 1 (Phase 3)**: Depends on policy tests and establishes the canonical model.
- **User Story 2 (Phase 4)**: Depends on T009 and can proceed in parallel with US1 contract/view
  reconciliation after the command matrix is stable.
- **User Story 3 (Phase 5)**: Depends on T009 and T003–T006; reporting semantics can be completed after
  the core command model exists.
- **Materialization/Validation (Phase 6)**: Depends on every desired user story.

### User Story Dependencies

- **US1 (P1)**: Core MVP; no dependency on US2/US3.
- **US2 (P1)**: Uses US1's anchor/affected model but is independently testable through rejection cases.
- **US3 (P2)**: Uses US1's affected set and architecture sources but is independently testable through
  completion/review-state cases.

### Parallel Opportunities

- T003–T006 can run in parallel across distinct test files.
- T010–T012 can run in parallel after T009 establishes terminology.
- T017–T019 can run in parallel after the canonical command is stable.
- T024 and T025 can run in parallel after materialization; T026 and T027 should run after all
  maintained architecture/doc sources are final.

## Parallel Example: User Story 1

```text
Task T010: Reconcile architecture-sources phase authority.
Task T011: Reconcile agent-command distribution handoff.
Task T012: Reconcile project workflow boundary contract.
```

## Implementation Strategy

### MVP First

1. Complete Setup and policy contract tests.
2. Implement the anchor/affected-set command model.
3. Reconcile its parent/project contract and diagram authorities.
4. Run the US1 policy tests independently.

### Incremental Delivery

1. US1 enables bounded multi-feature/contract work.
2. US2 narrows rejection to module boundaries and project-level user policy.
3. US3 adds architecture review and complete evidence reporting.
4. Materialize once, then run focused and full validation.

## Notes

- Every task uses the existing Protocol v8 adapter; no Python runtime/schema change is planned.
- `.specify/feature.json` remains a single anchor pointer and is not a multi-selection registry.
- Generated HTML is validation output, never maintained intent.
- Do not update either accepted `implementation.md` during task execution; draft both realization
  deltas in `attempt/validation.md` for explicit acceptance/review.
- Architecture JSON and contract changes require exact maintainer review before durable acceptance.
