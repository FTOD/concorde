# Tasks: Publish a Concorde Release

**Input**: Temporal design documents from `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/implementation/`, plus the durable `spec.md` and `contracts/release-publication.md` at the sub-feature root

**Prerequisites**: `implementation/plan.md`, `spec.md`, `implementation/research.md`, `implementation/data-model.md`, `implementation/quickstart.md`, `contracts/release-publication.md`

**Tests**: Included. The constitution (Principle VII) requires tests proportional to the change, and the plan names the test files; each story lists its tests before its implementation.

**Organization**: Phases follow the three user stories in `spec.md` (US1 publish, US2 discover, US3 trust). The selected root is an immediate sub-feature; every path below is either repository source or beneath this child root. No task edits `design.md`, removes `implementation/`, or touches the parent/sibling roots.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 from `spec.md`
- Exact repository-relative file paths are given in every task

## Path Conventions

- Release automation: `scripts/release/`, `.github/workflows/`
- Component manifests: `bundles/concorde-bundle/bundle.yml`, `presets/concorde-core/preset.yml`, `extensions/concorde/extension.yml`
- Tests: `tests/concorde/unit/`, `tests/concorde/contract/` (unittest, run with `uv run python -m unittest discover -s tests/concorde -p 'test_*.py'`)
- Docs: `docs/`, `README.md`
- Attempt evidence: `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/implementation/validation.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Correct the advertised repository and add the one dev dependency the new contract test needs.

- [X] T001 [P] Replace `repository: "https://github.com/concorde-workflow/concorde"` with `https://github.com/FTOD/concorde` in `presets/concorde-core/preset.yml` and `extensions/concorde/extension.yml` (research R3)
- [X] T002 [P] Add `jsonschema` to the `dev` dependency group in `pyproject.toml` and refresh `uv.lock` with `uv lock`; confirm `uv sync` succeeds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Make the bundle manifest the single version authority and make the verifier able to prove the published base URL. Every story depends on these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Refactor `scripts/release/build-components.py`: add `REPOSITORY = "https://github.com/FTOD/concorde"`; add `read_release_version()` that reads `bundle.version` from `bundles/concorde-bundle/bundle.yml` and raises a named error unless `provides.presets[0].version`, `provides.extensions[0].version`, `presets/concorde-core/preset.yml` `preset.version`, and `extensions/concorde/extension.yml` `extension.version` all equal it; add `default_base_url(version)` returning `f"{REPOSITORY}/releases/download/v{version}"`; use `REPOSITORY` for the catalog `repository` field; remove the `--version` CLI flag and the `VERSION` constant; add `--print-version` that prints the manifest version and exits (research R2)
- [X] T004 Extend `scripts/release/verify-release.py`: add `--expect-version` and `--expect-base-url`; fail when any catalog `version` differs from the expected version, when any `catalog_url` or `download_url` does not start with the expected base URL, or when a manifest `repository` differs from the builder's `REPOSITORY`; keep accepting `http://127.0.0.1:` bases when `--expect-base-url` is omitted (research R10); derive the version via the builder's `read_release_version()` instead of a constant
- [X] T005 Update `tests/concorde/contract/test_release_artifacts.py`: remove the comparison against the git-ignored `catalogs/` directory (research R9); assert default catalogs use HTTPS, start with `https://github.com/FTOD/concorde/releases/download/v<version>`, and carry `repository == REPOSITORY`; add a test that `read_release_version()` raises when a manifest version is patched to disagree; add a test that `verify_release` rejects a wrong `--expect-version` and a wrong `--expect-base-url`
- [X] T006 Run `uv run python -m unittest discover -s tests/concorde -p 'test_*.py'` and fix any regression caused by T003–T005 (the localhost acceptance fixtures must remain green)

**Checkpoint**: One version authority, truthful repository URL, verifier can prove the published base — story work can begin

---

## Phase 3: User Story 1 - Publish a tagged release (Priority: P1) 🎯 MVP

**Goal**: A `v<version>` tag builds, verifies, and publishes the seven assets at the advertised locations with no manual step; verification failure or version mismatch publishes nothing.

**Independent Test**: Trigger the workflow with `dry_run=true` and see the ordered plan; then push `v0.1.0` and, from a machine without the checkout, register the three published catalogs in a fresh project and preview the bundle (quickstart §3–§5).

### Tests for User Story 1

- [X] T007 [P] [US1] Create `tests/concorde/unit/test_publish_release.py` with a fake `gh` (a recorded-command stub injected via `--gh` or a `GhClient` seam) covering: absent release → `create --draft --verify-tag`, seven `upload` calls, then `edit --draft=false` as the last mutating call; `--dry-run` → outcome `dry-run`, plan printed, zero gh calls; tag `v9.9.9` against manifest `0.1.0` → exit 1 outcome `version-mismatch` naming both values; verifier failure → exit 1 outcome `verification-failed` and zero gh mutations; pre-release version (`0.2.0-rc.1`) → `--prerelease` on create; leftover draft → assets deleted and re-uploaded, then published
- [X] T008 [P] [US1] Create `tests/concorde/contract/test_release_publication.py` with a workflow-shape test: `.github/workflows/publish-release.yml` parses as YAML, triggers on `push.tags: ['v*']` and `workflow_dispatch` with a boolean `dry_run` input, declares `permissions.contents: write`, and orders steps so tests → build → `verify-release.py` → `publish-release.py` (assert by step names)

### Implementation for User Story 1

- [X] T009 [US1] Create `scripts/release/publish-release.py`: CLI `--dist`, `--tag`, `--dry-run`, `--compare-only`, `--gh` (default `gh`); load `dist/*.json`; compute version via the builder's `read_release_version()` and require `tag == f"v{version}"`; detect pre-release suffix; implement the decision engine from `implementation/data-model.md` (absent → draft → upload 7 assets → publish; leftover draft → repair); print a Publication Record JSON (`outcome`, `plan`, `compared`, `residual_state`) on stdout; exit codes 0 published/already-published/dry-run, 1 version-mismatch/verification-failed, 2 divergent; never pass `--clobber` (research R4)
- [X] T010 [US1] Add `render_notes(version, catalogs, speckit_range, base_url)` to `scripts/release/publish-release.py` producing deterministic release notes with component ids/versions, supported Spec Kit range, digest table, the three `specify … catalog add` commands, and a link to `docs/quick-start.md`; pass via `--notes-file` on create (research R7); add a unit test in `tests/concorde/unit/test_publish_release.py` asserting the notes contain `concorde-core@<version>`, `concorde@<version>`, and the Spec Kit range (FR-009)
- [X] T011 [US1] Create `.github/workflows/publish-release.yml`: `on: push: tags: ['v*']` and `workflow_dispatch: inputs.dry_run (boolean, default true)`; `permissions: contents: write`; `concurrency: release-${{ github.ref }}`; steps: checkout, `astral-sh/setup-uv` with Python 3.11, `uv sync`, `uv run python -m unittest discover -s tests/concorde/unit -p 'test_*.py'`, `uv run python -m unittest discover -s tests/concorde/contract -p 'test_release*.py'`, `uv run python scripts/release/build-components.py --output dist`, `uv run specify bundle build --path bundles/concorde-bundle --output dist`, `uv run python scripts/release/verify-release.py --dist dist --expect-version "$(uv run python scripts/release/build-components.py --print-version)" --expect-base-url "https://github.com/FTOD/concorde/releases/download/${TAG}"`, then `uv run python scripts/release/publish-release.py --dist dist --tag "$TAG"` with `--dry-run` when the dispatch input is true; `TAG` is `github.ref_name` on tag pushes and `v$(--print-version)` on dispatch; append the Publication Record JSON to `$GITHUB_STEP_SUMMARY` (research R5, R6)
- [ ] T012 [US1] Rehearse: run the workflow via `workflow_dispatch` with `dry_run=true`; record run URL, printed plan, and elapsed time in `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/implementation/validation.md` (quickstart §3)
- [ ] T013 [US1] Publish `v0.1.0` (maintainer action: `git tag v0.1.0 && git push origin v0.1.0` after Phase 1–2 changes are merged to `main`); record release URL, the seven asset names, tag-to-published duration (SC-001 < 15 min), and the clean-project catalog registration + `specify bundle info concorde-bundle --json` result from quickstart §5 (SC-003 < 2 min) in `implementation/validation.md`

**Checkpoint**: A real published release exists and installs from a clean project with public Spec Kit commands only

---

## Phase 4: User Story 2 - Discover the current release (Priority: P2)

**Goal**: A consumer reads one stable location and learns the current version and its catalog URLs; older versions stay unchanged.

**Independent Test**: `curl -fsSL https://github.com/FTOD/concorde/releases/latest/download/release.json` returns `version` and three catalog URLs; after a later version publishes it returns the newer one while the `v0.1.0` locations are unchanged (quickstart §6).

### Tests for User Story 2

- [X] T014 [P] [US2] Add to `tests/concorde/contract/test_release_publication.py`: extract the JSON Schema and example from `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/contracts/release-publication.md` and validate the example with `jsonschema`; build a release into a temp dir, generate `release.json` with the publisher's `build_release_pointer()`, validate it against the same schema, and assert `archives` digests equal the catalogs' `sha256` values, `catalogs` URLs equal each catalog's `catalog_url`, and no key is named `published_at`/`updated_at`
- [X] T015 [P] [US2] Add to `tests/concorde/unit/test_publish_release.py`: `release.json` is among the seven uploaded assets; for a pre-release version the pointer carries `"prerelease": true` and the release is created with `--prerelease`; `edit --draft=false` is the final gh call so the `latest` alias can only observe a complete release (FR-007)

### Implementation for User Story 2

- [X] T016 [US2] Implement `build_release_pointer(dist, version, tag, base_url, speckit_range, prerelease)` in `scripts/release/publish-release.py` that writes `dist/release.json` exactly per the schema in `contracts/release-publication.md` (`schema_version "1.0"`, `version`, `tag`, `repository`, `base_url`, `speckit_version` from `bundle.yml` `requires.speckit_version`, `bundle_id`, optional `prerelease`, `catalogs`, `archives`), with sorted keys and no wall-clock fields; include it in the asset upload list (research R8)
- [ ] T017 [US2] After T013 has published, fetch `https://github.com/FTOD/concorde/releases/latest/download/release.json`, confirm `version == "0.1.0"` and the three catalog URLs point under `…/download/v0.1.0/`, and record the output in `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/implementation/validation.md` (quickstart §6); note that the "newer version supersedes" scenario is verifiable only at the next release and mark it pending

**Checkpoint**: The pointer resolves to the published version and validates against the contract schema

---

## Phase 5: User Story 3 - Trust what was published (Priority: P2)

**Goal**: Published assets are reproducible from the tagged sources, re-publication of the same version is a byte-safe no-op, and any divergence is refused.

**Independent Test**: Re-run the workflow for `v0.1.0` → `already-published`, no changes; in a scratch clone alter one allowlisted preset file, rebuild, run the publisher with `--compare-only` → exit 2 `divergent` naming the asset (quickstart §7).

### Tests for User Story 3

- [X] T018 [P] [US3] Add to `tests/concorde/unit/test_publish_release.py`: existing published release with identical catalog digests and URLs → outcome `already-published`, exit 0, no `upload`/`edit`/`delete` calls; one differing archive digest → outcome `divergent`, exit 2, `compared` lists that asset, no mutating calls; `--compare-only` never mutates even when the release is absent (outcome `absent`)

### Implementation for User Story 3

- [X] T019 [US3] Implement the comparison path in `scripts/release/publish-release.py`: when `gh release view <tag> --json isDraft,assets` shows a published release, download its `extensions.json`, `presets.json`, `bundles.json`, and `release.json` with `gh release download <tag> --pattern` into a temp dir and compare each catalog entry's `version`, `download_url`, `catalog_url`, and `sha256` plus the pointer's `archives` with the local `dist/`; identical → `already-published`; otherwise `divergent` with the field-level differences; treat a missing published asset as divergent (research R4, FR-006)
- [ ] T020 [US3] Live evidence after T013: re-dispatch the workflow for the `v0.1.0` ref with `dry_run=false` and confirm `already-published`; in a fresh clone at tag `v0.1.0` run `build-components.py` + `verify-release.py` and compare the seven digests with the published `release.json` (SC-002 = 100% match); record both in `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/implementation/validation.md` (quickstart §7)

**Checkpoint**: Reproducibility and immutability are demonstrated against the live release

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, architecture bookkeeping, and the final validation pass.

- [X] T021 [P] Create `docs/releasing.md` (frontmatter `title: Releasing Concorde`, `sidebar_position: 8`): version bump procedure (edit `bundle.yml` pins and both manifests together), dry-run rehearsal, tagging, what the workflow does, pre-release suffix behaviour, immutability rules (never delete or move a published tag; a changed release needs a new version), and how to read the Publication Record (research R11)
- [X] T022 [P] Update `docs/quick-start.md`: insert a new section "Install from the published release" before the current "2. Build the current local release" showing `specify init`, the three `catalog add` commands using `https://github.com/FTOD/concorde/releases/download/v0.1.0/…`, `specify bundle install concorde-bundle`, and the `releases/latest/download/release.json` pointer; retitle the existing build/serve sections as the development path and keep them intact (FR-010)
- [X] T023 [P] Update `README.md`: in the Spec Kit installation orientation, link the published-release install section of `docs/quick-start.md` and the new `docs/releasing.md`
- [X] T024 Confirm the diagram decision for this child: `spec.md` declares no `role: core` or `role: supplemental` diagram and keeps its sufficiency rationale (parent views cover release→discovery→install), no `diagrams/` directory is created under `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/`, and `npm --prefix docsite run validate` still publishes the feature page without diagram embeds
- [X] T025 Create `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/implementation/validation.md` (if not already started by T012) consolidating automated evidence (test commands and results from T006–T019), live evidence (T012, T013, T017, T020), and outstanding items; then set `evidence_status` in `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/spec.md` to `partial` once automated evidence passes and to `verified` only after the live steps are recorded
- [X] T026 Run `.specify/extensions/concorde/scripts/bash/concorde.sh validate --format json`, `uv run python -m unittest discover -s tests/concorde -p 'test_*.py'`, and `npm --prefix docsite run check`; record the three results in `implementation/validation.md` and fix anything red before declaring the attempt task-complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 and T002 are independent and can start immediately
- **Foundational (Phase 2)**: T003 depends on T001 (repository constant must match the manifests); T004 depends on T003; T005 depends on T003–T004; T006 depends on T005 — this phase BLOCKS all stories
- **US1 (Phase 3)**: depends on Phase 2; T007/T008 in parallel first, then T009 → T010 → T011 → T012 → T013
- **US2 (Phase 4)**: T014/T015 can be written in parallel with US1 tests; T016 depends on T009; T017 depends on T013
- **US3 (Phase 5)**: T018 can be written in parallel with other tests; T019 depends on T009; T020 depends on T013 and T019
- **Polish (Phase 6)**: T021–T023 in parallel any time after Phase 2; T024 any time; T025–T026 last

### User Story Dependencies

- **US1 (P1)**: independent after Phase 2; delivers the MVP (a real published release)
- **US2 (P2)**: the pointer file is produced by the same publisher (T016 extends T009) but is testable on its own with the contract test T014; live check needs US1's release
- **US3 (P2)**: the comparison path extends the publisher; its unit tests are independent; live check needs US1's release

### Within Each User Story

- Tests are written first and must fail before the implementation task lands
- Publisher logic before workflow wiring; workflow rehearsal (dry-run) before the live tag
- Live evidence tasks (T013, T017, T020) require a maintainer with push rights to `FTOD/concorde` and are the only tasks that touch the public location

### Parallel Opportunities

- T001 ∥ T002
- T007 ∥ T008 ∥ T014 ∥ T015 ∥ T018 (all test files, distinct or additive)
- T021 ∥ T022 ∥ T023 (distinct docs files)
- US2 and US3 implementation (T016, T019) both edit `scripts/release/publish-release.py` — sequence them, do not parallelize

---

## Parallel Example: User Story 1

```bash
# Write both US1 test files together (they fail until T009–T011 exist):
Task: "Unit tests with fake gh in tests/concorde/unit/test_publish_release.py"
Task: "Workflow-shape contract test in tests/concorde/contract/test_release_publication.py"

# Then implement sequentially (same publisher file, then workflow):
Task: "scripts/release/publish-release.py decision engine"      # T009
Task: "render_notes in scripts/release/publish-release.py"      # T010
Task: ".github/workflows/publish-release.yml"                   # T011
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (T001–T002) and Phase 2 (T003–T006): truthful URLs, one version authority, verifier proves the base URL
2. Phase 3 (T007–T011): publisher + workflow, green unit/contract tests
3. **STOP and VALIDATE**: T012 dry-run rehearsal; then T013 publishes `v0.1.0` and the clean-project check passes
4. At this point the sibling `one-command-install` feature has a real release to target

### Incremental Delivery

1. Add US2 (T014–T017): `release.json` pointer, contract-validated, live pointer check
2. Add US3 (T018–T020): idempotent re-run and divergence refusal proven live
3. Polish (T021–T026): docs, evidence consolidation, final gates

### Notes

- `design.md` stays untouched; after every task is complete and `validation.md` is accepted, the maintainer may run `speckit.concorde.feature.harden` separately
- The localhost catalog-server path used by acceptance tests is never modified (FR-010)
- Do not add `--clobber`, `--version`, or timestamps anywhere in the release path; those would break immutability, the single version authority, or determinism respectively
