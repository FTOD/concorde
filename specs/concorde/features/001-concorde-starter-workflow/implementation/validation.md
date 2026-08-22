# Validation Record: Concorde Core Workflow Refactoring

**Feature**: `feature.concorde.core-workflow`  
**Attempt state**: active  
**Evidence status**: partial

This record belongs only to the current Feature 001 implementation attempt. Installation and bundle
lifecycle evidence remains under Feature 003.

## Baseline

- Existing deterministic operations: `init`, `context`, and `validate`.
- Existing installed command surfaces: three Concorde extension commands.
- Known gaps at attempt start: nested feature create/select, installable temporal-path composition,
  architecture-readiness output, feature-specific context, representation conformance, evidence
  disagreement, and generated-projection freshness.
- Baseline Python suite before this refactor: 54 passing tests.
- Baseline documentation gate before this refactor: 29 passing tests, 31 validated pages, successful
  production build.

## Automated Evidence

### Core workflow and compatibility

- `uv run python -m unittest discover -s tests/concorde -v`: 74 tests passed. The suite covers
  proposal safety, nested feature creation and selection, explicit resume handling, durable/temporal
  path routing, readiness review, bounded context, contract conformance, evidence/freshness findings,
  release determinism, installed command registration, and clean-project preset composition.
- Both supported command presentations were exercised: Codex skills and Gemini-style slash commands.
  The installed extension exposes five public Concorde commands; the preset contributes three
  append-only template fragments and nine append-only Spec Kit command-routing fragments.
- `uv run python extensions/concorde/scripts/python/concorde.py --project-root . validate`: success
  across 32 canonical architecture artifacts with zero errors, warnings, or informational findings.
  Final source digest:
  `sha256:81db4d56414740899124362993d5e7918c642578b0919506c36379fb7ad8fd68`.

### Architecture and documentation projections

- Archify showcase validation passed 9/9 checks with zero errors and zero warnings for both
  `specs/concorde/architecture.json` and
  `specs/concorde/modules/documentation/architecture.json`.
- Archify delivery regenerated `generated/architecture/concorde-root.html` and
  `generated/architecture/documentation.html`. Their source/artifact SHA-256 pairs are
  `0bb4ec…/ac3798…` and `b96cec…/a5d189…`, respectively. The root view now exposes
  all three root features and their user-to-module invocation paths.
- Browser visual checks were attempted but skipped because Chrome/Chromium is unavailable in the
  execution environment. Their receipts correctly retain `visualReview: pending`; structural
  validation is not presented as perceptual review.
- `npm run check` in `docsite/`: TypeScript passed, 14 test files and 29 tests passed, 31 pages were
  validated with 27 excluded sources and zero errors, and the production build was promoted to
  `docsite/build/`.

### Release and repository integrity

- `uv run python scripts/release/build-components.py --output dist --publish-catalogs` regenerated
  all component archives and catalogs. Release digests are `971965…` (extension), `2b2605…`
  (preset), and `af0581…` (bundle); the release contract test reproduced them byte-for-byte.
- Feature 002 and Feature 003 temporal artifacts were migrated below their own `implementation/`
  directories; no compatibility copies or symlinks remain at feature roots.
- `git diff --check`, Bash syntax checks, checked-in JSON parsing, and the required absence check for
  `.specify/extensions.yml` all passed.

## Human Evidence

- SC-001 placement pilot: pending real participants.
- SC-007 authority mental-model pilot: pending real participants.
- SC-008 reviewer approval: pending explicit maintainer review of the final architecture-source digest.

Automated tests must not be used to mark these human outcomes verified.
