# Tasks: [FEATURE]

**Input**: selected direct feature file, providing module `architecture.md`, source code and executable
tests/checks, and the returned stable-ID project-control attempt artifacts where present.

**Tests**: Include test-first tasks whenever the design or maintainer requires executable evidence.

## Concorde Task Coverage

Every task has at least one explicit trace: a requirement ID or acceptance-outcome trace,
architecture entity/relationship/interaction, embedded interface, named plan section, or
deterministic evidence gate.

Before finalizing, cover every affected:

- module `architecture.md` entity, relationship, interaction, inventory, decision, or diagram;
- selected or explicitly related direct feature file outcome, usage, interface, requirement, failure,
  Architecture Zoom, or relation;
- source-code and executable test path;
- executable interface fixture kept with source/tests;
- generated documentation/package/projection and freshness receipt; and
- migration, compatibility, user guide, reflection-path, and cleanup-only delivery readiness consequence.

For architecture-owned diagrams, include the textual architecture update, maintained JSON,
`meta.legend.mode: hidden`, unique normalized generated output, validation/delivery, freshness,
publication, and truthful visual-review result. Never create a diagram source inside a feature.

## Required Checklist Format

```text
- [ ] T001 [P?] [US?] Action with exact project-relative path [trace]
```

- IDs are sequential in dependency order.
- `[P]` appears only when files and incomplete dependencies do not overlap.
- `[USN]` appears on user-story phase tasks, not setup/foundational/polish tasks.
- Every description names an exact existing path or an intentional new path whose parent exists.
- Never create a task that edits generated output as intent.

## Phase 1: Setup and Protected Baseline

- [ ] T001 Record protected feature/architecture/related-summary digests and initial inventory in the returned `validation` file [Plan:Risk Controls]
- [ ] T002 [P] Add or migrate test fixtures in `[exact test paths]` [requirement trace]

## Phase 2: Foundational Work

**Goal**: Complete shared prerequisites that block every story.

- [ ] T003 [P] Write failing shared contract/unit tests in `[exact paths]` [requirement trace]
- [ ] T004 Implement shared model/runtime/configuration in `[exact paths]` [requirement trace]
- [ ] T005 Run focused foundational checks and record evidence in the returned `validation` file [plan gate]

## Phase 3: User Story 1 — [Title] (P1)

**Goal**: [Observable independently useful outcome.]

**Independent Test**: [Exact runnable scenario and expected result.]

- [ ] T006 [P] [US1] Write the failing story test in `[exact path]` [requirement]
- [ ] T007 [US1] Implement the story in `[exact source path]` [requirement]
- [ ] T008 [US1] Reconcile architecture/feature/interface/projection owners in `[exact paths]` [requirement]
- [ ] T009 [US1] Run the independent check and record evidence in the returned `validation` file [acceptance outcome]

## Phase 4+: Additional User Stories

Repeat the same goal, independent-test, test-first, implementation, authority reconciliation, and
evidence pattern for each priority. Keep stories independent after foundational work whenever the
design permits.

## Final Phase: Cross-Cutting Validation and Delivery Readiness

- [ ] TXXX Run full behavioral, architecture, interface, package, docs, and freshness checks [success criteria]
- [ ] TXXX Scan for legacy/stale authority references and unresolved reflection paths [migration]
- [ ] TXXX Record final protected digests, task/checklist completeness, limitations, and exact delivery remove path in the returned `validation` file [delivery]

## Evidence Before Completion

Before changing a task to `[X]`, the returned `validation` file names its ID/trace, actual command or check,
outcome (`passed` only authorizes completion), evidence path, and material limitation. A skipped,
failed, or missing required check leaves the task unchecked.

## Dependencies and Parallel Opportunities

- Setup precedes foundational work.
- Foundational work blocks all user stories.
- Story tests precede implementation; same-file tasks are sequential.
- Independent stories/files may run in parallel after shared prerequisites.
- Cross-cutting/full validation follows every desired story.
- Cleanup-only delivery is invoked only after every task/checklist/evidence item is complete.

## Implementation Strategy

Deliver the smallest independently useful story first, then add later stories without breaking prior
ones. A milestone is not deliverable while any declared architecture/feature/code/test/projection
authority disagrees or while required evidence is absent.
