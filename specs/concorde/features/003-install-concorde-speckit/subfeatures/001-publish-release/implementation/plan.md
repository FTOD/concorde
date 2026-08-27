# Implementation Plan: Publish a Concorde Release

**Branch**: `main` (no feature branch hook configured) | **Date**: 2026-08-27 | **Spec**: [spec.md](../spec.md)

**Input**: Feature specification from `specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/spec.md`

**Selected level**: Immediate sub-feature of `feature.concorde.install-with-spec-kit`. The parent
`spec.md`/`design.md` and the sibling summary are aggregate context only; this attempt writes only
beneath this child root.

## Summary

Turn the existing deterministic release build into a published release. A version tag on the
maintained sources triggers an automated job that builds the three archives and three catalogs with
the parent's builder, verifies them, and publishes them as immutable release assets at the exact
locations the catalogs advertise. A small `release.json` pointer asset, reachable through the
hosting platform's stable "latest release" location, lets consumers and the sibling installer
discover the current version without hard-coding it. Publication is atomic (assets are uploaded to a
draft and the release is published only when complete), idempotent for an identical re-run, and
refuses version mismatches, verification failures, and divergent re-publication. The advertised
repository is corrected from `concorde-workflow/concorde` to the maintained `FTOD/concorde`.

## Technical Context

**Language/Version**: Python 3.11 (release scripts), GitHub Actions YAML (publication job), POSIX shell only inside workflow steps

**Primary Dependencies**: `uv` (environment), `specify-cli==0.16.4` (bundle build/validate and consumer-side catalog resolution), GitHub CLI `gh` (release creation, asset upload, existing-release inspection; preinstalled on hosted runners), existing `scripts/release/build-components.py` and `scripts/release/verify-release.py`

**Storage**: GitHub Releases assets (immutable per tag) as the public location; `dist/` as local build output (ignored); no database

**Testing**: `uv run python -m unittest discover -s tests/concorde -p test_*.py` (contract + unit tests for the builder, verifier, and publisher with a fake `gh`); workflow rehearsal through `workflow_dispatch` dry-run; post-publication clean-project check with the public Spec Kit CLI

**Target Platform**: GitHub-hosted Linux runner for publication; any platform with the pinned Spec Kit CLI for consumption

**Project Type**: Release automation for an existing CLI-distributed component set

**Performance Goals**: Tag-to-published in under 15 minutes (SC-001); consumer catalog registration and bundle preview in under 2 minutes (SC-003)

**Constraints**: Catalog URLs must be HTTPS with a host (Spec Kit rejects anything else and re-validates every redirect hop); version-specific locations immutable; no manual upload steps; the localhost development path must keep working unchanged; build stays deterministic (no timestamps or run identifiers inside archives or catalogs)

**Scale/Scope**: One release line, three archives + three catalogs + one pointer + notes per version; first published version is `0.1.0`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Evaluation | Status |
|---|---|---|
| I. Product and proving ground | Publication makes the bundle actually installable by other projects, closing the parent design's stated limitation ("publication transport is a separate release operation"). Concorde's own quick start will consume the published release. | Pass |
| II. Spec Kit-native and composable | Publication emits only Spec Kit 0.16.4 catalog and archive formats produced by the existing builder; consumers use public `specify … catalog add` and `bundle install`. No new install mechanism. | Pass |
| III. Bounded architecture | No module or hierarchy change; the child inherits `module.concorde` and refines the parent's release/discovery stages. | Pass |
| IV. Ownership | Parent owns package content and lifecycle; this child owns publication transport, location truthfulness, immutability, and discovery. No duplication of parent facts. | Pass |
| V. Contracts govern boundaries | The pointer asset is a new consumer-facing interface, so it gets a feature-local interface profile with a normative JSON schema, field semantics, compatibility rules, an example, and a contract test (`contracts/release-publication.md`). Catalog and archive formats stay governed by the parent's `bundle-distribution.md`. | Pass |
| VI. One authority per fact | Today the version is written in four places (builder constant, bundle, preset, extension manifests) and the repository URL in three. The plan makes the bundle manifest the single version authority read by the builder, requires preset/extension equality, and requires the tag to equal it; the repository URL becomes one builder constant that manifests are checked against. | Pass (after Phase 1 decisions) |
| VII. Deterministic validation | Verification is the existing byte-equivalent rebuild plus digest checks; publication compares digests, never timestamps. Human review happens at tag creation (a maintainer action) and by reading the dry-run plan. | Pass |
| Product requirement: automated fixture per supported Spec Kit version | Unchanged; the release job runs the existing contract tests before publishing. | Pass |

No violations; Complexity Tracking is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/concorde/features/003-install-concorde-speckit/subfeatures/001-publish-release/
├── spec.md
├── design.md                      # accepted baseline: no hardened realization (unchanged by this attempt)
├── contracts/
│   └── release-publication.md     # interface profile: release layout + release.json pointer schema
└── implementation/
    ├── checklists/requirements.md
    ├── plan.md                    # this file
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── tasks.md                   # $speckit-tasks output (not created here)
    └── validation.md              # attempt evidence (implementation phase)
```

### Source Code (repository root)

```text
.github/workflows/
└── publish-release.yml            # NEW: on tag v*, and workflow_dispatch(dry_run)

scripts/release/
├── build-components.py            # CHANGE: version read from bundle.yml; repository constant → FTOD/concorde;
│                                  #         default base URL derived from repository + version
├── verify-release.py              # CHANGE: --expect-version / --expect-base-url; manifest version equality
└── publish-release.py             # NEW: plan/publish/no-op/fail logic over `gh`; writes release.json + notes

presets/concorde-core/preset.yml   # CHANGE: repository URL
extensions/concorde/extension.yml  # CHANGE: repository URL

docs/
├── quick-start.md                 # CHANGE: add "Install from the published release" before the dev path
└── releasing.md                   # NEW: maintainer release procedure (tag → publish → verify)
README.md                          # CHANGE: link to releasing guide / published install

tests/concorde/
├── contract/test_release_artifacts.py     # CHANGE: drop dependence on ignored catalogs/; assert FTOD URLs
├── contract/test_release_publication.py   # NEW: release.json schema + example conformance; workflow shape
└── unit/test_publish_release.py           # NEW: publisher decisions with a fake gh (new / identical / divergent / mismatch / partial)
```

**Structure Decision**: Publication logic lives in a testable Python script beside the existing
release scripts; the workflow YAML only sequences `uv sync`, tests, build, verify, and the publisher.
That keeps every decision (version equality, no-op vs conflict, draft-then-publish) under unit test
rather than buried in shell steps.

## Feature Diagram Strategy

No core diagram: the spec records that the parent's `spec-kit-component-model.json` (core) and
`bundle-installation-flow.json` (supplemental) already show release, discovery, and installation;
this child inserts one "publish" step between "release built and verified" and "catalog
discovered" and adds no new component. The `Publish a tagged release` scenario is an ordered
sequence of five steps that prose describes completely (see research R6), so no supplemental view
is planned. If implementation reveals a branching state machine worth showing (for example the
draft/identical/divergent outcomes), a `role: supplemental` lifecycle diagram
`diagrams/release-publication-lifecycle.json` may be added under this child's `diagrams/` with a
declaration in `spec.md`, Archify 2.16 showcase validation, and the docsite freshness check — that
is an optional task, not a promise.

## Phase 0: Research

See [research.md](research.md). All Technical Context items are resolved; no NEEDS CLARIFICATION
remains.

## Phase 1: Design

- [data-model.md](data-model.md) — Published Release, Release Asset, Current-Release Pointer,
  Publication Record, Version Identity; validation rules and the publication state transitions.
- [../contracts/release-publication.md](../contracts/release-publication.md) — published-release
  layout, `release.json` schema and semantics, immutability and compatibility rules, example.
- [quickstart.md](quickstart.md) — runnable validation: unit/contract tests, local dry-run,
  workflow rehearsal, post-publication clean-project check, pointer check, idempotent re-run.

### Realization delta against the accepted design

The child `design.md` records no hardened realization, so the whole realization is new. Against the
**parent** design (read-only context): its "Durable Implementation Decisions" and "Traceability"
sections remain unchanged; the only parent statement this attempt supersedes in practice is the
Known Limitation "publication transport is a separate release operation" — which now becomes this
child's realization. Nothing in the parent design is edited; a later hardening of this child records
the publication realization here, and the parent limitation can be revised by its own lifecycle.

### Post-design Constitution re-check

Unchanged from the table above. Principle VI is satisfied by the Phase 1 decision to read the
version from `bundle.yml` and check the other manifests and the tag against it (research R2).
